from typing import Dict, Any, List, Optional

def align_with_timestamps(data: Dict[str, Any], hesitation_threshold: float = 2.0) -> Dict[str, Any]:
    target_words = data["target_text"].strip().split()
    trans_words = data["transcribed_text"].strip().split()
    timestamps = data.get("word_timestamps", [])

    # --- Build a lookup list for transcript timestamps (same order as trans_words) ---
    # Assumption: word_timestamps corresponds to transcribed_text word order
    trans_ts: List[Optional[Dict[str, Any]]] = []
    for i in range(len(trans_words)):
        if i < len(timestamps) and timestamps[i]["word"] == trans_words[i]:
            trans_ts.append(timestamps[i])
        else:
            # fallback if mismatch (still keep alignment running)
            trans_ts.append(None)

    n, m = len(target_words), len(trans_words)

    # DP + backtrack
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    back = [[None] * (m + 1) for _ in range(n + 1)]

    for i in range(n + 1):
        dp[i][0] = i
        if i > 0:
            back[i][0] = "deletion"
    for j in range(m + 1):
        dp[0][j] = j
        if j > 0:
            back[0][j] = "insertion"

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = 0 if target_words[i - 1] == trans_words[j - 1] else 1

            sub_cost = dp[i - 1][j - 1] + cost
            del_cost = dp[i - 1][j] + 1
            ins_cost = dp[i][j - 1] + 1

            best = min(sub_cost, del_cost, ins_cost)
            dp[i][j] = best

            if best == sub_cost:
                back[i][j] = "correct" if cost == 0 else "substitution"
            elif best == del_cost:
                back[i][j] = "deletion"
            else:
                back[i][j] = "insertion"

    # --- Backtrack + attach timestamps ---
    i, j = n, m
    alignment = []

    while i > 0 or j > 0:
        op = back[i][j]

        if op in ("correct", "substitution"):
            ts = trans_ts[j - 1] if (j - 1) >= 0 else None
            alignment.append({
                "op": op,
                "target_word": target_words[i - 1],
                "transcribed_word": trans_words[j - 1],
                "start": ts["start"] if ts else None,
                "end": ts["end"] if ts else None,
                "duration": (ts["end"] - ts["start"]) if ts else None,
            })
            i -= 1
            j -= 1

        elif op == "deletion":
            alignment.append({
                "op": "deletion",
                "target_word": target_words[i - 1],
                "transcribed_word": None,
                "start": None,
                "end": None,
                "duration": None,
            })
            i -= 1

        elif op == "insertion":
            ts = trans_ts[j - 1] if (j - 1) >= 0 else None
            alignment.append({
                "op": "insertion",
                "target_word": None,
                "transcribed_word": trans_words[j - 1],
                "start": ts["start"] if ts else None,
                "end": ts["end"] if ts else None,
                "duration": (ts["end"] - ts["start"]) if ts else None,
            })
            j -= 1

    alignment.reverse()

    # --- Compute hesitation gaps (pause between spoken words) ---
    hesitations = 0
    prev_end = None

    for step in alignment:
        if step["start"] is None or step["end"] is None:
            step["gap_before"] = None
            step["is_hesitation"] = False
            continue

        if prev_end is None:
            step["gap_before"] = 0.0
            step["is_hesitation"] = False
        else:
            gap = step["start"] - prev_end
            step["gap_before"] = round(gap, 3)
            step["is_hesitation"] = gap >= hesitation_threshold
            if step["is_hesitation"]:
                hesitations += 1

        prev_end = step["end"]

    # --- Stats ---
    correct = sum(1 for a in alignment if a["op"] == "correct")
    subs = sum(1 for a in alignment if a["op"] == "substitution")
    dels = sum(1 for a in alignment if a["op"] == "deletion")
    ins = sum(1 for a in alignment if a["op"] == "insertion")

    total_target = len(target_words)
    errors = subs + dels
    accuracy = (correct / total_target) * 100 if total_target > 0 else 0.0

    return {
        "alignment": alignment,
        "distance": dp[n][m],
        "stats": {
            "correct": correct,
            "substitution": subs,
            "deletion": dels,
            "insertion": ins,
            "errors": errors,
            "accuracy_percent": round(accuracy, 2),
            "hesitation_count": hesitations,
            "hesitation_threshold_sec": hesitation_threshold
        }
    }
data = {
  "target_text": "The quick brown fox",
  "transcribed_text": "The kick brown box",
  "word_timestamps": [
    {"word": "The", "start": 0.5, "end": 0.8},
    {"word": "kick", "start": 3.2, "end": 3.7},
    {"word": "brown", "start": 3.9, "end": 4.2},
    {"word": "box", "start": 4.5, "end": 4.9}
  ]
}

result = align_with_timestamps(data, hesitation_threshold=2.0)
"""

for step in result["alignment"]:
    print(step)

print("\nSTATS:", result["stats"])
"""
