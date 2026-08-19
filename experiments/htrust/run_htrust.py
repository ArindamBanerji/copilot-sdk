"""Falsification-first H-TRUST experiment runner.

This runner intentionally does not import copilot_sdk or any product scorer.
It uses public tabular data, train-only prototypes/variance estimates, and
writes raw outputs beside this file.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import tarfile
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
RAW = ROOT / "raw"
DATA.mkdir(parents=True, exist_ok=True)
RAW.mkdir(parents=True, exist_ok=True)
SEEDS = list(range(20))
H_LEVELS = [0.0, 0.25, 0.50, 1.0, 1.5, 2.0]
DRAW_COUNT = 20
VAR_FLOOR = 1e-4


def fetch(url: str, path: Path) -> Path:
    if not path.exists():
        with urllib.request.urlopen(url, timeout=60) as response:
            path.write_bytes(response.read())
    return path


def load_credit() -> tuple[str, np.ndarray, np.ndarray, list[str]]:
    path = fetch(
        "https://raw.githubusercontent.com/rlancaster243/UCI-Credit-Card-Analysis/master/UCI_Credit_Card.csv",
        DATA / "default_credit.csv",
    )
    frame = pd.read_csv(path)
    target = "default.payment.next.month"
    frame = frame.rename(columns={frame.columns[-1]: target})
    frame = frame.drop(columns=[c for c in frame.columns if str(c).upper() == "ID"], errors="ignore")
    y = frame.pop(target).to_numpy(dtype=int)
    return "credit", frame.to_numpy(dtype=float), y, [str(c) for c in frame.columns]


def load_coil() -> tuple[str, np.ndarray, np.ndarray, list[str]]:
    path = fetch(
        "https://archive.ics.uci.edu/static/public/125/insurance%2Bcompany%2Bbenchmark%2Bcoil%2B2000.zip",
        DATA / "coil.zip",
    )
    import zipfile

    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        train_name = next(n for n in names if n.lower().endswith("ticdata2000.txt"))
        train = pd.read_csv(archive.open(train_name), sep="\t", header=None)
    y = train.iloc[:, 85].to_numpy(dtype=int)
    frame = train.iloc[:, :85]
    return "coil2000", frame.to_numpy(dtype=float), y, [f"f{i}" for i in range(frame.shape[1])]


def load_heloc() -> tuple[str, np.ndarray, np.ndarray, list[str]]:
    path = fetch(
        "https://huggingface.co/datasets/vitaliykinakh/heloc/resolve/main/heloc.csv?download=true",
        DATA / "heloc.csv",
    )
    frame = pd.read_csv(path)
    target = "RiskPerformance"
    y = (frame.pop(target).astype(str).str.lower() == "bad").to_numpy(dtype=int)
    # FICO special codes are missingness-like values, not measurements.
    frame = frame.replace({-9: np.nan, -8: np.nan, -7: np.nan})
    return "heloc", frame.to_numpy(dtype=float), y, [str(c) for c in frame.columns]


def load_all() -> dict[str, tuple[np.ndarray, np.ndarray, list[str]]]:
    loaders = [load_credit, load_coil, load_heloc]
    result = {}
    for loader in loaders:
        name, x, y, columns = loader()
        result[name] = (x, y, columns)
    return result


def preprocess(x_train: np.ndarray, x_other: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    med = np.nanmedian(x_train, axis=0)
    med = np.where(np.isfinite(med), med, 0.0)
    train = np.where(np.isfinite(x_train), x_train, med)
    other = np.where(np.isfinite(x_other), x_other, med)
    scaler = MinMaxScaler()
    train = scaler.fit_transform(train)
    other = np.clip(scaler.transform(other), 0.0, 1.0)
    return train, other


def preprocess_split(x_train: np.ndarray, x_valid: np.ndarray, x_test: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    med = np.nanmedian(x_train, axis=0)
    med = np.where(np.isfinite(med), med, 0.0)
    train = np.where(np.isfinite(x_train), x_train, med)
    valid = np.where(np.isfinite(x_valid), x_valid, med)
    test = np.where(np.isfinite(x_test), x_test, med)
    scaler = MinMaxScaler()
    train = scaler.fit_transform(train)
    valid = np.clip(scaler.transform(valid), 0.0, 1.0)
    test = np.clip(scaler.transform(test), 0.0, 1.0)
    return train, valid, test


def prototypes(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    classes = np.array([0, 1])
    return np.vstack([x[y == cls].mean(axis=0) for cls in classes])


def variance_weights(x: np.ndarray, y: np.ndarray, centers: np.ndarray) -> np.ndarray:
    values = []
    for cls in (0, 1):
        residual = x[y == cls] - centers[cls]
        values.append(np.var(residual, axis=0, ddof=1))
    variance = np.mean(np.vstack(values), axis=0)
    variance = np.nan_to_num(variance, nan=VAR_FLOOR, posinf=VAR_FLOOR, neginf=VAR_FLOOR)
    variance = np.maximum(variance, VAR_FLOOR)
    return 1.0 / variance


def predict_metric(x: np.ndarray, centers: np.ndarray, weights: np.ndarray) -> np.ndarray:
    distance = ((x[:, None, :] - centers[None, :, :]) ** 2 * weights[None, None, :]).sum(axis=2)
    return np.argmin(distance, axis=1).astype(int)


def predict_cosine(x: np.ndarray, centers: np.ndarray) -> np.ndarray:
    x_norm = np.linalg.norm(x, axis=1, keepdims=True)
    c_norm = np.linalg.norm(centers, axis=1, keepdims=True)
    x_unit = x / np.maximum(x_norm, 1e-12)
    c_unit = centers / np.maximum(c_norm, 1e-12)
    return np.argmax(x_unit @ c_unit.T, axis=1).astype(int)


def balanced_accuracy(y: np.ndarray, pred: np.ndarray) -> float:
    recalls = []
    for cls in (0, 1):
        mask = y == cls
        recalls.append(float(np.mean(pred[mask] == cls)) if np.any(mask) else 0.0)
    return float(np.mean(recalls))


def bootstrap_ci(values: np.ndarray, seed: int, draws: int = 1000) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    if len(values) < 2:
        value = float(values[0]) if len(values) else float("nan")
        return value, value
    samples = rng.choice(values, size=(draws, len(values)), replace=True).mean(axis=1)
    return float(np.quantile(samples, 0.025)), float(np.quantile(samples, 0.975))


def fit_logistic(x_train: np.ndarray, y_train: np.ndarray, x_valid: np.ndarray, y_valid: np.ndarray, x_test: np.ndarray) -> np.ndarray:
    best = None
    for c_value in (0.01, 0.1, 1.0, 10.0):
        model = LogisticRegression(C=c_value, max_iter=1000, class_weight="balanced", random_state=0)
        model.fit(x_train, y_train)
        score = balanced_accuracy(y_valid, model.predict(x_valid))
        if best is None or score > best[0]:
            best = (score, c_value)
    model = LogisticRegression(C=best[1], max_iter=1000, class_weight="balanced", random_state=0)
    model.fit(np.vstack([x_train, x_valid]), np.concatenate([y_train, y_valid]))
    return model.predict(x_test).astype(int)


def split_data(x: np.ndarray, y: np.ndarray, seed: int) -> tuple[np.ndarray, ...]:
    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.2, stratify=y, random_state=seed
    )
    x_train, x_valid, y_train, y_valid = train_test_split(
        x_train, y_train, test_size=0.125, stratify=y_train, random_state=seed + 1000
    )
    x_train, x_valid, x_test = preprocess_split(x_train, x_valid, x_test)
    return x_train, x_valid, x_test, y_train, y_valid, y_test


def evaluate_split(x: np.ndarray, y: np.ndarray, seed: int, normalized: bool = False) -> dict[str, float]:
    x_train, x_valid, x_test, y_train, y_valid, y_test = split_data(x, y, seed)
    if normalized:
        x_train = x_train / np.maximum(np.linalg.norm(x_train, axis=1, keepdims=True), 1e-12)
        x_valid = x_valid / np.maximum(np.linalg.norm(x_valid, axis=1, keepdims=True), 1e-12)
        x_test = x_test / np.maximum(np.linalg.norm(x_test, axis=1, keepdims=True), 1e-12)
    centers = prototypes(x_train, y_train)
    weights = variance_weights(x_train, y_train, centers)
    pred_weighted = predict_metric(x_test, centers, weights)
    pred_uniform = predict_metric(x_test, centers, np.ones(x_train.shape[1]))
    pred_cosine = predict_cosine(x_test, centers)
    pred_logistic = fit_logistic(x_train, y_train, x_valid, y_valid, x_test)
    return {
        "weighted": balanced_accuracy(y_test, pred_weighted),
        "uniform_l2": balanced_accuracy(y_test, pred_uniform),
        "cosine": balanced_accuracy(y_test, pred_cosine),
        "logistic": balanced_accuracy(y_test, pred_logistic),
        "n_test": float(len(y_test)),
        "heterogeneity": float(np.log(np.max(1.0 / weights) / np.min(1.0 / weights))),
    }


def write_rows(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def run_f2(data: dict[str, tuple[np.ndarray, np.ndarray, list[str]]]) -> list[dict[str, object]]:
    rows = []
    for name, (x, y, columns) in data.items():
        for seed in SEEDS:
            result = evaluate_split(x, y, seed, normalized=True)
            rows.append({"dataset": name, "seed": seed, "features": len(columns), **result,
                         "weighted_minus_cosine": result["weighted"] - result["cosine"]})
    write_rows(RAW / "f2_normalized_cells.csv", rows)
    return rows


def run_c1(data: dict[str, tuple[np.ndarray, np.ndarray, list[str]]]) -> list[dict[str, object]]:
    rows = []
    for name, (x, y, columns) in data.items():
        for seed in SEEDS:
            result = evaluate_split(x, y, seed, normalized=False)
            rows.append({"dataset": name, "seed": seed, "features": len(columns), **result,
                         "weighted_minus_cosine": result["weighted"] - result["cosine"],
                         "weighted_minus_uniform": result["weighted"] - result["uniform_l2"],
                         "weighted_minus_logistic": result["weighted"] - result["logistic"]})
    write_rows(RAW / "c1_cells.csv", rows)
    return rows


def noisy_split(x: np.ndarray, y: np.ndarray, seed: int, heterogeneity: float, draw: int) -> tuple[np.ndarray, ...]:
    x_train, x_valid, x_test, y_train, y_valid, y_test = split_data(x, y, seed)
    rng = np.random.default_rng(seed * 10000 + draw)
    d = x_train.shape[1]
    z = np.linspace(-heterogeneity / 4.0, heterogeneity / 4.0, d)
    rng.shuffle(z)
    scales = 0.03 * np.exp(z)
    def perturb(values: np.ndarray) -> np.ndarray:
        return np.clip(values + rng.normal(0.0, scales, size=values.shape), 0.0, 1.0)
    return perturb(x_train), perturb(x_valid), perturb(x_test), y_train, y_valid, y_test


def run_c2(data: dict[str, tuple[np.ndarray, np.ndarray, list[str]]]) -> list[dict[str, object]]:
    rows = []
    for name, (x, y, _columns) in data.items():
        splits = {seed: split_data(x, y, seed) for seed in SEEDS}
        for heterogeneity in H_LEVELS:
            for seed in SEEDS:
                for draw in range(DRAW_COUNT):
                    base_train, base_valid, base_test, y_train, y_valid, y_test = splits[seed]
                    rng = np.random.default_rng(seed * 10000 + draw)
                    d = base_train.shape[1]
                    z = np.linspace(-heterogeneity / 4.0, heterogeneity / 4.0, d)
                    rng.shuffle(z)
                    scales = 0.03 * np.exp(z)
                    perturb = lambda values: np.clip(
                        values + rng.normal(0.0, scales, size=values.shape), 0.0, 1.0
                    )
                    x_train, _x_valid, x_test = perturb(base_train), perturb(base_valid), perturb(base_test)
                    centers = prototypes(x_train, y_train)
                    weights = variance_weights(x_train, y_train, centers)
                    weighted = balanced_accuracy(y_test, predict_metric(x_test, centers, weights))
                    uniform = balanced_accuracy(y_test, predict_metric(x_test, centers, np.ones(x.shape[1])))
                    measured_h = float(np.log(np.max(1.0 / weights) / np.min(1.0 / weights)))
                    rows.append({
                        "dataset": name, "target_heterogeneity": heterogeneity,
                        "measured_heterogeneity": measured_h, "seed": seed, "draw": draw,
                        "weighted": weighted, "uniform_l2": uniform,
                        "gain": weighted - uniform,
                    })
    write_rows(RAW / "c2_cells.csv", rows)
    return rows


def summarize(rows: list[dict[str, object]], key: str, group_keys: list[str]) -> list[dict[str, object]]:
    groups: dict[tuple[object, ...], list[float]] = {}
    for row in rows:
        group = tuple(row[k] for k in group_keys)
        groups.setdefault(group, []).append(float(row[key]))
    output = []
    for group, values in groups.items():
        arr = np.array(values, dtype=float)
        lo, hi = bootstrap_ci(arr, abs(hash(group)) % (2**32))
        item = dict(zip(group_keys, group))
        item.update({"n": len(arr), "mean": float(arr.mean()), "ci_low": lo, "ci_high": hi,
                     "ci_width": hi - lo})
        output.append(item)
    return output


def main() -> None:
    data = load_all()
    manifest = []
    for name, (x, y, columns) in data.items():
        manifest.append({"dataset": name, "rows": int(len(y)), "features": int(x.shape[1]),
                         "positive_rate": float(np.mean(y)), "columns_sha256": hashlib.sha256(
                             "\n".join(columns).encode()).hexdigest()})
    (RAW / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    # F2 is intentionally completed and persisted before C1/C2 begin.
    f2 = run_f2(data)
    f2_summary = summarize(
        [{**r, "gain": r["weighted_minus_cosine"]} for r in f2], "gain", ["dataset"]
    )
    (RAW / "f2_summary.json").write_text(json.dumps(f2_summary, indent=2), encoding="utf-8")

    c1 = run_c1(data)
    c1_summary = []
    for metric in ("weighted_minus_cosine", "weighted_minus_uniform", "weighted_minus_logistic"):
        c1_summary.extend([{**r, "contrast": metric} for r in summarize(c1, metric, ["dataset"])])
    (RAW / "c1_summary.json").write_text(json.dumps(c1_summary, indent=2), encoding="utf-8")

    c2 = run_c2(data)
    c2_summary = summarize(c2, "gain", ["dataset", "target_heterogeneity"])
    (RAW / "c2_summary.json").write_text(json.dumps(c2_summary, indent=2), encoding="utf-8")

    print(json.dumps({"datasets": manifest, "f2": f2_summary, "c1": c1_summary, "c2": c2_summary}, indent=2))


if __name__ == "__main__":
    main()
