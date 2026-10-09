"""Reset clears graph authorities without leaking across domains."""
from copilot_sdk.graph import InMemoryGraphStore


def _seed_authorities(graph: InMemoryGraphStore, domain: str) -> None:
    for save in (
        graph.save_evolution, graph.save_posterior, graph.save_promotion,
        graph.save_ledger, graph.save_governance,
    ):
        save(domain, "state", {"owner": domain, "revision": 7})


def test_domain_reset_clears_platform_state_and_preserves_other_domains() -> None:
    graph = InMemoryGraphStore()
    for domain in ("trading", "purchasing"):
        _seed_authorities(graph, domain)
    graph.domain_scoped_reset("trading")
    for read in (
        graph.get_evolution, graph.get_posterior, graph.get_promotion,
        graph.get_ledger, graph.get_governance,
    ):
        assert read("trading", "state") is None
        assert read("purchasing", "state") == {"owner": "purchasing", "revision": 7}


def test_full_reset_clears_platform_state_in_every_domain() -> None:
    graph = InMemoryGraphStore()
    for domain in ("trading", "purchasing"):
        _seed_authorities(graph, domain)
    graph.reset()
    for domain in ("trading", "purchasing"):
        for read in (
            graph.get_evolution, graph.get_posterior, graph.get_promotion,
            graph.get_ledger, graph.get_governance,
        ):
            assert read(domain, "state") is None

