"""H-TRUST v2.1 factorial instrument.

Only authoritative UCI archives are fetched.  This runner is intentionally
independent of copilot_sdk and product scorers.
"""

from __future__ import annotations

import csv
import hashlib
import json
import zipfile
from pathlib import Path
from urllib.request import urlopen

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit, train_test_split


HERE = Path(__file__).resolve().parent
DATA = HERE / "v2_data"
RAW = HERE / "v2_raw"
DATA.mkdir(parents=True, exist_ok=True)
RAW.mkdir(parents=True, exist_ok=True)
SEEDS = range(20)
SCALES = ("minmax", "robust_quantile", "standardized")
H_LEVELS = (0.0, 0.5, 1.0, 1.5, 2.0)
VAR_FLOOR = 1e-4


def download_origin(name: str, url: str) -> tuple[Path, str, int]:
    path = DATA / name
    if not path.exists():
        with urlopen(url, timeout=120) as response:
            path.write_bytes(response.read())
    payload = path.read_bytes()
    return path, hashlib.sha256(payload).hexdigest(), len(payload)


def read_member(archive: Path, suffix: str) -> bytes:
    with zipfile.ZipFile(archive) as zf:
        name = next(name for name in zf.namelist() if name.lower().endswith(suffix.lower()))
        return zf.read(name)


def load_credit() -> tuple[np.ndarray, np.ndarray, list[str], dict[str, object]]:
    path, digest, size = download_origin(
        "credit_origin.zip",
        "https://archive.ics.uci.edu/static/public/350/default%2Bof%2Bcredit%2Bcard%2Bclients.zip",
    )
    xls = read_member(path, ".xls")
    frame = pd.read_excel(xls, header=1, engine="xlrd")
    target = str(frame.columns[-1])
    frame = frame.drop(columns=[c for c in frame.columns if str(c).upper() == "ID"])
    y = frame.pop(target).to_numpy(dtype=int)
    columns = [str(c) for c in frame.columns]
    meta = {"source": "UCI id 350", "url": "https://archive.ics.uci.edu/dataset/350/default%2Bof%2Bcredit%2Bcard%2Bclients", "archive_sha256": digest, "bytes": size, "parser": "xlrd"}
    return frame.to_numpy(dtype=float), y, columns, meta


def load_coil() -> tuple[np.ndarray, np.ndarray, list[str], dict[str, object]]:
    path, digest, size = download_origin(
        "coil_origin.zip",
        "https://archive.ics.uci.edu/static/public/125/insurance%2Bcompany%2Bbenchmark%2Bcoil%2B2000.zip",
    )
    raw = read_member(path, "ticdata2000.txt")
    frame = pd.read_csv(pd.io.common.BytesIO(raw), sep="\t", header=None)
    y = frame.iloc[:, 85].to_numpy(dtype=int)
    frame = frame.iloc[:, :85]
    columns = [f"coil_f{i}" for i in range(frame.shape[1])]
    meta = {"source": "UCI id 125", "url": "https://archive.ics.uci.edu/dataset/125/insurance%2Bcompany%2Bbenchmark%2Bcoil%2B2000", "archive_sha256": digest, "bytes": size, "training_rows": int(len(frame))}
    return frame.to_numpy(dtype=float), y, columns, meta


def load_adult() -> tuple[np.ndarray, np.ndarray, list[str], dict[str, object]]:
    path, digest, size = download_origin(
        "adult_origin.zip",
        "https://archive.ics.uci.edu/static/public/2/adult.zip",
    )
    raw = read_member(path, "adult.data")
    frame = pd.read_csv(pd.io.common.BytesIO(raw), header=None, skipinitialspace=True)
    # Numeric/ordinal primary factors only; categorical education is excluded.
    indices = [0, 2, 4, 10, 11, 12]
    columns = ["age", "fnlwgt", "education_num", "capital_gain", "capital_loss", "hours_per_week"]
    target = frame.iloc[:, 14].astype(str).str.replace(".", "", regex=False).str.strip()
    y = target.str.startswith(">50K").astype(int).to_numpy()
    meta = {"source": "UCI id 2", "url": "https://archive.ics.uci.edu/dataset/2/adult", "archive_sha256": digest, "bytes": size, "source_file": "adult.data", "numeric_columns": columns}
    return frame.iloc[:, indices].to_numpy(dtype=float), y, columns, meta


