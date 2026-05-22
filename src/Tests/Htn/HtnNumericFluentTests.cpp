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
#include "FXPlatform/NanoTrace.h"  // pulls in `using namespace std` used throughout the project
#include "FXPlatform/Prolog/HtnRuleSet.h"
#include "FXPlatform/Prolog/HtnTerm.h"
#include "FXPlatform/Prolog/HtnTermFactory.h"
#include "FXPlatform/Htn/HtnOperator.h"
#include "FXPlatform/Htn/HtnPlanner.h"
#include "FXPlatform/Htn/HtnCompiler.h"
#include "UnitTest++/UnitTest++.h"

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

    // Convenience: does any term in the vector match the given functor/arity
    // and have a specific first-argument name (matched by ToString comparison)?
    static bool ContainsTermWithName(const std::vector<std::shared_ptr<HtnTerm>> &terms, const std::string &name)
    {
        for (auto t : terms)
        {
            if (t->name() == name)
            {
                return true;
            }
        }
        return false;
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

            // M2: verify the stored term is the whole increase(...) clause with arity 2
            // (one entry per clause, holding both target and delta).
            CHECK_EQUAL("increase", opGain->increases()[0]->name());
            CHECK_EQUAL(2, opGain->increases()[0]->arity());
        }

        HtnOperator *opLose = FindOperatorByNameArity(planner.get(), "opLose", 1);
        CHECK(opLose != nullptr);
        if (opLose != nullptr)
        {
            CHECK_EQUAL(0, (int)opLose->increases().size());
            CHECK_EQUAL(1, (int)opLose->decreases().size());
            CHECK_EQUAL(0, (int)opLose->additions().size());
            CHECK_EQUAL(0, (int)opLose->deletions().size());

            CHECK_EQUAL("decrease", opLose->decreases()[0]->name());
            CHECK_EQUAL(2, opLose->decreases()[0]->arity());
        }
    }

    // M1: an operator can mix increase() and decrease() in the same body, no
    // del/add required. Each kind ends up in its own bucket.
    TEST(MultiEffectOperator_DecreaseAndIncrease)
    {
        shared_ptr<HtnTermFactory> factory = shared_ptr<HtnTermFactory>(new HtnTermFactory());
        shared_ptr<HtnRuleSet> state = shared_ptr<HtnRuleSet>(new HtnRuleSet());
        shared_ptr<HtnPlanner> planner = shared_ptr<HtnPlanner>(new HtnPlanner());
        shared_ptr<HtnCompiler> compiler = shared_ptr<HtnCompiler>(new HtnCompiler(factory.get(), state.get(), planner.get()));

        compiler->ClearWithNewRuleSet();

        string program =
            "opSwap(?a, ?b) :- decrease(mana(?a), 10), increase(mana(?b), 10). ";

        CHECK(compiler->Compile(program));

        HtnOperator *opSwap = FindOperatorByNameArity(planner.get(), "opSwap", 2);
        CHECK(opSwap != nullptr);
        if (opSwap != nullptr)
        {
            CHECK_EQUAL(1, (int)opSwap->increases().size());
            CHECK_EQUAL(1, (int)opSwap->decreases().size());
            CHECK_EQUAL(0, (int)opSwap->additions().size());
            CHECK_EQUAL(0, (int)opSwap->deletions().size());
        }
    }

    // Two of the same kind: both clauses are preserved in declaration order.
    TEST(MultipleIncreaseClauses_BothStored)
    {
        shared_ptr<HtnTermFactory> factory = shared_ptr<HtnTermFactory>(new HtnTermFactory());
        shared_ptr<HtnRuleSet> state = shared_ptr<HtnRuleSet>(new HtnRuleSet());
        shared_ptr<HtnPlanner> planner = shared_ptr<HtnPlanner>(new HtnPlanner());
        shared_ptr<HtnCompiler> compiler = shared_ptr<HtnCompiler>(new HtnCompiler(factory.get(), state.get(), planner.get()));

        compiler->ClearWithNewRuleSet();

        string program =
            "opDouble() :- increase(a, 1), increase(b, 1). ";

        CHECK(compiler->Compile(program));

        HtnOperator *opDouble = FindOperatorByNameArity(planner.get(), "opDouble", 0);
        CHECK(opDouble != nullptr);
        if (opDouble != nullptr)
        {
            CHECK_EQUAL(2, (int)opDouble->increases().size());
            CHECK_EQUAL(0, (int)opDouble->decreases().size());
            // First-arg names are "a" then "b" in declaration order.
            CHECK_EQUAL("a", opDouble->increases()[0]->arguments()[0]->name());
            CHECK_EQUAL("b", opDouble->increases()[1]->arguments()[0]->name());
        }
    }

    // C1 regression: del() must not be silently dropped when add() is absent.
    // Previously the parse loop only registered the operator inside the add()
    // branch (or in the increase/decrease tail), so `del + increase + no add`
    // lost the del entirely.
    TEST(DelPlusIncrease_NoAdd_KeepsDel)
    {
        shared_ptr<HtnTermFactory> factory = shared_ptr<HtnTermFactory>(new HtnTermFactory());
        shared_ptr<HtnRuleSet> state = shared_ptr<HtnRuleSet>(new HtnRuleSet());
        shared_ptr<HtnPlanner> planner = shared_ptr<HtnPlanner>(new HtnPlanner());
        shared_ptr<HtnCompiler> compiler = shared_ptr<HtnCompiler>(new HtnCompiler(factory.get(), state.get(), planner.get()));

        compiler->ClearWithNewRuleSet();

        string program =
            "opDelInc() :- del(foo), increase(score(player), 5). ";

        CHECK(compiler->Compile(program));

        HtnOperator *opDelInc = FindOperatorByNameArity(planner.get(), "opDelInc", 0);
        CHECK(opDelInc != nullptr);
        if (opDelInc != nullptr)
        {
            CHECK_EQUAL(1, (int)opDelInc->deletions().size());
            CHECK_EQUAL(0, (int)opDelInc->additions().size());
            CHECK_EQUAL(1, (int)opDelInc->increases().size());
            CHECK(ContainsTermWithName(opDelInc->deletions(), "foo"));
            CHECK_EQUAL("increase", opDelInc->increases()[0]->name());
        }
    }

    // C2 regression: decrease() followed by add() (no preceding del) used to
    // trip the `del != nullptr` assertion in the add() branch. It must now
    // compile cleanly and preserve both effects.
    TEST(DecreasePlusAdd_NoDel_Compiles)
    {
        shared_ptr<HtnTermFactory> factory = shared_ptr<HtnTermFactory>(new HtnTermFactory());
        shared_ptr<HtnRuleSet> state = shared_ptr<HtnRuleSet>(new HtnRuleSet());
        shared_ptr<HtnPlanner> planner = shared_ptr<HtnPlanner>(new HtnPlanner());
        shared_ptr<HtnCompiler> compiler = shared_ptr<HtnCompiler>(new HtnCompiler(factory.get(), state.get(), planner.get()));

        compiler->ClearWithNewRuleSet();

        // The plan's headline example: spend mana, set "spent" flag, no del.
        string program =
            "opSpendMana(?cost) :- decrease(mana(player), ?cost), add(spent(true)). ";

        CHECK(compiler->Compile(program));

        HtnOperator *opSpendMana = FindOperatorByNameArity(planner.get(), "opSpendMana", 1);
        CHECK(opSpendMana != nullptr);
        if (opSpendMana != nullptr)
        {
            CHECK_EQUAL(0, (int)opSpendMana->deletions().size());
            CHECK_EQUAL(1, (int)opSpendMana->additions().size());
            CHECK_EQUAL(0, (int)opSpendMana->increases().size());
            CHECK_EQUAL(1, (int)opSpendMana->decreases().size());
            CHECK(ContainsTermWithName(opSpendMana->additions(), "spent"));
        }
    }

    // I4 regression: increase() listed AFTER add() used to be silently dropped
    // because the add() branch returned early from the parse loop. All three
    // clauses must now be preserved.
    TEST(DelAddIncrease_TrailingIncreasePreserved)
    {
        shared_ptr<HtnTermFactory> factory = shared_ptr<HtnTermFactory>(new HtnTermFactory());
        shared_ptr<HtnRuleSet> state = shared_ptr<HtnRuleSet>(new HtnRuleSet());
        shared_ptr<HtnPlanner> planner = shared_ptr<HtnPlanner>(new HtnPlanner());
        shared_ptr<HtnCompiler> compiler = shared_ptr<HtnCompiler>(new HtnCompiler(factory.get(), state.get(), planner.get()));

        compiler->ClearWithNewRuleSet();

        string program =
            "opTrail() :- del(a), add(b), increase(c, 1). ";

        CHECK(compiler->Compile(program));

        HtnOperator *opTrail = FindOperatorByNameArity(planner.get(), "opTrail", 0);
        CHECK(opTrail != nullptr);
        if (opTrail != nullptr)
        {
            CHECK_EQUAL(1, (int)opTrail->deletions().size());
            CHECK_EQUAL(1, (int)opTrail->additions().size());
            CHECK_EQUAL(1, (int)opTrail->increases().size());
            CHECK(ContainsTermWithName(opTrail->deletions(), "a"));
            CHECK(ContainsTermWithName(opTrail->additions(), "b"));
            CHECK_EQUAL("c", opTrail->increases()[0]->arguments()[0]->name());
        }
    }

    // I3 regression: increase()/decrease() must have exactly arity 2.
    // The compiler enforces this via FailFastAssertDesc; we route the assert
    // through an exception (TreatFailFastAsException) so the test runner
    // can observe the failure rather than the process aborting.
    TEST(IncreaseWithWrongArity_FailsToCompile_Arity1)
    {
        TreatFailFastAsException(true);
        shared_ptr<HtnTermFactory> factory = shared_ptr<HtnTermFactory>(new HtnTermFactory());
        shared_ptr<HtnRuleSet> state = shared_ptr<HtnRuleSet>(new HtnRuleSet());
        shared_ptr<HtnPlanner> planner = shared_ptr<HtnPlanner>(new HtnPlanner());
        shared_ptr<HtnCompiler> compiler = shared_ptr<HtnCompiler>(new HtnCompiler(factory.get(), state.get(), planner.get()));
        compiler->ClearWithNewRuleSet();

        // arity 1 -- missing delta expression
        string program = "opBadArity() :- increase(only_one_arg). ";

        bool threw = false;
        try
        {
            compiler->Compile(program);
        }
        catch (const std::runtime_error &)
        {
            threw = true;
        }
        CHECK(threw);
        TreatFailFastAsException(false);
    }

    TEST(DecreaseWithWrongArity_FailsToCompile_Arity3)
    {
        TreatFailFastAsException(true);
        shared_ptr<HtnTermFactory> factory = shared_ptr<HtnTermFactory>(new HtnTermFactory());
        shared_ptr<HtnRuleSet> state = shared_ptr<HtnRuleSet>(new HtnRuleSet());
        shared_ptr<HtnPlanner> planner = shared_ptr<HtnPlanner>(new HtnPlanner());
        shared_ptr<HtnCompiler> compiler = shared_ptr<HtnCompiler>(new HtnCompiler(factory.get(), state.get(), planner.get()));
        compiler->ClearWithNewRuleSet();

        // arity 3 -- one too many arguments
        string program = "opBadArity() :- decrease(a, b, c). ";

        bool threw = false;
        try
        {
            compiler->Compile(program);
        }
        catch (const std::runtime_error &)
        {
            threw = true;
        }
        CHECK(threw);
        TreatFailFastAsException(false);
    }
}
