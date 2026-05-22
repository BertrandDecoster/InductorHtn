//
//  HtnNumericFluentTests.cpp
//  TestLib
//
//  Tests for numeric-fluents support: parser recognition of
//  increase()/decrease() effect clauses on operators.
//
//  Task 1 only verifies that the compiler PARSES these clauses
//  and stores them on HtnOperator. Engine ignores them at apply time;
//  Task 2 will give them runtime semantics.
//

#include "FXPlatform/FailFast.h"
#include "FXPlatform/Parser/ParserDebug.h"
#include "FXPlatform/Prolog/HtnGoalResolver.h"
#include "FXPlatform/Prolog/HtnRuleSet.h"
#include "FXPlatform/Prolog/HtnTerm.h"
#include "FXPlatform/Prolog/HtnTermFactory.h"
#include "FXPlatform/Htn/HtnOperator.h"
#include "FXPlatform/Htn/HtnPlanner.h"
#include "FXPlatform/Htn/HtnCompiler.h"
#include "Logger.h"
#include "Tests/ParserTestBase.h"
#include "UnitTest++/UnitTest++.h"
using namespace Prolog;

SUITE(HtnNumericFluentTests)
{
    // Helper that pulls a specific operator out of a planner via AllOperators().
    // Returns nullptr if no operator matches the given name+arity.
    static HtnOperator *FindOperatorByNameArity(HtnPlanner *planner, const std::string &name, int arity)
    {
        HtnOperator *result = nullptr;
        planner->AllOperators([&](HtnOperator *op)
        {
            if (op->head()->name() == name && op->head()->arity() == arity)
            {
                result = op;
                return false; // stop iteration
            }
            return true;
        });
        return result;
    }

    TEST(IncreaseDecreaseClauses_ParsedAndStoredOnOperator)
    {
        shared_ptr<HtnTermFactory> factory = shared_ptr<HtnTermFactory>(new HtnTermFactory());
        shared_ptr<HtnRuleSet> state = shared_ptr<HtnRuleSet>(new HtnRuleSet());
        shared_ptr<HtnPlanner> planner = shared_ptr<HtnPlanner>(new HtnPlanner());
        shared_ptr<HtnCompiler> compiler = shared_ptr<HtnCompiler>(new HtnCompiler(factory.get(), state.get(), planner.get()));

        compiler->ClearWithNewRuleSet();

        // opGain has a single increase() effect; opLose has a single decrease() effect.
        // Neither has add() or del() effects.
        string program =
            "opGain(?n) :- increase(score(player), ?n). "
            "opLose(?n) :- decrease(score(player), ?n). ";

        CHECK(compiler->Compile(program));

        HtnOperator *opGain = FindOperatorByNameArity(planner.get(), "opGain", 1);
        CHECK(opGain != nullptr);
        if (opGain != nullptr)
        {
            CHECK_EQUAL(1, (int)opGain->increases().size());
            CHECK_EQUAL(0, (int)opGain->decreases().size());
            CHECK_EQUAL(0, (int)opGain->additions().size());
            CHECK_EQUAL(0, (int)opGain->deletions().size());
        }

        HtnOperator *opLose = FindOperatorByNameArity(planner.get(), "opLose", 1);
        CHECK(opLose != nullptr);
        if (opLose != nullptr)
        {
            CHECK_EQUAL(0, (int)opLose->increases().size());
            CHECK_EQUAL(1, (int)opLose->decreases().size());
            CHECK_EQUAL(0, (int)opLose->additions().size());
            CHECK_EQUAL(0, (int)opLose->deletions().size());
        }
    }
}
