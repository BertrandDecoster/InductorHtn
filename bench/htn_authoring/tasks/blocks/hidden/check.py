"""Blocks: exactly one plan, it reaches the goal, and it moves no more blocks than the reference."""
import re


def _moves(plan):
    return len(re.findall(r"\b(pickup|unstack)\(", plan))


def check_instance(want, got, inst):
    if len(got["plans"]) != 1:
        return False, f"{len(got['plans'])} plans, expected exactly 1"
    final = got["finals"][0] or []
    needed = inst["goal_facts"]
    missing = [g for g in needed if g not in final]
    if missing:
        return False, f"goal not reached, missing {missing}"
    if _moves(got["plans"][0]) > _moves(want["plans"][0]):
        return False, f"{_moves(got['plans'][0])} moves, reference needs {_moves(want['plans'][0])}"
    return True, ""
