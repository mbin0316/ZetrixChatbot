import json
import numpy as np

with open("results.jsonl") as f:
    rows = [json.loads(line) for line in f]

total = len(rows)
hits, hallucinated, correct = 0, 0, 0
latencies = []

for row in rows:
    hits        += int(row.get("hit", 0) or 0)
    hallucinated += int(row.get("hallucinated", 0) or 0)
    correct     += int(row.get("correct", 0) or 0)
    if row.get("latency_ms"):
        latencies.append(int(row["latency_ms"]))

p50 = int(np.percentile(latencies, 50)) if latencies else 0
p95 = int(np.percentile(latencies, 95)) if latencies else 0

print("============================================")
print(f"  Retrieval Hit Rate : {hits}/{total} = {hits/total*100:.1f}%  {'✅' if hits/total >= 0.8 else '❌'} (target >80%)")
print(f"  Hallucination Rate : {hallucinated}/{total} = {hallucinated/total*100:.1f}% {'✅' if hallucinated/total < 0.1 else '❌'} (target <10%)")
print(f"  Correct Rate       : {correct}/{total} = {correct/total*100:.1f}%")
print(f"  p50 Latency        : {p50}ms {'✅' if p50 < 2000 else '❌'} (target <2000ms)")
print(f"  p95 Latency        : {p95}ms {'✅' if p95 < 4000 else '❌'} (target <4000ms)")
print("============================================")