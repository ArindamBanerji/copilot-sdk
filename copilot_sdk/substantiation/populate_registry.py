"""Populate ClaimRegistry with entries for shipped features."""

from .registry import ClaimRegistry
from .tiers import ClaimProvenance, Tier


def populate_default_registry() -> ClaimRegistry:
    registry = ClaimRegistry()

    registry.register(
        ClaimProvenance(
            claim_id="P50-market-data",
            text="Market data populated from real sources (yfinance/Alpaca)",
            tier=Tier.SCRAPED,
            evidence_ref="MarketDataProvider P50",
            is_magnitude_claim=False,
            copilot="trading",
            feature="P50-TRD-YFINANCE",
        )
    )
    registry.register(
        ClaimProvenance(
            claim_id="P53-trust-radar",
            text="DK trust radar shows factor reliability",
            tier=Tier.SCRAPED,
            evidence_ref="DK weights from scorer",
            is_magnitude_claim=False,
            copilot="trading",
            feature="P53-TRD-TRUST-RADAR",
        )
    )
    registry.register(
        ClaimProvenance(
            claim_id="P49-regime",
            text="Regime recommendation derived from market data",
            tier=Tier.SCRAPED,
            evidence_ref="K4 market data via P50",
            is_magnitude_claim=False,
            copilot="trading",
            feature="P49-TRD-REGIME-RECOMMENDER",
        )
    )
    registry.register(
        ClaimProvenance(
            claim_id="P54-factor-computers",
            text="Trading factor computers provide deterministic factor scores",
            tier=Tier.SCRAPED,
            evidence_ref="Trading factor registry over tier-tagged market/journal context",
            is_magnitude_claim=False,
            copilot="trading",
            feature="P54-TRD-FACTOR-COMPUTERS",
        )
    )
    registry.register(
        ClaimProvenance(
            claim_id="P55-patterns",
            text="Statistical pattern detection",
            tier=Tier.SCRAPED,
            evidence_ref="computed from K4 trade data",
            is_magnitude_claim=False,
            copilot="trading",
            feature="P55-TRD-PATTERN-DETECTOR",
        )
    )
    registry.register(
        ClaimProvenance(
            claim_id="P57-trade-journal",
            text="Trade journal records and reflections",
            tier=Tier.REAL,
            evidence_ref="manual journal entries and imported trade records",
            is_magnitude_claim=False,
            copilot="trading",
            feature="P57-TRD-TRADE-JOURNAL",
        )
    )
    registry.register(
        ClaimProvenance(
            claim_id="P59-ibkr-connector",
            text="IBKR connector imports broker fills and market bars",
            tier=Tier.SCRAPED,
            evidence_ref="IBKRConnector broker API import path",
            is_magnitude_claim=False,
            copilot="trading",
            feature="P59-TRD-IBKR-CONNECTOR",
        )
    )
    registry.register(
        ClaimProvenance(
            claim_id="P60-csv-import",
            text="CSV import normalizes broker trade exports",
            tier=Tier.SCRAPED,
            evidence_ref="CSVConnector imported external trade files",
            is_magnitude_claim=False,
            copilot="trading",
            feature="P60-TRD-CSV-IMPORT",
        )
    )
    registry.register(
        ClaimProvenance(
            claim_id="P63-evidence-nl",
            text="NL evidence with polarity + DK trust labels",
            tier=Tier.SCRAPED,
            evidence_ref="polarity from preset, DK from scorer",
            is_magnitude_claim=False,
            copilot="trading",
            feature="P63-TRD-EVIDENCE-NL",
        )
    )

    registry.register(
        ClaimProvenance(
            claim_id="P66-qbo",
            text="QBO vendor/invoice data for supplier intelligence",
            tier=Tier.SCRAPED,
            evidence_ref="QuickBooks Online API (MockQBO)",
            is_magnitude_claim=False,
            copilot="purchasing",
            feature="P66-PUR-QBO-CONNECTOR",
        )
    )
    registry.register(
        ClaimProvenance(
            claim_id="P68-spend",
            text="Food cost dashboard metrics",
            tier=Tier.SCRAPED,
            evidence_ref="QBO fetch_bills() K4 (P68-FIX)",
            is_magnitude_claim=False,
            copilot="purchasing",
            feature="P68-PUR-SPEND-DASH",
        )
    )
    registry.register(
        ClaimProvenance(
            claim_id="P69-match",
            text="Three-way match results + confidence",
            tier=Tier.SCRAPED,
            evidence_ref="QBO order data K4",
            is_magnitude_claim=False,
            copilot="purchasing",
            feature="P69-PUR-MATCH-ENGINE",
        )
    )
    registry.register(
        ClaimProvenance(
            claim_id="P70-queue",
            text="Smart order queue with priority scores",
            tier=Tier.SCRAPED,
            evidence_ref="QBO order data K4 + scorer",
            is_magnitude_claim=False,
            copilot="purchasing",
            feature="P70-PUR-ORDER-QUEUE",
        )
    )
    registry.register(
        ClaimProvenance(
            claim_id="P71-verify",
            text="Confirm/override with conservation status",
            tier=Tier.REAL,
            evidence_ref="verified decisions from scorer.learn()",
            is_magnitude_claim=False,
            copilot="purchasing",
            feature="P71-PUR-VERIFY",
        )
    )
    registry.register(
        ClaimProvenance(
            claim_id="P72-auto-order",
            text="Auto-order gate with conservation gating",
            tier=Tier.REAL,
            evidence_ref="conservation from verified decisions",
            is_magnitude_claim=False,
            copilot="purchasing",
            feature="P72-PUR-CONSERVATION-FULL",
        )
    )
    registry.register(
        ClaimProvenance(
            claim_id="P-PUR-COMMODITY-K4",
            text="Commodity price indices for purchasing categories",
            tier=Tier.SCRAPED,
            evidence_ref="FRED commodity source with K4 provenance cascade",
            is_magnitude_claim=False,
            copilot="purchasing",
            feature="P-PUR-COMMODITY-K4",
        )
    )

    registry.register(
        ClaimProvenance(
            claim_id="P36-lead-time",
            text="Supplier lead time from invoice context",
            tier=Tier.SCRAPED,
            evidence_ref="invoice context \u2591\u2591 (F-17)",
            is_magnitude_claim=False,
            copilot="s2p",
            feature="P36-S2P-LEAD-TIME",
        )
    )
    registry.register(
        ClaimProvenance(
            claim_id="P37-nl-trust",
            text="Trust-weighted NL evidence",
            tier=Tier.SCRAPED,
            evidence_ref="trust source tier-tagged",
            is_magnitude_claim=False,
            copilot="s2p",
            feature="P37-S2P-NL-TRUST",
        )
    )
    registry.register(
        ClaimProvenance(
            claim_id="P38-context-builder",
            text="Source-labeled S2P context builder",
            tier=Tier.SCRAPED,
            evidence_ref="ProvenancedValue source labels",
            is_magnitude_claim=False,
            copilot="s2p",
            feature="P38-S2P-CONTEXT-BUILDER",
        )
    )
    registry.register(
        ClaimProvenance(
            claim_id="P39-graph-enrichment",
            text="Supplier enrichment hooks for S2P graph context",
            tier=Tier.SCRAPED,
            evidence_ref="P39A/P39B shipped, provenance-tagged",
            is_magnitude_claim=False,
            copilot="s2p",
            feature="P39-S2P-GRAPH-ENRICHMENT",
        )
    )
    registry.register(
        ClaimProvenance(
            claim_id="P40-auto-approve",
            text="Auto-approve advisory (shadow)",
            tier=Tier.SCRAPED,
            evidence_ref="advisory = real-pending",
            is_magnitude_claim=False,
            copilot="s2p",
            feature="P40-S2P-AUTO-APPROVE",
        )
    )
    registry.register(
        ClaimProvenance(
            claim_id="P41-centroid-explorer",
            text="Centroid explorer factor values in FactorRadar",
            tier=Tier.SCRAPED,
            evidence_ref="per-factor provenance from preset",
            is_magnitude_claim=False,
            copilot="s2p",
            feature="P41-S2P-CENTROID-EXPLORER",
        )
    )

    registry.register(
        ClaimProvenance(
            claim_id="P42-nl-query",
            text="NL query results (deterministic, no LLM)",
            tier=Tier.SCRAPED,
            evidence_ref="deterministic query engine",
            is_magnitude_claim=False,
            copilot="dataops",
            feature="P42-DI-3-NL-QUERY",
        )
    )
    registry.register(
        ClaimProvenance(
            claim_id="P43-combinations",
            text="Discovered factor combinations (non-causal)",
            tier=Tier.SCRAPED,
            evidence_ref="statistical discovery",
            is_magnitude_claim=False,
            copilot="dataops",
            feature="P43-DI-5-COMBINATION-DISCOVERY",
        )
    )
    registry.register(
        ClaimProvenance(
            claim_id="P30-profiler",
            text="Source profiles",
            tier=Tier.SCRAPED,
            evidence_ref="K3 fixture profiles -> sample",
            is_magnitude_claim=False,
            copilot="dataops",
            feature="P30-DI-1-SOURCE-PROFILER",
        )
    )
    registry.register(
        ClaimProvenance(
            claim_id="P44-graph-enrichment",
            text="DataOps graph enrichment writes idempotent enrichment records",
            tier=Tier.SCRAPED,
            evidence_ref="DataOpsGraphEnricher graph-store write path",
            is_magnitude_claim=False,
            copilot="dataops",
            feature="P44-DI-GRAPH-ENRICHMENT",
        )
    )

    registry.register(
        ClaimProvenance(
            claim_id="SOC-gamma",
            text="Compounding intelligence gamma > 1 (mechanism proven)",
            tier=Tier.ANALYTIC,
            evidence_ref="gamma theorem (epsilon_firm > 0.128)",
            is_magnitude_claim=False,
            copilot="soc",
            feature="CC-21-GAMMA",
        )
    )
    registry.register(
        ClaimProvenance(
            claim_id="SOC-threat-intel",
            text="Threat intelligence enrichment factor",
            tier=Tier.SCRAPED,
            evidence_ref="seeded ThreatIndicator/Campaign (K3->K4 on real alerts)",
            is_magnitude_claim=False,
            copilot="soc",
            feature="SOC-THREAT-INTEL",
        )
    )
    registry.register(
        ClaimProvenance(
            claim_id="SOC-campaign",
            text="Campaign intelligence context",
            tier=Tier.SCRAPED,
            evidence_ref="campaign context from seed (K3->K4 on real campaigns)",
            is_magnitude_claim=False,
            copilot="soc",
            feature="SOC-CAMPAIGN",
        )
    )
    registry.register(
        ClaimProvenance(
            claim_id="SOC-conservation",
            text="SOC conservation state",
            tier=Tier.REAL,
            evidence_ref="from verified decisions via scorer.learn()",
            is_magnitude_claim=False,
            copilot="soc",
            feature="SOC-CONSERVATION",
        )
    )

    return registry
