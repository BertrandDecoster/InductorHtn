"""
Reproduces HtnParallelTests.cpp tests (plan-content only).
Tests the parallel() keyword for multi-agent parallel execution.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from conftest import HtnTestHelper


class TestParallelBasic:
    def test_basic_two_tasks(self):
        h = HtnTestHelper()
        program = (
            "doParallel() :- if(), do(parallel(taskA, taskB)). "
            "taskA :- del(), add(doneA). "
            "taskB :- del(), add(doneB). "
            "goals(doParallel())."
        )
        result = h.find_first_plan(program)
        assert "taskA" in result
        assert "taskB" in result

    def test_empty_block(self):
        h = HtnTestHelper()
        program = (
            "emptyParallel() :- if(), do(setup, parallel(), cleanup). "
            "setup :- del(stateS1), add(stateS2). "
            "cleanup :- del(stateC1), add(stateC2). "
            "stateS1. stateC1. "
            "goals(emptyParallel())."
        )
        result = h.find_first_plan(program)
        assert "setup" in result
        assert "cleanup" in result

    def test_single_task(self):
        h = HtnTestHelper()
        program = (
            "singleParallel() :- if(), do(parallel(onlyTask)). "
            "onlyTask :- del(), add(taskDone). "
            "goals(singleParallel())."
        )
        result = h.find_first_plan(program)
        assert "onlyTask" in result
