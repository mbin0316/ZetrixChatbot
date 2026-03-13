import json, numpy as np

results = [json.loads(l) for l in open("results.jsonl")]
total = len(results)

hit  = sum(1 for r in results if str(r.get("hit")).lower()  == "true")
hall = sum(1 for r in results if str(r.get("hallucinated")).lower() == "true")
corr = sum(1 for r in results if str(r.get("correct")).lower() == "true")
lats = [r["latency_ms"] for r in results if r["latency_ms"] > 0]

p50 = int(np.percentile(lats, 50))
p95 = int(np.percentile(lats, 95))

print(f"\n{'='*44}")
print(f"  Retrieval Hit Rate : {hit}/{total} = {hit/total*100:.1f}%  {'✅' if hit/total >= 0.8 else '❌'} (target >80%)")
print(f"  Hallucination Rate : {hall}/{total} = {hall/total*100:.1f}% {'✅' if hall/total <= 0.1 else '❌'} (target <10%)")
print(f"  Correct Rate       : {corr}/{total} = {corr/total*100:.1f}%")
print(f"  p50 Latency        : {p50}ms {'✅' if p50 <= 2000 else '❌'} (target <2000ms)")
print(f"  p95 Latency        : {p95}ms {'✅' if p95 <= 4000 else '❌'} (target <4000ms)")
print(f"{'='*44}\n")