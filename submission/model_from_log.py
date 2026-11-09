"""Count the model ids the harness itself recorded in a Claude Code session log. Reads only the `model`
field of assistant messages; prints counts and the session id, nothing else. Usage: model_from_log.py <session.jsonl>"""
import json, sys, collections
p = sys.argv[1]
c = collections.Counter(); n = 0; first = last = None
with open(p, encoding="utf-8") as f:
    for line in f:
        try: rec = json.loads(line)
        except Exception: continue
        msg = rec.get("message") if isinstance(rec, dict) else None
        if isinstance(msg, dict) and msg.get("role") == "assistant" and msg.get("model"):
            c[msg["model"]] += 1; n += 1
            ts = rec.get("timestamp")
            if ts:
                first = first or ts; last = ts
print("session file:", p.rsplit("/", 1)[-1])
print("assistant messages with a model field:", n, "| first:", first, "| last:", last)
for m, k in c.most_common(): print(f"  {m}: {k}")
