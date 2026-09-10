"""Player-perspective play over a level's plan space.

The MCP level tools are a playtest, not an oracle: the caller sees what the
player would see (their region, their skills, the companions' stated
intentions), is offered their own legal actions without strategy labels,
acts, and only afterwards asks the planner to explain what was reached and
what was missed. Off-plan actions are allowed when forced, and re-plan from
the resulting world - which is how a mistake becomes observable.

These tests drive the session object directly; the MCP server wraps it.

Run:  python -m pytest mcp-server/tests/test_level_tools.py -v
"""

import json
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_PROJECT = os.path.abspath(os.path.join(_HERE, "..", ".."))
for _p in (os.path.join(_PROJECT, "src", "Python"), os.path.join(_PROJECT, "mcp-server")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from indhtn_mcp.level_tools import LevelSession, fun_profile  # noqa: E402

REFERENCE_GOOD = os.path.join(_PROJECT, "tests", "fun_fixtures", "reference_good")
GREASE_TRAP = os.path.join(_PROJECT, "levels", "grease_trap")


def _play_to_the_end(session, pick=0):
    while not session.done:
        actions = session.actions()
        if not actions:
            break
        session.act(actions[min(pick, len(actions) - 1)]["action"])
    return session


def test_observation_is_the_players_view_not_the_planners(tmp_path):
    session = LevelSession(REFERENCE_GOOD, playthrough_dir=str(tmp_path))
    obs = session.observe()
    assert obs["step"] == 0
    assert obs["you"] == "player"
    assert "companions" in obs and "enemies" in obs
    text = json.dumps(obs)
    assert "theQuietRun" not in text and "theLoudRun" not in text, (
        "strategy names are the planner's, not the player's"
    )


def test_actions_are_the_players_own_after_companions_open(tmp_path):
    """reference_good opens with three companion clears; the first thing the
    player is asked is which route move to make."""
    session = LevelSession(REFERENCE_GOOD, playthrough_dir=str(tmp_path))
    actions = session.actions()
    assert session.step == 3, "companion steps were auto-advanced"
    assert len(actions) >= 2
    for action in actions:
        assert action["actor"] == "player"
        assert "narration" in action and "consequences" in action
        assert "theQuietRun" not in action["narration"]
    intentions = session.observe()["companions"]
    assert any(c.get("intention") for c in intentions) or session.done


def test_act_narrows_the_plans_and_records_the_walk(tmp_path):
    session = LevelSession(REFERENCE_GOOD, playthrough_dir=str(tmp_path))
    before = session.plans_remaining
    actions = session.actions()
    result = session.act(actions[0]["action"])
    assert 0 < session.plans_remaining < before
    assert result["accepted"] is True

    _play_to_the_end(session)
    assert session.done
    files = list((tmp_path / "reference_good").glob("*.json"))
    assert len(files) == 1
    data = json.loads(files[0].read_text(encoding="utf-8"))
    assert data["level"] == "reference_good"
    assert data["final_class"]
    assert any(len(step["actions_offered"]) >= 2 for step in data["steps"])


def test_undo_returns_to_the_previous_decision(tmp_path):
    session = LevelSession(REFERENCE_GOOD, playthrough_dir=str(tmp_path))
    actions = session.actions()
    step_before = session.step
    session.act(actions[0]["action"])
    assert session.step > step_before
    session.undo()
    assert session.step == step_before
    assert [a["action"] for a in session.actions()] == [a["action"] for a in actions]


def test_explain_names_what_was_reached_and_what_was_missed(tmp_path):
    session = _play_to_the_end(LevelSession(REFERENCE_GOOD, playthrough_dir=str(tmp_path)))
    explanation = session.explain()
    assert explanation["reached_class"]
    assert explanation["missed_classes"], "the other route was never taken"
    assert explanation["decisions"], "each decision lists the alternatives and where they led"


def test_forcing_an_off_plan_action_replans_from_the_new_world(tmp_path):
    """Wasting the only ignite charge before the fight: no plan survives,
    and the session says so instead of pretending."""
    session = LevelSession(GREASE_TRAP, playthrough_dir=str(tmp_path))
    assert session.plans_remaining > 0
    refused = session.act("opSpendCharge(player, ignite, i1)")
    assert refused["accepted"] is False
    forced = session.act("opSpendCharge(player, ignite, i1)", force=True)
    assert forced["accepted"] is True and forced["forced"] is True
    assert session.plans_remaining == 0
    assert session.done
    files = list((tmp_path / "grease_trap").glob("*.json"))
    data = json.loads(files[0].read_text(encoding="utf-8"))
    assert data["steps"][0]["forced"] is True


def test_fun_profile_is_available_to_the_tools():
    profile = fun_profile(REFERENCE_GOOD)
    assert profile["level_id"] == "reference_good"
    assert {f["key"] for f in profile["families"]} >= {"f1_multiplicity", "f6_player"}
