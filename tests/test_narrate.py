"""Narration shared by `play`, the MCP tools and the scorecard.

Run:  python -m pytest tests/test_narrate.py -v
"""

from test_fun_metrics import FIXTURES  # noqa: E402,F401

from htn_metrics.narrate import narrate_fact, narrate_intention, narrate_operator  # noqa: E402


def test_known_core_operators_read_as_sentences():
    text = narrate_operator("opLure(warden, bearer, exit, corridor)")
    assert "warden" in text and "bearer" in text and "corridor" in text
    assert "action completed" not in text
    text = narrate_operator("opCastRegion(player, ignite, corridor, oil, scorched)")
    assert "ignite" in text and "oil" in text and "scorched" in text


def test_unknown_operators_fall_back_to_their_effects():
    text = narrate_operator("opWhatever(a, b)", dels=["foo(a)"], adds=["bar(b)"])
    assert "foo(a)" in text and "bar(b)" in text
    assert narrate_operator("opNothing(a)") != ""


def test_intentions_are_first_person_from_the_companion():
    text = narrate_intention("opLure(warden, bearer, exit, corridor)", actor="warden")
    assert text.startswith("Warden:")
    assert "I" in text


def test_facts_read_as_phrases():
    assert narrate_fact("at(player,entry)") == "player at entry"
    assert narrate_fact("status(bearer,snared)") == "bearer is snared"
    assert narrate_fact("regionHas(corridor,oil)") == "corridor has oil"
