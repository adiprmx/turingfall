from turingfall.core.scoring import summarize, wilson

def test_wilson_bounds():
    lo, hi = wilson(0, 10)
    assert 0.0 <= lo <= hi <= 1.0

def test_per_session_beats_per_challenge():
    recs = [{"challenge_id": f"c{i}", "family": "t", "cls": "A", "attempt": 1,
             "correct": i % 2 == 0, "latency_s": 0.01, "cost_usd": 0.0} for i in range(10)]
    recs += [{"challenge_id": f"c{i}", "family": "t", "cls": "A", "attempt": 2,
              "correct": True, "latency_s": 0.01, "cost_usd": 0.0} for i in range(1, 10, 2)]
    s = summarize(recs, 3)
    assert s["per_challenge"] == 0.5 and s["per_session_at_3"] > s["per_challenge"]
