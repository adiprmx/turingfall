import random
from turingfall.core.challenge import Answer, Challenge
from turingfall.core.registry import solver
from turingfall.synth import CHARS

@solver
class Random:
    name = "baseline_random"
    manifest = {"usd_per_1k": 0.0, "needs": [], "classes": "A"}

    def solve(self, ch: Challenge) -> Answer:
        rng = random.Random(ch.id)
        return Answer("".join(rng.choice(CHARS) for _ in range(len(ch.truth or "AAAA"))), "text", 0.0)
