//
//  HtnDecompositionTreeTests.cpp
//  TestLib
//
//  Tests for decomposition tree structure, particularly sibling flattening.
//  Copyright 2025 Bertrand Decoster. All rights reserved.
//

#include "FXPlatform/FailFast.h"
#include "FXPlatform/Parser/ParserDebug.h"
#include "FXPlatform/Prolog/HtnGoalResolver.h"
#include "FXPlatform/Prolog/HtnRuleSet.h"
#include "FXPlatform/Prolog/HtnTermFactory.h"
#include "FXPlatform/Htn/HtnPlanner.h"
#include "FXPlatform/Htn/HtnCompiler.h"
#include "FXPlatform/Prolog/PrologQueryCompiler.h"
#include "Logger.h"
#include "Tests/ParserTestBase.h"
#include "UnitTest++/UnitTest++.h"
using namespace Prolog;
using namespace std;

SUITE(HtnDecompositionTreeTests)
{
    class TreeTestHelper
    {
    public:
        TreeTestHelper()
        {
            factory = shared_ptr<HtnTermFactory>(new HtnTermFactory());
            state = shared_ptr<HtnRuleSet>(new HtnRuleSet());
            planner = shared_ptr<HtnPlanner>(new HtnPlanner());
            compiler = shared_ptr<HtnCompiler>(new HtnCompiler(factory.get(), state.get(), planner.get()));
        }

        shared_ptr<HtnPlanner::SolutionType> FindFirstSolution(const string& program)
        {
            compiler->ClearWithNewRuleSet();
            CHECK(compiler->Compile(program));
            return planner->FindPlan(factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals());
        }

        // Find node by task name prefix in decomposition tree
        const DecompTreeNode* FindNodeByTaskPrefix(const vector<DecompTreeNode>& tree, const string& prefix)
        {
            for(const auto& node : tree) {
                if(node.taskName.find(prefix) == 0) return &node;
            }
            return nullptr;
        }

        shared_ptr<HtnTermFactory> factory;
        shared_ptr<HtnRuleSet> state;
        shared_ptr<HtnPlanner> planner;
        shared_ptr<HtnCompiler> compiler;
    };

    // Test: Simple case - siblings should share same parent
    TEST(SiblingFlatteningSimple)
    {
        TreeTestHelper helper;

        // Domain: parent decomposes to 3 siblings, first sibling has children
        string program = R"(
            parent() :- if(), do(sibling1, sibling2, sibling3).
            sibling1() :- if(), do(child1a, child1b).
            sibling2() :- if(), do(opLeaf2).
            sibling3() :- if(), do(opLeaf3).
            child1a() :- if(), do(opLeaf1a).
            child1b() :- if(), do(opLeaf1b).
            opLeaf1a() :- del(), add().
            opLeaf1b() :- del(), add().
            opLeaf2() :- del(), add().
            opLeaf3() :- del(), add().
            goals(parent()).
        )";

        auto solution = helper.FindFirstSolution(program);
        CHECK(solution != nullptr);

        const auto& tree = solution->decompositionTree;

        // Find sibling1, sibling2, sibling3 nodes
        const DecompTreeNode* sibling1 = helper.FindNodeByTaskPrefix(tree, "sibling1");
        const DecompTreeNode* sibling2 = helper.FindNodeByTaskPrefix(tree, "sibling2");
        const DecompTreeNode* sibling3 = helper.FindNodeByTaskPrefix(tree, "sibling3");

        CHECK(sibling1 != nullptr);
        CHECK(sibling2 != nullptr);
        CHECK(sibling3 != nullptr);

        // All siblings must have same parent
        CHECK_EQUAL(sibling1->parentNodeID, sibling2->parentNodeID);
        CHECK_EQUAL(sibling1->parentNodeID, sibling3->parentNodeID);
    }

    // Test: RECURSIVE navigation - mimics theBurn scenario from CombatLevel1_GreaseTrap.htn
    // theBurn decomposes to: navigateTo, bringEnemyTo, applyTag
    // navigateTo is RECURSIVE: do(opMove, navigateTo)
    // Verifies that after navigateTo recursion completes, bringEnemyTo is sibling of navigateTo
    TEST(SiblingFlatteningWithRecursiveMethod)
    {
        TreeTestHelper helper;

        // Domain that mimics the real scenario EXACTLY:
        // - theBurn has 3 sibling tasks: navigateTo, bringEnemyTo, applyTag
        // - navigateTo base case has EMPTY do() - this is key!
        // - navigateTo recursive case calls itself
        // - After navigateTo completes, bringEnemyTo should be sibling of navigateTo
        string program = R"(
            at(start).
            path(start, mid).
            path(mid, dest).

            theBurn() :- if(), do(navigateTo(dest), bringEnemyTo, applyTag).

            % Base case: already at destination - EMPTY do() like real domain!
            navigateTo(?dest) :- if(at(?dest)), do().
            % Recursive case: move one step then continue
            navigateTo(?dest) :- else, if(at(?current), path(?current, ?next)), do(opMoveTo(?current, ?next), navigateTo(?dest)).

            bringEnemyTo() :- if(), do(opBringEnemy).
            applyTag() :- if(), do(opApplyTag).

            opMoveTo(?from, ?to) :- del(at(?from)), add(at(?to)).
            opBringEnemy() :- del(), add().
            opApplyTag() :- del(), add().

            goals(theBurn()).
        )";

        auto solution = helper.FindFirstSolution(program);
        CHECK(solution != nullptr);

        const auto& tree = solution->decompositionTree;

        // Find theBurn (root task)
        const DecompTreeNode* theBurn = helper.FindNodeByTaskPrefix(tree, "theBurn");
        CHECK(theBurn != nullptr);
        int theBurnNodeID = theBurn->nodeID;

        // Find first navigateTo (direct child of theBurn), opBringEnemy (leaf of bringEnemyTo),
        // and applyTag (sibling of navigateTo)
        //
        // Note: Methods decompose fully, so bringEnemyTo becomes opBringEnemy.
        // The KEY assertion: opBringEnemy's parent chain should go back to theBurn,
        // NOT through the empty do() node from navigateTo's base case.
        const DecompTreeNode* firstNavigateTo = nullptr;
        const DecompTreeNode* opBringEnemy = nullptr;
        const DecompTreeNode* applyTag = nullptr;

        for(const auto& node : tree) {
            // Get first navigateTo (should be direct child of theBurn)
            if(node.taskName.find("navigateTo") == 0 && firstNavigateTo == nullptr) {
                firstNavigateTo = &node;
            }
            if(node.taskName.find("opBringEnemy") == 0) {
                opBringEnemy = &node;
            }
            if(node.taskName.find("applyTag") == 0) {
                applyTag = &node;
            }
        }

        CHECK(firstNavigateTo != nullptr);
        CHECK(opBringEnemy != nullptr);
        CHECK(applyTag != nullptr);

        // First navigateTo should be direct child of theBurn
        CHECK_EQUAL(theBurnNodeID, firstNavigateTo->parentNodeID);

        // applyTag should also be direct child of theBurn
        CHECK_EQUAL(theBurnNodeID, applyTag->parentNodeID);

        // THE BUG: opBringEnemy's parent should be a node that is a child of theBurn
        // (i.e., bringEnemyTo), NOT a child of the empty do() node from navigateTo's base case.
        //
        // Since bringEnemyTo() :- if(), do(opBringEnemy), there's no intermediate node.
        // In a correct tree, opBringEnemy's parent should be a node with parentID=theBurnNodeID.
        //
        // Currently buggy: opBringEnemy->parentNodeID = 6 (empty node from navigateTo base case)
        // Expected: opBringEnemy's parent should be a node that has theBurn as its parent.

        // Find the parent of opBringEnemy
        int opBringEnemyParentID = opBringEnemy->parentNodeID;
        const DecompTreeNode* opBringEnemyParent = nullptr;
        for(const auto& node : tree) {
            if(node.nodeID == opBringEnemyParentID) {
                opBringEnemyParent = &node;
                break;
            }
        }

        CHECK(opBringEnemyParent != nullptr);

        // The parent of opBringEnemy (which represents bringEnemyTo's decomposition) should be theBurn
        // This was a bug when navigateTo's base case had empty do() - the empty node incorrectly
        // became the parent instead of theBurn
        CHECK_EQUAL(theBurnNodeID, opBringEnemyParent->parentNodeID);
    }
}
