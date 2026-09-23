//
//  HtnChoiceTrackingTests.cpp
//  TestLib
//
//  Tests for INDHTN_CHOICE_TRACKING instrumentation:
//  verifies that FindAllPlans records which methods unified with each
//  compound task and which of those had satisfiable preconditions.
//

#ifdef INDHTN_CHOICE_TRACKING

#include "FXPlatform/FailFast.h"
#include "FXPlatform/NanoTrace.h"
#include "FXPlatform/Prolog/HtnGoalResolver.h"
#include "FXPlatform/Prolog/HtnRuleSet.h"
#include "FXPlatform/Prolog/HtnTerm.h"
#include "FXPlatform/Prolog/HtnTermFactory.h"
#include "FXPlatform/Htn/HtnPlanner.h"
#include "FXPlatform/Htn/HtnCompiler.h"
#include "UnitTest++/UnitTest++.h"

SUITE(HtnChoiceTrackingTests)
{
    TEST(TwoMethodsOneViable_RecordsCorrectly)
    {
        // Set up standard planner infrastructure
        shared_ptr<HtnTermFactory> factory = shared_ptr<HtnTermFactory>(new HtnTermFactory());
        shared_ptr<HtnRuleSet> state = shared_ptr<HtnRuleSet>(new HtnRuleSet());
        shared_ptr<HtnPlanner> planner = shared_ptr<HtnPlanner>(new HtnPlanner());
        shared_ptr<HtnCompiler> compiler = shared_ptr<HtnCompiler>(new HtnCompiler(factory.get(), state.get(), planner.get()));

        compiler->ClearWithNewRuleSet();

        // Two methods for "doTask":
        //   method 1: requires precondition "ready" — satisfiable (fact exists)
        //   method 2: requires precondition "notReady" — NOT satisfiable (fact absent)
        // opDo is the leaf operator.
        string program =
            "ready. "
            "doTask() :- if(ready), do(opDo()). "
            "doTask() :- if(notReady), do(opDo()). "
            "opDo() :- del(), add(). "
            "goals(doTask()). ";

        CHECK(compiler->Compile(program));

        std::vector<ChoiceRecord> choiceData;
        auto solutions = planner->FindAllPlans(
            factory.get(),
            compiler->compilerOwnedRuleSet(),
            compiler->goals(),
            5000000);
        choiceData = planner->GetLastChoiceData();

        // Planning should succeed (method 1 is viable)
        CHECK(solutions != nullptr);
        CHECK(solutions->size() > 0);

        // There should be exactly one ChoiceRecord for the doTask() node
        CHECK_EQUAL(1, (int)choiceData.size());

        if(choiceData.size() >= 1)
        {
            const ChoiceRecord &rec = choiceData[0];

            // Task functor should be "doTask"
            CHECK_EQUAL("doTask", rec.taskFunctor);

            // Full task string for a zero-arity task is "doTask" (HtnTerm::ToString
            // omits empty parens).
            CHECK_EQUAL("doTask", rec.taskFull);

            // Both methods unified with the task (head unification)
            CHECK_EQUAL(2, (int)rec.unifyingMethods.size());

            // Only one method had satisfiable preconditions (method 1: if(ready))
            CHECK_EQUAL(1, (int)rec.viableMethods.size());
        }
    }

    TEST(AllMethodsViable_RecordsBothAsViable)
    {
        shared_ptr<HtnTermFactory> factory = shared_ptr<HtnTermFactory>(new HtnTermFactory());
        shared_ptr<HtnRuleSet> state = shared_ptr<HtnRuleSet>(new HtnRuleSet());
        shared_ptr<HtnPlanner> planner = shared_ptr<HtnPlanner>(new HtnPlanner());
        shared_ptr<HtnCompiler> compiler = shared_ptr<HtnCompiler>(new HtnCompiler(factory.get(), state.get(), planner.get()));

        compiler->ClearWithNewRuleSet();

        // Two methods both with empty (always-true) conditions — both should be viable
        string program =
            "doTask() :- if(), do(opA()). "
            "doTask() :- if(), do(opB()). "
            "opA() :- del(), add(done(a)). "
            "opB() :- del(), add(done(b)). "
            "goals(doTask()). ";

        CHECK(compiler->Compile(program));

        std::vector<ChoiceRecord> choiceData;
        auto solutions = planner->FindAllPlans(
            factory.get(),
            compiler->compilerOwnedRuleSet(),
            compiler->goals(),
            5000000);
        choiceData = planner->GetLastChoiceData();

        // Both methods succeed, so we get 2 solutions
        CHECK(solutions != nullptr);

        CHECK_EQUAL(1, (int)choiceData.size());

        if(choiceData.size() >= 1)
        {
            const ChoiceRecord &rec = choiceData[0];
            CHECK_EQUAL("doTask", rec.taskFunctor);
            CHECK_EQUAL(2, (int)rec.unifyingMethods.size());
            CHECK_EQUAL(2, (int)rec.viableMethods.size());
        }
    }

    TEST(NoMethodViable_EmptyViableMethods)
    {
        shared_ptr<HtnTermFactory> factory = shared_ptr<HtnTermFactory>(new HtnTermFactory());
        shared_ptr<HtnRuleSet> state = shared_ptr<HtnRuleSet>(new HtnRuleSet());
        shared_ptr<HtnPlanner> planner = shared_ptr<HtnPlanner>(new HtnPlanner());
        shared_ptr<HtnCompiler> compiler = shared_ptr<HtnCompiler>(new HtnCompiler(factory.get(), state.get(), planner.get()));

        compiler->ClearWithNewRuleSet();

        // Two methods, neither has a satisfiable precondition
        string program =
            "doTask() :- if(missingA), do(opA()). "
            "doTask() :- if(missingB), do(opB()). "
            "opA() :- del(), add(). "
            "opB() :- del(), add(). "
            "goals(doTask()). ";

        CHECK(compiler->Compile(program));

        std::vector<ChoiceRecord> choiceData;
        auto solutions = planner->FindAllPlans(
            factory.get(),
            compiler->compilerOwnedRuleSet(),
            compiler->goals(),
            5000000);
        choiceData = planner->GetLastChoiceData();

        // Planning should fail — no viable methods
        CHECK(solutions == nullptr);

        // We still get one ChoiceRecord (unification succeeded, viability checks happened)
        CHECK_EQUAL(1, (int)choiceData.size());

        if(choiceData.size() >= 1)
        {
            const ChoiceRecord &rec = choiceData[0];
            CHECK_EQUAL("doTask", rec.taskFunctor);
            CHECK_EQUAL(2, (int)rec.unifyingMethods.size());
            // No viable methods since both preconditions fail
            CHECK_EQUAL(0, (int)rec.viableMethods.size());
        }
    }

    // ----- Cross-search choice-count tracking (MethodClauseStats / AtomStats) -----

    static const MethodClauseStats* findClause(const std::vector<MethodClauseStats>& v, const std::string& functorPrefix)
    {
        for(const auto& c : v) { if(c.clauseSignature.rfind(functorPrefix, 0) == 0) { return &c; } }
        return nullptr;
    }
    static const MethodPositionStats* findPos(const MethodClauseStats& c, int slot)
    {
        for(const auto& p : c.positions) { if(p.positionIndex == slot) { return &p; } }
        return nullptr;
    }
    static const AtomStats* findAtom(const std::vector<AtomStats>& v, const std::string& functor)
    {
        for(const auto& a : v) { if(a.atomFunctor == functor) { return &a; } }
        return nullptr;
    }
    static int clearCountContaining(const std::vector<AtomMethodClear>& clears, const std::string& sigSubstr)
    {
        for(const auto& c : clears) { if(c.methodSignature.find(sigSubstr) != std::string::npos) { return c.clearCount; } }
        return 0;
    }

    // The headline example from the design: head() with two sequential subtasks,
    // verifying the grounding partition S + posFails = N and per-position tested counts.
    TEST(TwoSubtaskPartition)
    {
        shared_ptr<HtnTermFactory> factory = shared_ptr<HtnTermFactory>(new HtnTermFactory());
        shared_ptr<HtnRuleSet> state = shared_ptr<HtnRuleSet>(new HtnRuleSet());
        shared_ptr<HtnPlanner> planner = shared_ptr<HtnPlanner>(new HtnPlanner());
        shared_ptr<HtnCompiler> compiler = shared_ptr<HtnCompiler>(new HtnCompiler(factory.get(), state.get(), planner.get()));
        compiler->ClearWithNewRuleSet();

        // 9 groundings of (?x,?y) over {a,b,c}^2. func1 succeeds for x in {a,b},
        // func2 for y in {a,b}. So: 4 succeed, 3 fail at func1 (x==c),
        // 2 fail at func2 (x in {a,b}, y==c). func1 tested every grounding (9),
        // func2 only when func1 succeeded (x in {a,b} => 6).
        string program =
            "loc(a). loc(b). loc(c). "
            "path(a, c). path(b, c). "
            "head() :- if(loc(?x), loc(?y)), do(func1(?x), func2(?y)). "
            "func1(?x) :- if(path(?x, c)), do(op1(?x)). "
            "func2(?y) :- if(path(?y, c)), do(op2(?y)). "
            "op1(?x) :- del(), add(). "
            "op2(?y) :- del(), add(). "
            "goals(head()). ";
        CHECK(compiler->Compile(program));

        std::vector<ChoiceRecord> choiceData;
        std::vector<MethodClauseStats> methodStats;
        std::vector<AtomStats> atomStats;
        auto solutions = planner->FindAllPlans(
            factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals(),
            5000000);
        choiceData = planner->GetLastChoiceData();
        methodStats = planner->GetLastMethodStats();
        atomStats = planner->GetLastAtomStats();

        CHECK(solutions != nullptr);
        CHECK_EQUAL(4, (int)solutions->size());

        const MethodClauseStats* head = findClause(methodStats, "head");
        CHECK(head != nullptr);
        if(head)
        {
            CHECK_EQUAL("normal", head->methodType);
            CHECK_EQUAL(9, head->groundingsN);
            CHECK_EQUAL(4, head->successS);

            const MethodPositionStats* p0 = findPos(*head, 0);
            const MethodPositionStats* p1 = findPos(*head, 1);
            CHECK(p0 != nullptr);
            CHECK(p1 != nullptr);
            if(p0)
            {
                CHECK_EQUAL("func1", p0->atomFunctor);
                CHECK_EQUAL(9, p0->testedCount);
                CHECK_EQUAL(3, p0->failCount);
            }
            if(p1)
            {
                CHECK_EQUAL("func2", p1->atomFunctor);
                CHECK_EQUAL(6, p1->testedCount);
                CHECK_EQUAL(2, p1->failCount);
            }
            // The partition invariant: S + sum(positionFails) == N
            int sumFail = (p0 ? p0->failCount : 0) + (p1 ? p1->failCount : 0);
            CHECK_EQUAL(head->groundingsN, head->successS + sumFail);

            // Explicit furthest-completed histogram: [fail@func1, fail@func2, success].
            CHECK_EQUAL(2, head->subtaskCount);
            CHECK_EQUAL(3, (int)head->furthestCompleted.size());
            if(head->furthestCompleted.size() == 3)
            {
                CHECK_EQUAL(3, head->furthestCompleted[0]);
                CHECK_EQUAL(2, head->furthestCompleted[1]);
                CHECK_EQUAL(4, head->furthestCompleted[2]);
            }
            int sumHist = 0;
            for(int v : head->furthestCompleted) { sumHist += v; }
            CHECK_EQUAL(head->groundingsN, sumHist);
        }

        // The fix: func1's OWN body (op1) always completes locally, so it must
        // NEVER be recorded as a local failure — the downstream func2 failures are
        // NOT blamed on func1. (My previous continuation-based logic wrongly showed
        // func1 fail=2 here.)
        const MethodClauseStats* func1 = findClause(methodStats, "func1");
        CHECK(func1 != nullptr);
        if(func1)
        {
            CHECK_EQUAL(6, func1->groundingsN);
            CHECK_EQUAL(6, func1->successS);          // all groundings complete locally
            CHECK_EQUAL(1, func1->subtaskCount);
            CHECK_EQUAL(2, (int)func1->furthestCompleted.size());
            if(func1->furthestCompleted.size() == 2)
            {
                CHECK_EQUAL(0, func1->furthestCompleted[0]);  // no local failures
                CHECK_EQUAL(6, func1->furthestCompleted[1]);  // all 6 complete
            }
        }

        // by-atom rollup mirrors the per-position tested counts here.
        const AtomStats* a1 = findAtom(atomStats, "func1");
        const AtomStats* a2 = findAtom(atomStats, "func2");
        CHECK(a1 != nullptr);
        CHECK(a2 != nullptr);
        if(a1) { CHECK_EQUAL(9, a1->testedCount); }
        if(a2) { CHECK_EQUAL(6, a2->testedCount); }

        // op1 always completes, so it is never the local blocker.
        const AtomStats* op1 = findAtom(atomStats, "op1");
        CHECK(op1 != nullptr);
        if(op1) { CHECK_EQUAL(0, op1->failCount); }
    }

    // Overloaded atom: travelTo resolved by a "walk" method and a "taxi" method.
    // Demonstrates per-resolving-method clear counts that overlap (sum > tested).
    TEST(OverloadClears)
    {
        shared_ptr<HtnTermFactory> factory = shared_ptr<HtnTermFactory>(new HtnTermFactory());
        shared_ptr<HtnRuleSet> state = shared_ptr<HtnRuleSet>(new HtnRuleSet());
        shared_ptr<HtnPlanner> planner = shared_ptr<HtnPlanner>(new HtnPlanner());
        shared_ptr<HtnCompiler> compiler = shared_ptr<HtnCompiler>(new HtnCompiler(factory.get(), state.get(), planner.get()));
        compiler->ClearWithNewRuleSet();

        // 9 destinations. canWalk: {p1,p2,p3} (3). canTaxi: {p1,p4..p9} (7).
        // p1 overlaps. travelTo tested 9; walk clears 3 + taxi clears 7 = 10 > 9.
        string program =
            "dest(p1). dest(p2). dest(p3). dest(p4). dest(p5). dest(p6). dest(p7). dest(p8). dest(p9). "
            "canWalk(p1). canWalk(p2). canWalk(p3). "
            "canTaxi(p1). canTaxi(p4). canTaxi(p5). canTaxi(p6). canTaxi(p7). canTaxi(p8). canTaxi(p9). "
            "trip() :- if(dest(?d)), do(travelTo(?d)). "
            "travelTo(?d) :- if(canWalk(?d)), do(opWalk(?d)). "
            "travelTo(?d) :- if(canTaxi(?d)), do(opTaxi(?d)). "
            "opWalk(?d) :- del(), add(). "
            "opTaxi(?d) :- del(), add(). "
            "goals(trip()). ";
        CHECK(compiler->Compile(program));

        std::vector<ChoiceRecord> choiceData;
        std::vector<MethodClauseStats> methodStats;
        std::vector<AtomStats> atomStats;
        auto solutions = planner->FindAllPlans(
            factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals(),
            5000000);
        choiceData = planner->GetLastChoiceData();
        methodStats = planner->GetLastMethodStats();
        atomStats = planner->GetLastAtomStats();
        CHECK(solutions != nullptr);

        const AtomStats* travelTo = findAtom(atomStats, "travelTo");
        CHECK(travelTo != nullptr);
        if(travelTo)
        {
            CHECK_EQUAL(false, travelTo->isOperator);
            CHECK_EQUAL(9, travelTo->testedCount);
            int walk = clearCountContaining(travelTo->clears, "canWalk");
            int taxi = clearCountContaining(travelTo->clears, "canTaxi");
            CHECK_EQUAL(3, walk);
            CHECK_EQUAL(7, taxi);
            // Overlap: per-method clears sum to more than the atom's tested count.
            CHECK(walk + taxi > travelTo->testedCount);
        }
    }

    // Precondition gate failure (N == 0 groundings).
    TEST(GateFailure)
    {
        shared_ptr<HtnTermFactory> factory = shared_ptr<HtnTermFactory>(new HtnTermFactory());
        shared_ptr<HtnRuleSet> state = shared_ptr<HtnRuleSet>(new HtnRuleSet());
        shared_ptr<HtnPlanner> planner = shared_ptr<HtnPlanner>(new HtnPlanner());
        shared_ptr<HtnCompiler> compiler = shared_ptr<HtnCompiler>(new HtnCompiler(factory.get(), state.get(), planner.get()));
        compiler->ClearWithNewRuleSet();

        string program =
            "gateMethod() :- if(missing), do(opX()). "
            "opX() :- del(), add(). "
            "goals(gateMethod()). ";
        CHECK(compiler->Compile(program));

        std::vector<ChoiceRecord> choiceData;
        std::vector<MethodClauseStats> methodStats;
        std::vector<AtomStats> atomStats;
        auto solutions = planner->FindAllPlans(
            factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals(),
            5000000);
        choiceData = planner->GetLastChoiceData();
        methodStats = planner->GetLastMethodStats();
        atomStats = planner->GetLastAtomStats();
        CHECK(solutions == nullptr);

        const MethodClauseStats* gate = findClause(methodStats, "gateMethod");
        CHECK(gate != nullptr);
        if(gate)
        {
            CHECK_EQUAL(0, gate->groundingsN);
            CHECK_EQUAL(0, gate->successS);
            CHECK_EQUAL(1, gate->gateFailCount);
        }
    }

    // Leaf operators are counted as atoms (tested, isOperator=true, no clears).
    TEST(OperatorTested)
    {
        shared_ptr<HtnTermFactory> factory = shared_ptr<HtnTermFactory>(new HtnTermFactory());
        shared_ptr<HtnRuleSet> state = shared_ptr<HtnRuleSet>(new HtnRuleSet());
        shared_ptr<HtnPlanner> planner = shared_ptr<HtnPlanner>(new HtnPlanner());
        shared_ptr<HtnCompiler> compiler = shared_ptr<HtnCompiler>(new HtnCompiler(factory.get(), state.get(), planner.get()));
        compiler->ClearWithNewRuleSet();

        string program =
            "doIt() :- if(), do(opLeaf()). "
            "opLeaf() :- del(), add(marker()). "
            "goals(doIt()). ";
        CHECK(compiler->Compile(program));

        std::vector<ChoiceRecord> choiceData;
        std::vector<MethodClauseStats> methodStats;
        std::vector<AtomStats> atomStats;
        auto solutions = planner->FindAllPlans(
            factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals(),
            5000000);
        choiceData = planner->GetLastChoiceData();
        methodStats = planner->GetLastMethodStats();
        atomStats = planner->GetLastAtomStats();
        CHECK(solutions != nullptr);

        const AtomStats* opLeaf = findAtom(atomStats, "opLeaf");
        CHECK(opLeaf != nullptr);
        if(opLeaf)
        {
            CHECK_EQUAL(true, opLeaf->isOperator);
            CHECK_EQUAL(1, opLeaf->testedCount);
            CHECK_EQUAL(0, (int)opLeaf->clears.size());
        }
        const AtomStats* doIt = findAtom(atomStats, "doIt");
        CHECK(doIt != nullptr);
        if(doIt) { CHECK_EQUAL(false, doIt->isOperator); }
    }

    // ===== Systematic furthest-completed histogram suite =====================
    // head() with three trivial subtasks s1,s2,s3 (each a single-gate, single-op
    // method). A subtask "fails" when its gate fact gN is absent. We vary:
    //   - the head precondition's unification count (1 vs 3), and
    //   - which subtask blocks (fail@1/2/3, or no-fail = full success).
    // The head furthest-completed histogram has size N+1 == 4:
    //   index 0 = failed at s1, 1 = failed at s2, 2 = failed at s3, 3 = full success.

    struct CaseStats {
        std::vector<MethodClauseStats> methods;
        std::vector<AtomStats> atoms;
        bool solvable;
        int solutionCount;
    };

    static CaseStats runHeadCase(const std::string& startFacts, const std::string& headCond,
                                 bool g1, bool g2, bool g3)
    {
        shared_ptr<HtnTermFactory> factory(new HtnTermFactory());
        shared_ptr<HtnRuleSet> state(new HtnRuleSet());
        shared_ptr<HtnPlanner> planner(new HtnPlanner());
        shared_ptr<HtnCompiler> compiler(new HtnCompiler(factory.get(), state.get(), planner.get()));
        compiler->ClearWithNewRuleSet();

        std::string p = startFacts + " ";
        if(g1) { p += "g1. "; }
        if(g2) { p += "g2. "; }
        if(g3) { p += "g3. "; }
        p += "head() :- if(" + headCond + "), do(s1(), s2(), s3()). ";
        p += "s1() :- if(g1), do(op1()). ";
        p += "s2() :- if(g2), do(op2()). ";
        p += "s3() :- if(g3), do(op3()). ";
        p += "op1() :- del(), add(). ";
        p += "op2() :- del(), add(). ";
        p += "op3() :- del(), add(). ";
        p += "goals(head()). ";
        CHECK(compiler->Compile(p));

        CaseStats cs;
        auto sols = planner->FindAllPlans(factory.get(), compiler->compilerOwnedRuleSet(),
                                          compiler->goals(), 5000000);
        cs.methods = planner->GetLastMethodStats();
        cs.atoms = planner->GetLastAtomStats();
        cs.solvable = (sols != nullptr);
        cs.solutionCount = sols ? (int)sols->size() : 0;
        return cs;
    }

    static void checkHist(const std::vector<int>& got, const std::vector<int>& want)
    {
        CHECK_EQUAL((int)want.size(), (int)got.size());
        if(got.size() == want.size())
        {
            for(size_t i = 0; i < want.size(); i++) { CHECK_EQUAL(want[i], got[i]); }
        }
    }

    static void checkHeadHist(const CaseStats& cs, const std::vector<int>& want)
    {
        const MethodClauseStats* h = findClause(cs.methods, "head");
        CHECK(h != nullptr);
        if(h)
        {
            CHECK_EQUAL(3, h->subtaskCount);
            checkHist(h->furthestCompleted, want);
            int sum = 0;
            for(int v : h->furthestCompleted) { sum += v; }
            CHECK_EQUAL(h->groundingsN, sum);     // histogram sums to groundings
            CHECK_EQUAL(want.back(), h->successS); // last bucket == successS
        }
    }

    // ---- Single unification of the head precondition (start.) ----

    TEST(Hist_1Unif_NoFail)
    {
        CaseStats cs = runHeadCase("start.", "start", true, true, true);
        checkHeadHist(cs, {0, 0, 0, 1});
        CHECK(cs.solvable);
        CHECK_EQUAL(1, cs.solutionCount);
    }
    TEST(Hist_1Unif_FailAt1)
    {
        CaseStats cs = runHeadCase("start.", "start", false, true, true);
        checkHeadHist(cs, {1, 0, 0, 0});
        CHECK(!cs.solvable);
        CHECK_EQUAL(0, cs.solutionCount);
    }
    TEST(Hist_1Unif_FailAt2)
    {
        CaseStats cs = runHeadCase("start.", "start", true, false, true);
        checkHeadHist(cs, {0, 1, 0, 0});
        CHECK(!cs.solvable);
    }
    TEST(Hist_1Unif_FailAt3)
    {
        CaseStats cs = runHeadCase("start.", "start", true, true, false);
        checkHeadHist(cs, {0, 0, 1, 0});
        CHECK(!cs.solvable);
    }

    // ---- Three unifications of the head precondition (start(a/b/c)) ----

    TEST(Hist_3Unif_NoFail)
    {
        CaseStats cs = runHeadCase("start(a). start(b). start(c).", "start(?s)", true, true, true);
        checkHeadHist(cs, {0, 0, 0, 3});
        CHECK(cs.solvable);
        CHECK_EQUAL(3, cs.solutionCount);
    }
    TEST(Hist_3Unif_FailAt1)
    {
        CaseStats cs = runHeadCase("start(a). start(b). start(c).", "start(?s)", false, true, true);
        checkHeadHist(cs, {3, 0, 0, 0});
        CHECK(!cs.solvable);
    }
    TEST(Hist_3Unif_FailAt2)
    {
        CaseStats cs = runHeadCase("start(a). start(b). start(c).", "start(?s)", true, false, true);
        checkHeadHist(cs, {0, 3, 0, 0});
        CHECK(!cs.solvable);
    }
    TEST(Hist_3Unif_FailAt3)
    {
        CaseStats cs = runHeadCase("start(a). start(b). start(c).", "start(?s)", true, true, false);
        checkHeadHist(cs, {0, 0, 3, 0});
        CHECK(!cs.solvable);
    }

    // ---- Subtask-level local semantics: subtasks BEFORE the blocker complete
    //      locally; the blocker gate-fails; subtasks AFTER are never reached. ----

    TEST(LocalSemantics_FailAt2_SubtaskBreakdown)
    {
        CaseStats cs = runHeadCase("start.", "start", true, false, true);  // s2 blocks

        // s1 (before the blocker): full LOCAL success even though head fails downstream.
        const MethodClauseStats* s1 = findClause(cs.methods, "s1");
        CHECK(s1 != nullptr);
        if(s1)
        {
            CHECK_EQUAL(1, s1->groundingsN);
            CHECK_EQUAL(1, s1->successS);
            checkHist(s1->furthestCompleted, {0, 1});
            CHECK_EQUAL(0, s1->gateFailCount);
        }

        // s2 (the blocker): its own gate failed; no grounding ran.
        const MethodClauseStats* s2 = findClause(cs.methods, "s2");
        CHECK(s2 != nullptr);
        if(s2)
        {
            CHECK_EQUAL(0, s2->groundingsN);
            CHECK_EQUAL(1, s2->gateFailCount);
            CHECK_EQUAL(0, (int)s2->furthestCompleted.size());
        }

        // s3 (after the blocker): never reached, so no clause and no atom.
        CHECK(findClause(cs.methods, "s3") == nullptr);
        CHECK(findAtom(cs.atoms, "s3") == nullptr);
        CHECK(findAtom(cs.atoms, "op2") == nullptr);  // op2 never reached either

        // by-atom: s2 was tested (reached) once and is the local blocker.
        const AtomStats* s2atom = findAtom(cs.atoms, "s2");
        CHECK(s2atom != nullptr);
        if(s2atom) { CHECK_EQUAL(1, s2atom->testedCount); }
        const AtomStats* op1atom = findAtom(cs.atoms, "op1");
        CHECK(op1atom != nullptr);
        if(op1atom) { CHECK_EQUAL(0, op1atom->failCount); }  // op1 always completes
    }

    TEST(LocalSemantics_FailAt1_BlockerGateFails)
    {
        CaseStats cs = runHeadCase("start.", "start", false, true, true);  // s1 blocks

        const MethodClauseStats* s1 = findClause(cs.methods, "s1");
        CHECK(s1 != nullptr);
        if(s1)
        {
            CHECK_EQUAL(0, s1->groundingsN);
            CHECK_EQUAL(1, s1->gateFailCount);
        }
        // s2/s3 never reached.
        CHECK(findClause(cs.methods, "s2") == nullptr);
        CHECK(findClause(cs.methods, "s3") == nullptr);
    }

    TEST(LocalSemantics_FailAt3_FirstTwoComplete)
    {
        CaseStats cs = runHeadCase("start.", "start", true, true, false);  // s3 blocks

        const MethodClauseStats* s1 = findClause(cs.methods, "s1");
        const MethodClauseStats* s2 = findClause(cs.methods, "s2");
        const MethodClauseStats* s3 = findClause(cs.methods, "s3");
        CHECK(s1 != nullptr);
        CHECK(s2 != nullptr);
        CHECK(s3 != nullptr);
        if(s1) { checkHist(s1->furthestCompleted, {0, 1}); }  // completed locally
        if(s2) { checkHist(s2->furthestCompleted, {0, 1}); }  // completed locally
        if(s3)
        {
            CHECK_EQUAL(0, s3->groundingsN);   // s3 reached but gate-failed
            CHECK_EQUAL(1, s3->gateFailCount);
        }
        // s3 was reached (tested) but op3 never was.
        CHECK(findAtom(cs.atoms, "s3") != nullptr);
        CHECK(findAtom(cs.atoms, "op3") == nullptr);
    }

    // ===== Arithmetic-bearing subtasks ======================================
    // Regression for the bug where a body subtask carrying an arithmetic
    // argument (e.g. opGain(+(2,3))) lost its by-method position attribution:
    // ResolveArithmeticTerms (in NextTask) rewrites opGain(+(2,3)) -> opGain(5),
    // changing the interned HtnTerm* pointer BEFORE csRecordTested looks up the
    // csTermOrigin tag csTagBody stamped on the pre-resolution pointer. The tag
    // missed, so positions[k].tested was never bumped and csGroundingDeepestPos
    // never advanced -> the failure histogram blamed the wrong subtask.

    // Success path: an arithmetic-argument subtask must still be attributed to
    // its parent clause position (tested == 1, not 0).
    TEST(ArithmeticSubtask_PositionAttributed)
    {
        shared_ptr<HtnTermFactory> factory(new HtnTermFactory());
        shared_ptr<HtnRuleSet> state(new HtnRuleSet());
        shared_ptr<HtnPlanner> planner(new HtnPlanner());
        shared_ptr<HtnCompiler> compiler(new HtnCompiler(factory.get(), state.get(), planner.get()));
        compiler->ClearWithNewRuleSet();

        string program =
            "gain() :- if(), do(opGain(+(2, 3))). "
            "opGain(?x) :- del(), add(gained(?x)). "
            "goals(gain()). ";
        CHECK(compiler->Compile(program));

        std::vector<ChoiceRecord> cd;
        std::vector<MethodClauseStats> methodStats;
        std::vector<AtomStats> atomStats;
        auto solutions = planner->FindAllPlans(
            factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals(),
            5000000);
        cd = planner->GetLastChoiceData();
        methodStats = planner->GetLastMethodStats();
        atomStats = planner->GetLastAtomStats();
        CHECK(solutions != nullptr);

        const MethodClauseStats* gain = findClause(methodStats, "gain");
        CHECK(gain != nullptr);
        if(gain)
        {
            CHECK_EQUAL(1, gain->groundingsN);
            CHECK_EQUAL(1, gain->successS);
            const MethodPositionStats* p0 = findPos(*gain, 0);
            CHECK(p0 != nullptr);
            if(p0)
            {
                CHECK_EQUAL("opGain", p0->atomFunctor);
                CHECK_EQUAL(1, p0->testedCount);  // BUG: was 0 (tag lost on pointer change)
            }
        }

        // by-atom counting uses the resolved functor name, so it was always correct.
        const AtomStats* opGain = findAtom(atomStats, "opGain");
        CHECK(opGain != nullptr);
        if(opGain) { CHECK_EQUAL(1, opGain->testedCount); }
    }

    // Failure path: slot 0 (non-arithmetic) completes, slot 1 (arithmetic) is the
    // blocker. The histogram must blame slot 1, not slot 0.
    TEST(ArithmeticSubtask_FailureBlamesCorrectSlot)
    {
        shared_ptr<HtnTermFactory> factory(new HtnTermFactory());
        shared_ptr<HtnRuleSet> state(new HtnRuleSet());
        shared_ptr<HtnPlanner> planner(new HtnPlanner());
        shared_ptr<HtnCompiler> compiler(new HtnCompiler(factory.get(), state.get(), planner.get()));
        compiler->ClearWithNewRuleSet();

        // stepTwo(2) gate-fails (no allowed(2) fact), so head blocks at slot 1.
        string program =
            "head() :- if(), do(stepOne(), stepTwo(+(1, 1))). "
            "stepOne() :- if(), do(opOne()). "
            "stepTwo(?x) :- if(allowed(?x)), do(opTwo()). "
            "opOne() :- del(), add(). "
            "opTwo() :- del(), add(). "
            "goals(head()). ";
        CHECK(compiler->Compile(program));

        std::vector<ChoiceRecord> cd;
        std::vector<MethodClauseStats> methodStats;
        std::vector<AtomStats> atomStats;
        auto solutions = planner->FindAllPlans(
            factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals(),
            5000000);
        cd = planner->GetLastChoiceData();
        methodStats = planner->GetLastMethodStats();
        atomStats = planner->GetLastAtomStats();
        CHECK(solutions == nullptr);  // unsolvable: stepTwo's gate fails

        const MethodClauseStats* head = findClause(methodStats, "head");
        CHECK(head != nullptr);
        if(head)
        {
            CHECK_EQUAL(2, head->subtaskCount);
            // Correct: completed slot 0, blocked at slot 1 -> [0, 1, 0].
            // BUG produced [1, 0, 0] (blamed slot 0) because deepest never reached 1.
            checkHist(head->furthestCompleted, {0, 1, 0});

            const MethodPositionStats* p0 = findPos(*head, 0);
            const MethodPositionStats* p1 = findPos(*head, 1);
            CHECK(p0 != nullptr);
            CHECK(p1 != nullptr);
            if(p0)
            {
                CHECK_EQUAL("stepOne", p0->atomFunctor);
                CHECK_EQUAL(1, p0->testedCount);
                CHECK_EQUAL(0, p0->failCount);   // stepOne completed; not the blocker
            }
            if(p1)
            {
                CHECK_EQUAL("stepTwo", p1->atomFunctor);
                CHECK_EQUAL(1, p1->testedCount); // BUG: was 0 (arithmetic tag lost)
                CHECK_EQUAL(1, p1->failCount);   // BUG: was 0; fail landed on slot 0
            }
        }
    }

    // ===== Wrapper (parallel) not analyzed — documented limitations ==========
    // These two tests pin down the KNOWN, documented behaviour around bodies whose
    // subtasks live inside a parallel() wrapper (see docs/method-failure-analysis.md
    // "Semantics caveats" and the TODOs in csRecordGrounding). They are NOT asserting
    // ideal behaviour — they exist so the future "tag parallel() inner tasks" work has
    // a concrete target and so the (deliberately imprecise) clamp can't regress into a
    // crash. parallel(), unlike try(), does NOT absorb a failing inner task.

    // #1 — A method whose ENTIRE do() is a single parallel(...) has subtaskCount==0,
    // so csRecordGrounding's N==0 shortcut records the grounding as a FULL SUCCESS even
    // though the inner work fails and the plan is unsolvable. The inner task is still
    // visible (exactly) via its OWN by-atom / by-method entry — that's the documented
    // workaround. When parallel() inner tasks become first-class tagged subtasks, this
    // test should flip to expecting a failure at the inner slot.
    TEST(ParallelOnlyBody_FalseSuccess_Documented)
    {
        shared_ptr<HtnTermFactory> factory(new HtnTermFactory());
        shared_ptr<HtnRuleSet> state(new HtnRuleSet());
        shared_ptr<HtnPlanner> planner(new HtnPlanner());
        shared_ptr<HtnCompiler> compiler(new HtnCompiler(factory.get(), state.get(), planner.get()));
        compiler->ClearWithNewRuleSet();

        // head's body is only parallel(failTask). failTask gate-fails (no 'missing'
        // fact), so the parallel block fails and head is unsolvable.
        string program =
            "head() :- if(), do(parallel(failTask())). "
            "failTask() :- if(missing), do(opNoop()). "
            "opNoop() :- del(), add(). "
            "goals(head()). ";
        CHECK(compiler->Compile(program));

        auto solutions = planner->FindAllPlans(
            factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals(), 5000000);
        std::vector<MethodClauseStats> methodStats = planner->GetLastMethodStats();
        std::vector<AtomStats> atomStats = planner->GetLastAtomStats();

        // Planning genuinely FAILS...
        CHECK(solutions == nullptr);

        // ...but head's by-method entry (wrongly, by documented limitation) shows a
        // full success because its tagged subtask count is 0 (parallel is skipped).
        const MethodClauseStats* head = findClause(methodStats, "head");
        CHECK(head != nullptr);
        if(head)
        {
            CHECK_EQUAL(0, head->subtaskCount);     // parallel() occupies no slot
            CHECK_EQUAL(1, head->groundingsN);
            CHECK_EQUAL(1, head->successS);         // <-- documented false success
            CHECK_EQUAL(0, head->gateFailCount);    // head's own gate passed
            checkHist(head->furthestCompleted, {1});  // size N+1 == 1, all "success"
        }

        // The real signal is intact on the INNER task's own entries: failTask was
        // reached and its gate failed; this is how you actually diagnose such a method.
        const MethodClauseStats* failTask = findClause(methodStats, "failTask");
        CHECK(failTask != nullptr);
        if(failTask)
        {
            CHECK_EQUAL(0, failTask->groundingsN);
            CHECK_EQUAL(1, failTask->gateFailCount);
        }
        const AtomStats* failAtom = findAtom(atomStats, "failTask");
        CHECK(failAtom != nullptr);
        if(failAtom) { CHECK_EQUAL(1, failAtom->testedCount); }
    }

    // #2 — The clamp path. When a parallel() wrapper that appears BEFORE a method's
    // first tagged subtask fails, that tagged subtask is never reached, so
    // csGroundingDeepestPos stays -1 with N>=1. Pre-clamp this tripped a
    // FailFastAssertDesc (process abort / thrown error); now it clamps into [0,N) and
    // degrades gracefully. The blame lands (imprecisely, by design) on slot 0 — the
    // un-reached realSub — until parallel() inner tasks are tagged. The fact that this
    // test runs to completion at all is the regression guard against the crash.
    TEST(Clamp_ParallelBlockerBeforeTaggedSubtask_NoCrash)
    {
        shared_ptr<HtnTermFactory> factory(new HtnTermFactory());
        shared_ptr<HtnRuleSet> state(new HtnRuleSet());
        shared_ptr<HtnPlanner> planner(new HtnPlanner());
        shared_ptr<HtnCompiler> compiler(new HtnCompiler(factory.get(), state.get(), planner.get()));
        compiler->ClearWithNewRuleSet();

        // Body: parallel(blocker()) FIRST, then the tagged realSub(). blocker gate-fails,
        // so the branch dies inside the parallel before realSub (slot 0) is ever tested.
        string program =
            "head() :- if(), do(parallel(blocker()), realSub()). "
            "blocker() :- if(missing), do(opNoop()). "
            "realSub() :- if(), do(opReal()). "
            "opNoop() :- del(), add(). "
            "opReal() :- del(), add(). "
            "goals(head()). ";
        CHECK(compiler->Compile(program));

        auto solutions = planner->FindAllPlans(
            factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals(), 5000000);
        std::vector<MethodClauseStats> methodStats = planner->GetLastMethodStats();
        std::vector<AtomStats> atomStats = planner->GetLastAtomStats();

        // Unsolvable: blocker's gate fails inside the parallel block.
        CHECK(solutions == nullptr);

        const MethodClauseStats* head = findClause(methodStats, "head");
        CHECK(head != nullptr);
        if(head)
        {
            CHECK_EQUAL(1, head->subtaskCount);   // only realSub is tagged (parallel skipped)
            CHECK_EQUAL(1, head->groundingsN);
            CHECK_EQUAL(0, head->successS);
            // deepest stayed -1 (realSub never reached) -> clamped to slot 0.
            checkHist(head->furthestCompleted, {1, 0});

            // Slot 0 (realSub) carries the clamped failure even though it never ran —
            // testedCount==0 but failCount==1. This is the documented imprecision.
            const MethodPositionStats* p0 = findPos(*head, 0);
            CHECK(p0 != nullptr);
            if(p0)
            {
                CHECK_EQUAL("realSub", p0->atomFunctor);
                CHECK_EQUAL(0, p0->testedCount);  // never reached
                CHECK_EQUAL(1, p0->failCount);    // clamp blamed it anyway
            }
        }

        // realSub was genuinely never reached: it has no method clause of its own.
        CHECK(findClause(methodStats, "realSub") == nullptr);
        // ...yet the clamp's blame of slot 0 also bumps realSub's by-atom failCount via
        // csAtom, creating a PHANTOM by-atom entry (tested==0, fail==1) for a task that
        // never ran. Another facet of the documented imprecision (it breaks the usual
        // "by-atom counts are exact" promise specifically for parallel-wrapped bodies);
        // it should disappear once parallel() inner tasks are tagged.
        const AtomStats* realSubAtom = findAtom(atomStats, "realSub");
        CHECK(realSubAtom != nullptr);
        if(realSubAtom)
        {
            CHECK_EQUAL(0, realSubAtom->testedCount);
            CHECK_EQUAL(1, realSubAtom->failCount);
        }

        // The actual blocker is visible via its own entries (the real diagnosis path).
        const MethodClauseStats* blocker = findClause(methodStats, "blocker");
        CHECK(blocker != nullptr);
        if(blocker) { CHECK_EQUAL(1, blocker->gateFailCount); }
        const AtomStats* blockerAtom = findAtom(atomStats, "blocker");
        CHECK(blockerAtom != nullptr);
        if(blockerAtom) { CHECK_EQUAL(1, blockerAtom->testedCount); }
    }
}

#endif // INDHTN_CHOICE_TRACKING