def load_all() -> dict[str, tuple[np.ndarray, np.ndarray, list[str], dict[str, object]]]:
    return {"credit": load_credit(), "coil2000": load_coil(), "adult": load_adult()}


def feature_groups(x: np.ndarray) -> tuple[np.ndarray, int, int]:
    # Quantized full-vector hashes are the frozen fallback group key.
    quantized = np.round(np.nan_to_num(x, nan=-999999.0), 6)
    groups = np.array([hashlib.sha256(row.tobytes()).hexdigest() for row in quantized], dtype=object)
    counts = pd.Series(groups).value_counts()
    return groups, int((counts > 1).sum()), int((counts[counts > 1] - 1).sum())


def split_indices(y: np.ndarray, x: np.ndarray, seed: int) -> tuple[np.ndarray, ...]:
    groups, multi_groups, _ = feature_groups(x)
    if multi_groups:
        for attempt in range(100):
            splitter = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=seed + attempt)
            train_val, test = next(splitter.split(x, y, groups))
            splitter2 = GroupShuffleSplit(n_splits=1, test_size=0.125, random_state=seed + 1000 + attempt)
            train_rel, valid_rel = next(splitter2.split(x[train_val], y[train_val], groups[train_val]))
            train, valid = train_val[train_rel], train_val[valid_rel]
            if len(np.unique(y[train])) == 2 and len(np.unique(y[valid])) == 2 and len(np.unique(y[test])) == 2:
                return train, valid, test
        raise RuntimeError("could not construct class-complete group split")
    train_val, test, y_train_val, y_test = train_test_split(np.arange(len(y)), y, test_size=0.2, stratify=y, random_state=seed)
    train, valid = train_test_split(train_val, test_size=0.125, stratify=y_train_val, random_state=seed + 1000)
    return train, valid, test


