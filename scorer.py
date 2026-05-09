import time, math
AGE_HALFLIFE_HOURS = 12

def score_items(items):
    now = time.time()
    scored = []
    for item in items:
        v = _velocity(item, now)
        scored.append({**item, "velocity": v})
    scored.sort(key=lambda x: x["velocity"], reverse=True)
    return scored

def _velocity(item, now):
    interactions = float(item.get("interactions", 0))
    raw = float(item.get("score_raw", 0))
    created_ts = item.get("created_ts", 0)
    engagement = interactions * 0.6 + raw * 0.4
    if created_ts > 0:
        age_hours = max(0.1, (now - created_ts) / 3600)
        decay = math.exp(-0.693 * age_hours / AGE_HALFLIFE_HOURS)
    else:
        decay = 0.5
    return engagement * decay + (1.0 if created_ts > 0 else 0.0)
