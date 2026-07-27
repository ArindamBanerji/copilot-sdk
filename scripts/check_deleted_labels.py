"""Check counts for all labels deleted in §5.2/§5.3 — did pre-seed recreate any?"""
import psycopg2

conn = psycopg2.connect("host=localhost port=5433 dbname=soc_copilot user=postgres password=postgres")
conn.autocommit = True
cur = conn.cursor()
cur.execute("LOAD 'age'")
cur.execute('SET search_path = ag_catalog, "$user", public')

# Labels deleted in §5.2
deleted_52 = [
    "Outcome", "EvidenceReceipt", "CentroidCheckpoint",
    "DecisionDistanceLog", "DecisionEntityLink", "EvolutionEvent",
]

# Labels deleted in §5.3
deleted_53 = [
    "L5Centroid", "L5DKWeight", "L5ConservationState", "L5DKWeightArchive",
]

# Reference labels (should exist)
reference = ["Decision", "DataQualityAlert", "PipelineSystem"]

print("=" * 60)
print("POST PRE-SEED LABEL COUNTS")
print("=" * 60)

print("\n§5.2 deleted labels (should be 0 unless pre-seed recreated):")
for label in deleted_52:
    cur.execute(
        f"SELECT * FROM cypher('soc_graph', $$ MATCH (n:{label}) RETURN count(n) $$) as (c agtype)"
    )
    count = cur.fetchone()[0]
    tag = " ← PRE-SEED RECREATED" if str(count) != "0" else ""
    print(f"  {label}: {count}{tag}")

print("\n§5.3 deleted labels (should be 0 unless pre-seed recreated):")
for label in deleted_53:
    cur.execute(
        f"SELECT * FROM cypher('soc_graph', $$ MATCH (n:{label}) RETURN count(n) $$) as (c agtype)"
    )
    count = cur.fetchone()[0]
    tag = " ← PRE-SEED RECREATED" if str(count) != "0" else ""
    print(f"  {label}: {count}{tag}")

print("\nReference labels:")
for label in reference:
    cur.execute(
        f"SELECT * FROM cypher('soc_graph', $$ MATCH (n:{label}) RETURN count(n) $$) as (c agtype)"
    )
    print(f"  {label}: {cur.fetchone()[0]}")

# Edge counts for key relationships
print("\nEdge counts:")
edges = [
    ("HAS_OUTCOME", "MATCH ()-[r:HAS_OUTCOME]->() RETURN count(r)"),
    ("EMITTED_RECEIPT", "MATCH ()-[r:EMITTED_RECEIPT]->() RETURN count(r)"),
    ("DECIDED_ON", "MATCH ()-[r:DECIDED_ON]->() RETURN count(r)"),
]
for name, query in edges:
    try:
        cur.execute(
            f"SELECT * FROM cypher('soc_graph', $$ {query} $$) as (c agtype)"
        )
        print(f"  {name}: {cur.fetchone()[0]}")
    except Exception as e:
        print(f"  {name}: ERROR — {e}")
        conn.rollback()
        cur.execute("LOAD 'age'")
        cur.execute('SET search_path = ag_catalog, "$user", public')

conn.close()
print("\n" + "=" * 60)