def scale_fit(train: np.ndarray, valid: np.ndarray, test: np.ndarray, convention: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    med = np.nanmedian(train, axis=0)
    med = np.where(np.isfinite(med), med, 0.0)
    train = np.where(np.isfinite(train), train, med)
    valid = np.where(np.isfinite(valid), valid, med)
    test = np.where(np.isfinite(test), test, med)
    if convention == "minmax":
        low, high = train.min(0), train.max(0)
        denom = np.where(high > low, high - low, 1.0)
        return np.clip((train - low) / denom, 0, 1), np.clip((valid - low) / denom, 0, 1), np.clip((test - low) / denom, 0, 1)
    if convention == "robust_quantile":
        low, high = np.quantile(train, [0.02, 0.98], axis=0)
        denom = np.where(high > low, high - low, 1.0)
        return np.clip((train - low) / denom, 0, 1), np.clip((valid - low) / denom, 0, 1), np.clip((test - low) / denom, 0, 1)
    mean, std = train.mean(0), train.std(0)
    std = np.where(std > 0, std, 1.0)
    return (train - mean) / std, (valid - mean) / std, (test - mean) / std


def prepare(x: np.ndarray, y: np.ndarray, seed: int, convention: str) -> tuple[np.ndarray, ...]:
    train, valid, test = split_indices(y, x, seed)
    xt, xv, xs = scale_fit(x[train], x[valid], x[test], convention)
    return xt, xv, xs, y[train], y[valid], y[test]


def normalize(x: np.ndarray) -> np.ndarray:
    return x / np.maximum(np.linalg.norm(x, axis=1, keepdims=True), 1e-12)


def centers(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    return np.vstack([x[y == c].mean(0) for c in (0, 1)])


def weights(x: np.ndarray, y: np.ndarray, c: np.ndarray) -> np.ndarray:
    variances = []
    for cls in (0, 1):
        variances.append(np.var(x[y == cls] - c[cls], axis=0, ddof=1))
    v = np.maximum(np.nan_to_num(np.mean(variances, 0), nan=VAR_FLOOR), VAR_FLOOR)
    return 1.0 / v


def pred_distance(x: np.ndarray, c: np.ndarray, w: np.ndarray) -> np.ndarray:
    return np.argmin((((x[:, None, :] - c[None, :, :]) ** 2) * w).sum(2), 1)


def pred_dot(x: np.ndarray, c: np.ndarray) -> np.ndarray:
    return np.argmax(x @ c.T, 1)


def ba(y: np.ndarray, p: np.ndarray) -> float:
    return float(np.mean([(p[y == c] == c).mean() for c in (0, 1)]))


def cell_scores(xt: np.ndarray, xs: np.ndarray, yt: np.ndarray, ys: np.ndarray) -> dict[str, object]:
    cu = centers(xt, yt)
    cw = weights(xt, yt, cu)
    xn, cn = normalize(xt), normalize(cu)
    sn = normalize(xs)
    predictions = {
        "raw_uniform_distance": pred_distance(xs, cu, np.ones(xs.shape[1])),
        "normalized_uniform_distance": pred_distance(sn, cn, np.ones(xs.shape[1])),
        "raw_weighted_distance": pred_distance(xs, cu, cw),
        "raw_uniform_dot": pred_dot(xs, cu),
        "normalized_uniform_dot": pred_dot(sn, cn),
    }
    scores = {name: ba(ys, prediction) for name, prediction in predictions.items()}
    scores["qa_normalized_distance_dot_mismatch"] = int(np.sum(predictions["normalized_uniform_distance"] != predictions["normalized_uniform_dot"]))
    scores["h_base"] = float(np.log(np.max(1.0 / cw) / np.min(1.0 / cw)))
    return scores


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def ci(values: np.ndarray, seed: int) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    sample = rng.choice(values, (4000, len(values)), replace=True).mean(1)
    return float(np.quantile(sample, .025)), float(np.quantile(sample, .975))


def summarize(rows: list[dict[str, object]], field: str, keys: list[str]) -> list[dict[str, object]]:
    groups: dict[tuple[object, ...], list[float]] = {}
    for row in rows:
        groups.setdefault(tuple(row[k] for k in keys), []).append(float(row[field]))
    out = []
    for key, values in groups.items():
        arr = np.array(values); lo, hi = ci(arr, abs(hash(key)) % (2**32))
        item = dict(zip(keys, key)); item.update(mean=float(arr.mean()), ci_low=lo, ci_high=hi, ci_width=hi-lo, n=len(arr)); out.append(item)
    return out


def run_f2(data: dict[str, tuple[np.ndarray, np.ndarray, list[str], dict[str, object]]]) -> list[dict[str, object]]:
    rows = []
    for name, (x, y, _columns, _meta) in data.items():
        for scale in SCALES:
            for seed in SEEDS:
                xt, _xv, xs, yt, _yv, yy = prepare(x, y, seed, scale)
                result = cell_scores(xt, xs, yt, yy)
                rows.append({"dataset": name, "scale": scale, "seed": seed, "contrast": "magnitude", "raw_uniform_distance": result["raw_uniform_distance"], "normalized_uniform_distance": result["normalized_uniform_distance"], "difference": result["raw_uniform_distance"] - result["normalized_uniform_distance"], "qa_mismatch": result["qa_normalized_distance_dot_mismatch"]})
    write_csv(RAW / "f2_prime_cells.csv", rows); return rows


def run_c1(data: dict[str, tuple[np.ndarray, np.ndarray, list[str], dict[str, object]]]) -> list[dict[str, object]]:
    rows = []
    for name, (x, y, _columns, _meta) in data.items():
        for scale in SCALES:
            for seed in SEEDS:
                xt, _xv, xs, yt, _yv, yy = prepare(x, y, seed, scale)
                result = cell_scores(xt, xs, yt, yy)
                rows.append({"dataset": name, "scale": scale, "seed": seed, **result,
                             "magnitude": result["raw_uniform_distance"] - result["normalized_uniform_distance"],
                             "reliability": result["raw_weighted_distance"] - result["raw_uniform_distance"],
                             "primitive": result["raw_uniform_distance"] - result["raw_uniform_dot"]})
    write_csv(RAW / "c1_factorial_cells.csv", rows); return rows


def homogenize(xt: np.ndarray, xv: np.ndarray, xs: np.ndarray, yt: np.ndarray, seed: int) -> tuple[np.ndarray, np.ndarray, np.ndarray, float, float, float]:
    c = centers(xt, yt); w = weights(xt, yt, c); variance = 1.0 / w; target = float(np.max(variance))
    rng = np.random.default_rng(seed + 900000)
    scales = np.sqrt(np.maximum(target - variance, 0.0))
    def add(values: np.ndarray) -> np.ndarray:
        return values + rng.normal(0.0, scales, values.shape)
    ht, hv, hs = add(xt), add(xv), add(xs)
    post = weights(ht, yt, centers(ht, yt)); h_post = float(np.log(np.max(1.0/post) / np.min(1.0/post)))
    return ht, hv, hs, h_post, target, float(np.log(np.max(variance) / np.min(variance)))


def run_c2(data: dict[str, tuple[np.ndarray, np.ndarray, list[str], dict[str, object]]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    base_rows, curve_rows = [], []
    for name, (x, y, _columns, _meta) in data.items():
        splits = {seed: prepare(x, y, seed, "minmax") for seed in SEEDS}
        for seed, (xt, xv, xs, yt, _yv, yy) in splits.items():
            c = centers(xt, yt); w = weights(xt, yt, c); h_base = float(np.log(np.max(1.0/w) / np.min(1.0/w)))
            ht, hv, hs, h_post, target, _ = homogenize(xt, xv, xs, yt, seed)
            base_rows.append({"dataset": name, "seed": seed, "h_base_native": h_base, "h_base_post": h_post, "target_variance": target, "admissible": int(h_post <= .10)})
            if h_post > .10:
                continue
            for level in H_LEVELS:
                for draw in range(20):
                    rng = np.random.default_rng(seed * 10000 + draw)
                    d = ht.shape[1]; z = np.linspace(-level / 4, level / 4, d); rng.shuffle(z); scales = .03 * np.exp(z)
                    noisy = lambda v: v + rng.normal(0.0, scales, v.shape)
                    nt, ns = noisy(ht), noisy(hs)
                    c2 = centers(nt, yt); ww = weights(nt, yt, c2)
                    curve_rows.append({"dataset": name, "seed": seed, "draw": draw, "target_h": level, "measured_h": float(np.log(np.max(1.0/ww) / np.min(1.0/ww))), "reliability_gain": ba(yy, pred_distance(ns, c2, ww)) - ba(yy, pred_distance(ns, c2, np.ones(d)))})
    write_csv(RAW / "c2_h_base.csv", base_rows); write_csv(RAW / "c2_curve_cells.csv", curve_rows); return base_rows, curve_rows


def main() -> None:
    data = load_all()
    manifest = []
    for name, (x, y, columns, meta) in data.items():
        groups, multi, duplicate_rows = feature_groups(x)
        manifest.append({"dataset": name, "rows": len(y), "features": x.shape[1], "positive_rate": float(y.mean()), "columns": columns, "multi_record_groups": multi, "duplicate_rows": duplicate_rows, "feature_sha256": hashlib.sha256(np.nan_to_num(x, nan=-999999).tobytes()).hexdigest(), **meta})
    (RAW / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    f2 = run_f2(data)
    (RAW / "f2_prime_summary.json").write_text(json.dumps(summarize(f2, "difference", ["dataset", "scale"]), indent=2), encoding="utf-8")
    c1 = run_c1(data)
    c1s = []
    for contrast in ("magnitude", "reliability", "primitive"):
        c1s += [{**r, "contrast": contrast} for r in summarize(c1, contrast, ["dataset", "scale"])]
    (RAW / "c1_summary.json").write_text(json.dumps(c1s, indent=2), encoding="utf-8")
    base, curve = run_c2(data)
    (RAW / "c2_summary.json").write_text(json.dumps(summarize(curve, "reliability_gain", ["dataset", "target_h"]), indent=2), encoding="utf-8")
    print(json.dumps({"manifest": manifest, "f2": summarize(f2, "difference", ["dataset", "scale"]), "c1": c1s, "c2_base": summarize(base, "h_base_post", ["dataset"]), "c2": summarize(curve, "reliability_gain", ["dataset", "target_h"])}, indent=2))


if __name__ == "__main__":
    main()
