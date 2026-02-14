"""
Reproduces HtnPlannerTests_SetOf.cpp tests.
Tests for allOf/anyOf semantics with exact C++ format matching.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from conftest import HtnTestHelper


class TestAllOfSetOf:
    """allOf tests from PlannerSetOfTest"""

    def test_allof_modifies_state_in_condition(self):
        h = HtnTestHelper()
        program = (
            "IsTrue(Test1). Alternative(Alternative1). Alternative(Alternative2).\r\n"
            "trace(?Value, ?Value2, ?Value3) :- del(), add(item(?Value, ?Value2, ?Value3)). \r\n"
            "deleteTrueIfExists(?Value) :- if(IsTrue(?Value)), do(deleteTrue(?Value)). \r\n"
            "deleteTrue(?Value) :- del(IsTrue(?Value)), add(). \r\n"
            "method(?Value) :- allOf, if(IsTrue(?Value), Alternative(?Alt)), do(try(deleteTrueIfExists(?Value)), trace(?Value, Method1, ?Alt)). \r\n"
            "goals(method(Test1)).\r\n"
        )
        result = h.find_all_plans(program)
        assert result == "[ { (deleteTrue(Test1), trace(Test1,Method1,Alternative1), trace(Test1,Method1,Alternative2)) } ]"
        facts = h.get_all_solution_facts()
        assert facts == "[ { Alternative(Alternative1) => ,Alternative(Alternative2) => ,item(Test1,Method1,Alternative1) => ,item(Test1,Method1,Alternative2) =>  } ]"

    def test_allof_no_condition(self):
        h = HtnTestHelper()
        program = (
            "IsTrue(Test1). Alternative(Alternative1). Alternative(Alternative2).\r\n"
            "trace(?Value, ?Value2, ?Value3) :- del(), add(item(?Value, ?Value2, ?Value3)). \r\n"
            "method(?Value) :- allOf, if(), do(trace(?Value, Method1, None)). \r\n"
            "goals(method(Test1)).\r\n"
        )
        result = h.find_all_plans(program)
        assert result == "[ { (trace(Test1,Method1,None)) } ]"
        facts = h.get_all_solution_facts()
        assert facts == "[ { IsTrue(Test1) => ,Alternative(Alternative1) => ,Alternative(Alternative2) => ,item(Test1,Method1,None) =>  } ]"

    def test_allof_all_subtasks_succeed(self):
        h = HtnTestHelper()
        program = (
            "IsTrue(Test1). Alternative(Alternative1). Alternative(Alternative2).\r\n"
            "trace(?Value, ?Value2, ?Value3) :- del(), add(item(?Value, ?Value2, ?Value3)). \r\n"
            "method(?Value) :- allOf, if(IsTrue(?Value), Alternative(?Alt)), do(trace(?Value, Method1, ?Alt)). \r\n"
            "goals(method(Test1)).\r\n"
        )
        result = h.find_all_plans(program)
        assert result == "[ { (trace(Test1,Method1,Alternative1), trace(Test1,Method1,Alternative2)) } ]"
        facts = h.get_all_solution_facts()
        assert facts == "[ { IsTrue(Test1) => ,Alternative(Alternative1) => ,Alternative(Alternative2) => ,item(Test1,Method1,Alternative1) => ,item(Test1,Method1,Alternative2) =>  } ]"

    def test_allof_fails_then_normal_method_succeeds(self):
        h = HtnTestHelper()
        program = (
            "IsTrue(Test1). Alternative(Alternative1). Alternative(Alternative2).\r\n"
            "trace(?Value, ?Value2, ?Value3) :- del(), add(item(?Value, ?Value2, ?Value3)). \r\n"
            "method(?Value) :- allOf, if(IsTrue(Test2), Alternative(?Alt)), do(trace(?Value, MethodAllOf, ?Alt)). \r\n"
            "method(?Value) :- if(IsTrue(?Value), Alternative(?Alt)), do(trace(?Value, MethodNormal, ?Alt)). \r\n"
            "goals(method(Test1)).\r\n"
        )
        result = h.find_all_plans(program)
        assert result == "[ { (trace(Test1,MethodNormal,Alternative1)) } { (trace(Test1,MethodNormal,Alternative2)) } ]"
        facts = h.get_all_solution_facts()
        assert facts == "[ { IsTrue(Test1) => ,Alternative(Alternative1) => ,Alternative(Alternative2) => ,item(Test1,MethodNormal,Alternative1) =>  } { IsTrue(Test1) => ,Alternative(Alternative1) => ,Alternative(Alternative2) => ,item(Test1,MethodNormal,Alternative2) =>  } ]"

    def test_allof_preceded_and_followed_by_operator(self):
        h = HtnTestHelper()
        program = (
            "IsTrue(Test1). Alternative(Alternative1). Alternative(Alternative2).\r\n"
            "trace(?Value, ?Value2, ?Value3) :- del(), add(item(?Value, ?Value2, ?Value3)). \r\n"
            "method(?Value) :- allOf, if(IsTrue(?Value), Alternative(?Alt)), do(trace(?Value, Method1, ?Alt)). \r\n"
            "goals(trace(Finish, Finish1, Finish2), method(Test1), trace(Finish3, Finish4, Finish5)).\r\n"
        )
        result = h.find_all_plans(program)
        assert result == "[ { (trace(Finish,Finish1,Finish2), trace(Test1,Method1,Alternative1), trace(Test1,Method1,Alternative2), trace(Finish3,Finish4,Finish5)) } ]"
        facts = h.get_all_solution_facts()
        assert facts == "[ { IsTrue(Test1) => ,Alternative(Alternative1) => ,Alternative(Alternative2) => ,item(Finish,Finish1,Finish2) => ,item(Test1,Method1,Alternative1) => ,item(Test1,Method1,Alternative2) => ,item(Finish3,Finish4,Finish5) =>  } ]"

    def test_two_allof_methods(self):
        h = HtnTestHelper()
        program = (
            "IsTrue(Test1). IsTrue(Test2). Alternative(Alternative1). Alternative(Alternative2).\r\n"
            "trace(?Value, ?Value2, ?Value3) :- del(), add(item(?Value, ?Value2, ?Value3)). \r\n"
            "method(?Value) :- allOf, if(IsTrue(?Value), Alternative(?Alt)), do(trace(?Value, Method1, ?Alt)). \r\n"
            "goals(method(Test1), method(Test2)).\r\n"
        )
        result = h.find_all_plans(program)
        assert result == "[ { (trace(Test1,Method1,Alternative1), trace(Test1,Method1,Alternative2), trace(Test2,Method1,Alternative1), trace(Test2,Method1,Alternative2)) } ]"
        facts = h.get_all_solution_facts()
        assert facts == "[ { IsTrue(Test1) => ,IsTrue(Test2) => ,Alternative(Alternative1) => ,Alternative(Alternative2) => ,item(Test1,Method1,Alternative1) => ,item(Test1,Method1,Alternative2) => ,item(Test2,Method1,Alternative1) => ,item(Test2,Method1,Alternative2) =>  } ]"

    def test_allof_followed_by_normal_method_two_solutions(self):
        h = HtnTestHelper()
        program = (
            "IsTrue(Test1). IsTrue(Test2). Alternative(Alternative1). Alternative(Alternative2).\r\n"
            "trace(?Value, ?Value2, ?Value3) :- del(), add(item(?Value, ?Value2, ?Value3)). \r\n"
            "method(?Value) :- allOf, if(IsTrue(?Value), Alternative(?Alt)), do(trace(AllSet, ?Value, ?Alt)). \r\n"
            "method2(?Value) :- if(IsTrue(?Value), Alternative(?Alt)), do(trace(Normal, ?Value, ?Alt)). \r\n"
            "goals(method(Test1), method2(Test2)).\r\n"
        )
        result = h.find_all_plans(program)
        assert result == "[ { (trace(AllSet,Test1,Alternative1), trace(AllSet,Test1,Alternative2), trace(Normal,Test2,Alternative1)) } { (trace(AllSet,Test1,Alternative1), trace(AllSet,Test1,Alternative2), trace(Normal,Test2,Alternative2)) } ]"
        facts = h.get_all_solution_facts()
        assert facts == "[ { IsTrue(Test1) => ,IsTrue(Test2) => ,Alternative(Alternative1) => ,Alternative(Alternative2) => ,item(AllSet,Test1,Alternative1) => ,item(AllSet,Test1,Alternative2) => ,item(Normal,Test2,Alternative1) =>  } { IsTrue(Test1) => ,IsTrue(Test2) => ,Alternative(Alternative1) => ,Alternative(Alternative2) => ,item(AllSet,Test1,Alternative1) => ,item(AllSet,Test1,Alternative2) => ,item(Normal,Test2,Alternative2) =>  } ]"

    def test_allof_one_subtask_fails(self):
        h = HtnTestHelper()
        program = (
            "IsTrue(Test1). Alternative(Alternative1). Alternative(Alternative2).Combo(Test1,Alternative1).\r\n"
            "trace(?Value, ?Value2, ?Value3) :- del(), add(item(?Value, ?Value2, ?Value3)). \r\n"
            "method(?Value) :- allOf, if(IsTrue(?Value), Alternative(?Alt)), do(subtask(?Value, ?Alt)). \r\n"
            "subtask(?Value1, ?Value2) :- if(Combo(?Value1, ?Value2)), do(trace(?Value1, ?Value2)).\r\n"
            "goals(method(Test1)).\r\n"
        )
        result = h.find_all_plans(program)
        assert result == "null"
        facts = h.get_all_solution_facts()
        assert facts == "null"

    def test_allof_partial_success_then_normal_method(self):
        h = HtnTestHelper()
        program = (
            "IsTrue(Test1). IsTrue(Test2). Alternative(Alternative1). Alternative(Alternative2).\r\n"
            "IsTrue(Test1, Alternative1). \r\n"
            "trace(?Value, ?Value2, ?Value3) :- del(), add(item(?Value, ?Value2, ?Value3)). \r\n"
            "method(?Value) :- allOf, if(Alternative(?Alt)), do(method2(?Value, ?Alt)). \r\n"
            "method(?Value) :- if(IsTrue(?Value), Alternative(?Alt)), do(trace(Normal, ?Value, ?Alt)). \r\n"
            "method2(?Value, ?Alt) :- if(IsTrue(?Value, ?Alt)), do(trace(Method2, ?Value, ?Alt)).\r\n"
            "goals(method(Test1)).\r\n"
        )
        result = h.find_all_plans(program)
        assert result == "[ { (trace(Normal,Test1,Alternative1)) } { (trace(Normal,Test1,Alternative2)) } ]"
        facts = h.get_all_solution_facts()
        assert facts == "[ { IsTrue(Test1) => ,IsTrue(Test2) => ,Alternative(Alternative1) => ,Alternative(Alternative2) => ,IsTrue(Test1,Alternative1) => ,item(Normal,Test1,Alternative1) =>  } { IsTrue(Test1) => ,IsTrue(Test2) => ,Alternative(Alternative1) => ,Alternative(Alternative2) => ,IsTrue(Test1,Alternative1) => ,item(Normal,Test1,Alternative2) =>  } ]"

    def test_allof_followed_by_normal_with_one_failure(self):
        h = HtnTestHelper()
        program = (
            "IsTrue(Test1). IsTrue(Test2). Alternative(Alternative1). Alternative(Alternative2).\r\n"
            "IsTrue(Test2, Alternative2). \r\n"
            "trace(?Value, ?Value2, ?Value3) :- del(), add(item(?Value, ?Value2, ?Value3)). \r\n"
            "method(?Value) :- allOf, if(IsTrue(?Value), Alternative(?Alt)), do(trace(AllSet, ?Value, ?Alt)). \r\n"
            "method2(?Value) :- if(IsTrue(?Value), Alternative(?Alt)), do(method3(?Value, ?Alt)). \r\n"
            "method3(?Value, ?Alt) :- if(IsTrue(?Value, ?Alt)), do(trace(Normal, ?Value, ?Alt)). \r\n"
            "goals(method(Test1), method2(Test2)).\r\n"
        )
        result = h.find_all_plans(program)
        assert result == "[ { (trace(AllSet,Test1,Alternative1), trace(AllSet,Test1,Alternative2), trace(Normal,Test2,Alternative2)) } ]"
        facts = h.get_all_solution_facts()
        assert facts == "[ { IsTrue(Test1) => ,IsTrue(Test2) => ,Alternative(Alternative1) => ,Alternative(Alternative2) => ,IsTrue(Test2,Alternative2) => ,item(AllSet,Test1,Alternative1) => ,item(AllSet,Test1,Alternative2) => ,item(Normal,Test2,Alternative2) =>  } ]"


class TestAnyOfSetOf:
    """anyOf tests from PlannerSetOfTest"""

    def test_anyof_all_subtasks_succeed(self):
        h = HtnTestHelper()
        program = (
            "IsTrue(Test1). Alternative(Alternative1). Alternative(Alternative2).\r\n"
            "trace(?Value, ?Value2, ?Value3) :- del(), add(item(?Value, ?Value2, ?Value3)). \r\n"
            "method(?Value) :- anyOf, if(IsTrue(?Value), Alternative(?Alt)), do(trace(?Value, Method1, ?Alt)). \r\n"
            "goals(method(Test1)).\r\n"
        )
        result = h.find_all_plans(program)
        assert result == "[ { (trace(Test1,Method1,Alternative1), trace(Test1,Method1,Alternative2)) } ]"
        facts = h.get_all_solution_facts()
        assert facts == "[ { IsTrue(Test1) => ,Alternative(Alternative1) => ,Alternative(Alternative2) => ,item(Test1,Method1,Alternative1) => ,item(Test1,Method1,Alternative2) =>  } ]"

    def test_anyof_preceded_and_followed_by_operator(self):
        h = HtnTestHelper()
        program = (
            "IsTrue(Test1). Alternative(Alternative1). Alternative(Alternative2).\r\n"
            "trace(?Value, ?Value2, ?Value3) :- del(), add(item(?Value, ?Value2, ?Value3)). \r\n"
            "method(?Value) :- anyOf, if(IsTrue(?Value), Alternative(?Alt)), do(trace(?Value, Method1, ?Alt)). \r\n"
            "goals(trace(Finish, Finish1, Finish2), method(Test1), trace(Finish3, Finish4, Finish5)).\r\n"
        )
        result = h.find_all_plans(program)
        assert result == "[ { (trace(Finish,Finish1,Finish2), trace(Test1,Method1,Alternative1), trace(Test1,Method1,Alternative2), trace(Finish3,Finish4,Finish5)) } ]"
        facts = h.get_all_solution_facts()
        assert facts == "[ { IsTrue(Test1) => ,Alternative(Alternative1) => ,Alternative(Alternative2) => ,item(Finish,Finish1,Finish2) => ,item(Test1,Method1,Alternative1) => ,item(Test1,Method1,Alternative2) => ,item(Finish3,Finish4,Finish5) =>  } ]"

    def test_two_anyof_methods(self):
        h = HtnTestHelper()
        program = (
            "IsTrue(Test1). IsTrue(Test2). Alternative(Alternative1). Alternative(Alternative2).\r\n"
            "trace(?Value, ?Value2, ?Value3) :- del(), add(item(?Value, ?Value2, ?Value3)). \r\n"
            "method(?Value) :- anyOf, if(IsTrue(?Value), Alternative(?Alt)), do(trace(?Value, Method1, ?Alt)). \r\n"
            "goals(method(Test1), method(Test2)).\r\n"
        )
        result = h.find_all_plans(program)
        assert result == "[ { (trace(Test1,Method1,Alternative1), trace(Test1,Method1,Alternative2), trace(Test2,Method1,Alternative1), trace(Test2,Method1,Alternative2)) } ]"
        facts = h.get_all_solution_facts()
        assert facts == "[ { IsTrue(Test1) => ,IsTrue(Test2) => ,Alternative(Alternative1) => ,Alternative(Alternative2) => ,item(Test1,Method1,Alternative1) => ,item(Test1,Method1,Alternative2) => ,item(Test2,Method1,Alternative1) => ,item(Test2,Method1,Alternative2) =>  } ]"

    def test_anyof_followed_by_normal_two_solutions(self):
        h = HtnTestHelper()
        program = (
            "IsTrue(Test1). IsTrue(Test2). Alternative(Alternative1). Alternative(Alternative2).\r\n"
            "trace(?Value, ?Value2, ?Value3) :- del(), add(item(?Value, ?Value2, ?Value3)). \r\n"
            "method(?Value) :- anyOf, if(IsTrue(?Value), Alternative(?Alt)), do(trace(AllSet, ?Value, ?Alt)). \r\n"
            "method2(?Value) :- if(IsTrue(?Value), Alternative(?Alt)), do(trace(Normal, ?Value, ?Alt)). \r\n"
            "goals(method(Test1), method2(Test2)).\r\n"
        )
        result = h.find_all_plans(program)
        assert result == "[ { (trace(AllSet,Test1,Alternative1), trace(AllSet,Test1,Alternative2), trace(Normal,Test2,Alternative1)) } { (trace(AllSet,Test1,Alternative1), trace(AllSet,Test1,Alternative2), trace(Normal,Test2,Alternative2)) } ]"
        facts = h.get_all_solution_facts()
        assert facts == "[ { IsTrue(Test1) => ,IsTrue(Test2) => ,Alternative(Alternative1) => ,Alternative(Alternative2) => ,item(AllSet,Test1,Alternative1) => ,item(AllSet,Test1,Alternative2) => ,item(Normal,Test2,Alternative1) =>  } { IsTrue(Test1) => ,IsTrue(Test2) => ,Alternative(Alternative1) => ,Alternative(Alternative2) => ,item(AllSet,Test1,Alternative1) => ,item(AllSet,Test1,Alternative2) => ,item(Normal,Test2,Alternative2) =>  } ]"

    def test_anyof_one_subtask_fails(self):
        h = HtnTestHelper()
        program = (
            "IsTrue(Test1). Alternative(Alternative1). Alternative(Alternative2).Combo(Test1,Alternative1).\r\n"
            "trace(?Value, ?Value2) :- del(), add(item(?Value, ?Value2)). \r\n"
            "method(?Value) :- anyOf, if(IsTrue(?Value), Alternative(?Alt)), do(subtask(?Value, ?Alt)). \r\n"
            "subtask(?Value1, ?Value2) :- if(Combo(?Value1, ?Value2)), do(trace(?Value1, ?Value2)).\r\n"
            "goals(method(Test1)).\r\n"
        )
        result = h.find_all_plans(program)
        assert result == "[ { (trace(Test1,Alternative1)) } ]"
        facts = h.get_all_solution_facts()
        assert facts == "[ { IsTrue(Test1) => ,Alternative(Alternative1) => ,Alternative(Alternative2) => ,Combo(Test1,Alternative1) => ,item(Test1,Alternative1) =>  } ]"

    def test_anyof_followed_by_normal_with_one_failure(self):
        h = HtnTestHelper()
        program = (
            "IsTrue(Test1). IsTrue(Test2). Alternative(Alternative1). Alternative(Alternative2).\r\n"
            "IsTrue(Test2, Alternative2). \r\n"
            "trace(?Value, ?Value2, ?Value3) :- del(), add(item(?Value, ?Value2, ?Value3)). \r\n"
            "method(?Value) :- anyOf, if(IsTrue(?Value), Alternative(?Alt)), do(trace(AllSet, ?Value, ?Alt)). \r\n"
            "method2(?Value) :- if(IsTrue(?Value), Alternative(?Alt)), do(method3(?Value, ?Alt)). \r\n"
            "method3(?Value, ?Alt) :- if(IsTrue(?Value, ?Alt)), do(trace(Normal, ?Value, ?Alt)). \r\n"
            "goals(method(Test1), method2(Test2)).\r\n"
        )
        result = h.find_all_plans(program)
        assert result == "[ { (trace(AllSet,Test1,Alternative1), trace(AllSet,Test1,Alternative2), trace(Normal,Test2,Alternative2)) } ]"
        facts = h.get_all_solution_facts()
        assert facts == "[ { IsTrue(Test1) => ,IsTrue(Test2) => ,Alternative(Alternative1) => ,Alternative(Alternative2) => ,IsTrue(Test2,Alternative2) => ,item(AllSet,Test1,Alternative1) => ,item(AllSet,Test1,Alternative2) => ,item(Normal,Test2,Alternative2) =>  } ]"


class TestSingleSolution:
    """Reproduces PlannerSingleSolutionTest from HtnPlannerTests_SetOf.cpp"""

    def test_single_solution_anyof_then_normal(self):
        h = HtnTestHelper()
        program = (
            "IsTrue(Test1). IsTrue(Test2). Alternative(Alternative1). Alternative(Alternative2).\r\n"
            "trace(?Value, ?Value2, ?Value3) :- del(), add(item(?Value, ?Value2, ?Value3)). \r\n"
            "method(?Value) :- anyOf, if(IsTrue(?Value), Alternative(?Alt)), do(trace(AllSet, ?Value, ?Alt)). \r\n"
            "method2(?Value) :- if(IsTrue(?Value), Alternative(?Alt)), do(trace(Normal, ?Value, ?Alt)). \r\n"
            "goals(method(Test1), method2(Test2)).\r\n"
        )
        result = h.find_first_plan(program)
        assert result == "(trace(AllSet,Test1,Alternative1), trace(AllSet,Test1,Alternative2), trace(Normal,Test2,Alternative1))"

    def test_single_solution_allof_then_normal(self):
        h = HtnTestHelper()
        program = (
            "IsTrue(Test1). IsTrue(Test2). Alternative(Alternative1). Alternative(Alternative2).\r\n"
            "trace(?Value, ?Value2, ?Value3) :- del(), add(item(?Value, ?Value2, ?Value3)). \r\n"
            "method(?Value) :- allOf, if(IsTrue(?Value), Alternative(?Alt)), do(trace(AllSet, ?Value, ?Alt)). \r\n"
            "method2(?Value) :- if(IsTrue(?Value), Alternative(?Alt)), do(trace(Normal, ?Value, ?Alt)). \r\n"
            "goals(method(Test1), method2(Test2)).\r\n"
        )
        result = h.find_first_plan(program)
        assert result == "(trace(AllSet,Test1,Alternative1), trace(AllSet,Test1,Alternative2), trace(Normal,Test2,Alternative1))"
