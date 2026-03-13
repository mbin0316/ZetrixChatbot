import json, time, requests

URL = "http://localhost:5678/webhook/chat"

queries = [q for q in map(json.loads, open("queries.jsonl"))]
results = []

for q in queries:
    print(f"[{q['id']}/15] {q['query']}")
    t0 = time.time()
    try:
        r = requests.post(URL, json={"chatInput": q["query"]}, timeout=30)
        actual = r.text.strip()
        latency = int((time.time() - t0) * 1000)
        print(f"  → {actual[:120]}")
        print(f"  latency: {latency}ms\n")
        results.append({**q, "actual": actual, "latency_ms": latency,
                        "hit": "", "hallucinated": "", "correct": ""})
    except Exception as e:
        print(f"  ERROR: {e}\n")
        results.append({**q, "actual": f"ERROR: {e}", "latency_ms": 0,
                        "hit": "false", "hallucinated": "false", "correct": "false"})
    time.sleep(5)

with open("results.jsonl", "w") as f:
    for r in results:
        f.write(json.dumps(r) + "\n")

print(f"Done. results.jsonl saved. Fill in hit/hallucinated/correct then run calc_metrics.py")