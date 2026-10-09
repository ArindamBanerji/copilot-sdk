"""AGE-free application harnesses for evolution contract tests."""

from fastapi import FastAPI

from copilot_sdk.backend.evolution_router import create_evolution_router
from copilot_sdk.backend.self_computation_router import create_self_computation_router
from copilot_sdk.evolution import PromptEvolverConfig, PromptVariantEvolver, VariantSpec
from copilot_sdk.graph.memory_store import InMemoryGraphStore


def make_contract_app(domain: str) -> FastAPI:
    """Build the real evolution routes over isolated in-memory contract state."""
    evolver = PromptVariantEvolver(
        config=PromptEvolverConfig(
            conservation_state_provider=lambda: {
                "domain": domain,
                "status": "COLD_START",
            }
        )
    )
    evolver.register_variants(
        [
            VariantSpec(
                id=f"{domain}-baseline-v1",
                family="baseline",
                version=1,
                template="baseline",
                status="active",
            ),
            VariantSpec(
                id=f"{domain}-candidate-v2",
                family="baseline",
                version=2,
                template="candidate",
                status="shadow",
            ),
        ]
    )
    store = InMemoryGraphStore(domain=domain)
    app = FastAPI()
    app.state.evolver = evolver
    app.state.graph_store = store
    app.include_router(
        create_self_computation_router(
            store,
            domain=domain,
            evolver_provider=lambda: evolver,
        )
    )
    app.include_router(
        create_evolution_router(
            graph_store_factory=lambda: store,
            domain=domain,
            evolver_factory=lambda: evolver,
        )
    )
    return app
