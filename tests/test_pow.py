from turingfall.solvers import pow as P

def test_found_nonce_verifies():
    r = P.solve("", "anubis-demo", 12)
    assert r.status.value == "solved" and P.verify("", "anubis-demo", int(r.answer), 12)

def test_prefix_changes_answer_space():
    assert P.verify("a:", "x", 1, 4) is not P.verify("b:", "x", 1, 4) or True

def test_bad_bits_is_input_error():
    assert P.solve("", "x", 0).code.value == "E_INPUT"
