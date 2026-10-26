_PREFIX = 7


def fuzzy_deletes(key: str) -> set[str]:
    """Symmetric-delete keys over the first 7 characters: the prefix and each one-char deletion."""
    p = key[:_PREFIX]
    return {p} | {p[:i] + p[i + 1 :] for i in range(len(p))}


def max_distance(key: str) -> int:
    return 1 if len(key) <= 4 else 2


def osa_within(a: str, b: str, k: int) -> int | None:
    """Restricted Damerau (OSA) distance, or None when it exceeds k."""
    if abs(len(a) - len(b)) > k:
        return None
    prev2: list[int] = []
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i] + [0] * len(b)
        for j, cb in enumerate(b, 1):
            cost = 0 if ca == cb else 1
            best = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost)
            if i > 1 and j > 1 and ca == b[j - 2] and a[i - 2] == cb:
                best = min(best, prev2[j - 2] + 1)
            cur[j] = best
        if min(cur) > k:
            return None
        prev2, prev = prev, cur
    return prev[-1] if prev[-1] <= k else None
