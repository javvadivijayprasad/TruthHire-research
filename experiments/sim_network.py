"""Network-effect (flywheel) and fraud-ring detection experiments.

flywheel(): as the participation rate (fraction of organizations on the shared
network) grows, the chance that a repeat fraudster was already flagged by >= t
in-network organizations rises -- so the network's catch rate on repeat fraud
increases. This is the contributory-network effect, quantified.

fraud_ring(): a single actor applies under k synthetic identities that share one
secondary identifier (e.g., a reused phone). Linking on any shared identifier,
the network detects the ring once >= t of its identities have been seen.
"""
from __future__ import annotations
import random
from typing import Dict, List


def flywheel(participation: float, seed: int = 0, n_orgs: int = 50,
             n_fraud_actors: int = 2000, apps_per_actor: int = 4,
             threshold: int = 2) -> float:
    """Return the network catch rate on repeat-fraud applications."""
    rng = random.Random(seed)
    in_network = set(rng.sample(range(n_orgs), max(1, int(participation * n_orgs))))
    seen_by = {}                      # actor -> set of in-network orgs that flagged
    caught = 0; eligible = 0
    for _ in range(n_fraud_actors):
        orgs = rng.sample(range(n_orgs), min(apps_per_actor, n_orgs))
        prior = set()
        for k, org in enumerate(orgs):
            if k > 0:                 # repeat applications are the catchable ones
                eligible += 1
                if len(prior & in_network) >= threshold:
                    caught += 1
            if org in in_network:     # this org flags the (fraudulent) actor
                prior.add(org)
    return caught / eligible if eligible else 0.0


def fraud_ring(n_identities: int, seed: int = 0, n_actors: int = 1000,
               reuse_prob: float = 0.7, threshold: int = 2) -> float:
    """Detection rate of multi-identity fraud rings via shared-identifier linkage."""
    rng = random.Random(seed)
    detected = 0
    for _ in range(n_actors):
        # each identity may reuse a shared secondary identifier (phone)
        shared = sum(1 for _ in range(n_identities) if rng.random() < reuse_prob)
        if shared >= threshold:       # >= t identities linkable -> ring surfaces
            detected += 1
    return detected / n_actors
