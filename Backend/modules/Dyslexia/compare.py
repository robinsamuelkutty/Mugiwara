from typing import Dict, Any, List, Optional
from rapidfuzz.distance import Levenshtein


# ------------------ Mispronunciation Check (Fast) ------------------
def is_likely_mispronunciation(a: str, b: str) -> bool:
    a = a.lower().strip()
    b = b.lower().strip()

    # exact match handled separately
    if a == b:
        return False

    # big length difference => likely error
    if abs(len(a) - len(b)) >= 3:
        return False

    # normalized similarity using edit distance
    dist = Levenshtein.distance(a, b)
    max_len = max(len(a), len(b))
    similarity = 1 - (dist / max_len)

    # tune this threshold if needed
    return similarity >= 0.6


# ------------------ Main Compare Function ------------------
def compare_text(data: Dict[str, Any]) -> Dict[str, Any]:
    target_words = data["target_text"].strip().split()
    trans_words = data["transcribed_text"].strip().split()
    timestamps = data.get("word_timestamps", [])

    # transcript timestamps aligned with trans_words order
    trans_ts: List[Optional[Dict[str, Any]]] = []
    for i in range(len(trans_words)):
        if i < len(timestamps) and timestamps[i].get("word") == trans_words[i]:
            trans_ts.append(timestamps[i])
        else:
            trans_ts.append(None)

    n, m = len(target_words), len(trans_words)

    # ------------------ Levenshtein DP + Backtrack ------------------
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
            cost = 0 if target_words[i - 1].lower() == trans_words[j - 1].lower() else 1

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

    # ------------------ Backtrack Alignment ------------------
    i, j = n, m
    alignment = []

    while i > 0 or j > 0:
        op = back[i][j]

        if op in ("correct", "substitution"):
            ts = trans_ts[j - 1] if (j - 1) >= 0 else None
            alignment.append({
                "op": op,
                "target_word": target_words[i - 1],
                "spoken_word": trans_words[j - 1],
                "start": ts["start"] if ts else None,
                "end": ts["end"] if ts else None,
            })
            i -= 1
            j -= 1

        elif op == "deletion":
            alignment.append({
                "op": "deletion",
                "target_word": target_words[i - 1],
                "spoken_word": None,
                "start": None,
                "end": None,
            })
            i -= 1

        elif op == "insertion":
            ts = trans_ts[j - 1] if (j - 1) >= 0 else None
            alignment.append({
                "op": "insertion",
                "target_word": None,
                "spoken_word": trans_words[j - 1],
                "start": ts["start"] if ts else None,
                "end": ts["end"] if ts else None,
            })
            j -= 1

    alignment.reverse()

    # ------------------ Convert to 3 Labels ------------------
    # correct / mispronunciation / error
    word_status = []

    for step in alignment:

        # Correct
        if step["op"] == "correct":
            word_status.append({
                "target_word": step["target_word"],
                "spoken_word": step["spoken_word"],
                "label": "correct",
                "confidence": 1.0,
                "reason": "Exact match",
                "start": step["start"],
                "end": step["end"],
            })

        # Substitution -> decide mispronunciation or error
        elif step["op"] == "substitution":
            target = step["target_word"]
            spoken = step["spoken_word"]

            # 1) Same word (extra safety)
            if target.lower() == spoken.lower():
                label = "correct"
                confidence = 1.0
                reason = "Exact match"

            # 2) Mispronunciation
            elif is_likely_mispronunciation(target, spoken):
                label = "mispronunciation"
                confidence = 0.7
                reason = "High similarity (edit-distance based)"

            # 3) Otherwise error
            else:
                label = "error"
                confidence = 0.9
                reason = "Too different from expected word"

            word_status.append({
                "target_word": target,
                "spoken_word": spoken,
                "label": label,
                "confidence": confidence,
                "reason": reason,
                "start": step["start"],
                "end": step["end"],
            })

        # insertion/deletion => error
        else:
            word_status.append({
                "target_word": step["target_word"],
                "spoken_word": step["spoken_word"],
                "label": "error",
                "confidence": 0.9,
                "reason": f"{step['op']} detected",
                "start": step["start"],
                "end": step["end"],
            })

    return {
        "target_text": data["target_text"],
        "transcribed_text": data["transcribed_text"],
        "distance": dp[n][m],
        "word_status": word_status
    }


# ------------------ TEST RUN ------------------
"""if __name__ == "__main__":
    data = {
        "target_text": "The quick brown fox",
        "transcribed_text": "The for brown box",
        "word_timestamps": [
            {"word": "The", "start": 0.5, "end": 0.8},
            {"word": "kick", "start": 3.2, "end": 3.7},
            {"word": "brown", "start": 3.9, "end": 4.2},
            {"word": "box", "start": 4.5, "end": 4.9}
        ]
    }

    output = compare_text(data)

    for row in output["word_status"]:
        print(row)
"""