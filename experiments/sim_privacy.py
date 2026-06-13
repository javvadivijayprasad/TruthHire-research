"""Re-identification demonstration for shared candidate references (Section 4.3).

Shows that publishing SHA-256(email||phone) does NOT anonymize: because the
identifier space is small and enumerable, an adversary that can guess candidate
values recovers identities exactly. A keyed (HMAC) construction blocks an OUTSIDE
adversary but not a consortium INSIDER who holds the key -- motivating private
set intersection plus a disclosure threshold, which bounds insider leakage to
candidates the insider has itself seen.
"""
from __future__ import annotations
import hashlib
import hmac
import random
from typing import Dict, List


def _identifier_universe(n: int, rng: random.Random) -> List[str]:
    firsts = ["john", "jane", "alex", "sam", "maria", "wei", "raj", "ana", "omar", "li"]
    lasts = ["smith", "jones", "patel", "kim", "garcia", "khan", "nguyen", "lee", "brown", "das"]
    out = set()
    while len(out) < n:
        e = f"{rng.choice(firsts)}.{rng.choice(lasts)}{rng.randint(1,9999)}@mail.com"
        p = f"+1{rng.randint(2000000000,9999999999)}"
        out.add(f"{e}|{p}")
    return list(out)


def _sha(x: str) -> str:
    return hashlib.sha256(x.encode()).hexdigest()


def _hmac(key: bytes, x: str) -> str:
    return hmac.new(key, x.encode(), hashlib.sha256).hexdigest()


def run(seed: int = 20260612):
    rng = random.Random(seed)
    universe = _identifier_universe(20000, rng)
    shared = set(rng.sample(universe, 4000))            # flagged candidates in network
    key = b"network-secret-pepper"

    print(f"{'adversary coverage':>18} | {'naive SHA-256':>13} | {'keyed (outsider)':>16} | {'keyed (insider)':>15}")
    print("-" * 74)
    rows = []
    for coverage in (0.25, 0.5, 1.0):
        guess = set(rng.sample(universe, int(len(universe) * coverage)))
        targets = shared & guess                         # shared members adversary could guess

        # naive published hashes -> adversary recomputes and matches
        pub_naive = {_sha(x) for x in shared}
        reid_naive = sum(1 for x in targets if _sha(x) in pub_naive) / len(targets)

        # keyed published digests, outsider lacks key
        pub_keyed = {_hmac(key, x) for x in shared}
        reid_keyed_out = sum(1 for x in targets if _sha(x) in pub_keyed) / len(targets)  # wrong fn -> ~0

        # keyed, insider holds key
        reid_keyed_in = sum(1 for x in targets if _hmac(key, x) in pub_keyed) / len(targets)

        rows.append({"coverage": coverage, "reid_naive": round(reid_naive, 4),
                     "reid_keyed_outsider": round(reid_keyed_out, 4),
                     "reid_keyed_insider": round(reid_keyed_in, 4)})
        print(f"{int(coverage*100):>17}% | {reid_naive:>13.3f} | {reid_keyed_out:>16.3f} | {reid_keyed_in:>15.3f}")
    print("\nThreshold-t disclosure bounds the INSIDER: only candidates corroborated")
    print("by >= t organizations are revealed, so a single insider learns nothing")
    print("beyond candidates it (and t-1 others) already reported.")
    return rows


if __name__ == "__main__":
    run()
