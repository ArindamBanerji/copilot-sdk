"""Phase 3 Step 6 — dual-write factory smoke test."""
from copilot_sdk.graph.factory import create_graph_store

store = create_graph_store(domain="trading", decision_id_prefix="TRD-")
print(f"Store type: {type(store).__name__}")
print(f"Primary: {type(store.primary).__name__}")
print(f"Secondary: {type(store.secondary).__name__}")

did = store.generate_decision_id("trading")
print(f"Generated ID: {did}")
print(f"Starts with TRD-: {did.startswith('TRD-')}")

has_outbox = hasattr(store, "_outbox") and store._outbox is not None
print(f"Durable outbox: {has_outbox}")

print(f"Outbox empty: {store.outbox_empty()}")

store.close()
print("OK")
