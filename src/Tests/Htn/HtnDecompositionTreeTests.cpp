//
//  HtnDecompositionTreeTests.cpp
//  TestLib
//
//  Tests for decomposition tree structure, particularly sibling flattening.
//  Copyright 2025 Bertrand Decoster. All rights reserved.
//

#include <map>
#include <set>
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

    // Test: try() failure must not corrupt sibling stack
    // Mimics CombatLevel1_GreaseTrap.htn scenario where try(triggerSnareEnemies) fails
    // and causes bringEnemyTo to incorrectly become child of applyTag instead of sibling
    TEST(TryFailureSiblingTracking)
    {
        TreeTestHelper helper;

        // Domain:
        // - mainGoal has 3 sibling tasks: childA, childB, childC
        // - childB decomposes to tasks including try() that fails
        // - After try() failure, childC should still be sibling of childB, not child
        string program = R"(
            hasItem.

            mainGoal() :- if(), do(childA, childB, childC).

            childA() :- if(), do(opA).
            opA() :- del(), add(aDone).

            % childB has try() where first succeeds, second fails
            childB() :- if(), do(opB1, try(trySucceeds), try(tryFails)).
            trySucceeds() :- if(hasItem), do(opB2).
            tryFails() :- if(noSuchFact), do(opB3).
            opB1() :- del(), add().
            opB2() :- del(), add().

            childC() :- if(), do(opC).
            opC() :- del(), add(cDone).

            goals(mainGoal()).
        )";

        auto solution = helper.FindFirstSolution(program);
        CHECK(solution != nullptr);
        if(!solution) return;

        const auto& tree = solution->decompositionTree;

        // Find mainGoal (root), childA, childB, childC nodes
        const DecompTreeNode* mainGoal = helper.FindNodeByTaskPrefix(tree, "mainGoal");
        const DecompTreeNode* childA = helper.FindNodeByTaskPrefix(tree, "childA");
        const DecompTreeNode* childB = helper.FindNodeByTaskPrefix(tree, "childB");
        const DecompTreeNode* childC = helper.FindNodeByTaskPrefix(tree, "childC");

        CHECK(mainGoal != nullptr);
        CHECK(childA != nullptr);
        CHECK(childB != nullptr);
        CHECK(childC != nullptr);
        if(!mainGoal || !childA || !childB || !childC) return;

        int mainGoalNodeID = mainGoal->nodeID;

        // All three children should be direct children of mainGoal
        CHECK_EQUAL(mainGoalNodeID, childA->parentNodeID);
        CHECK_EQUAL(mainGoalNodeID, childB->parentNodeID);

        // THE BUG: Before fix, try() failure left stale sibling scope on stack,
        // causing childC to incorrectly become child of childB instead of sibling.
        // After fix, childC should be direct child of mainGoal like childA and childB.
        CHECK_EQUAL(mainGoalNodeID, childC->parentNodeID);
    }

    // Test: Matches CombatLevel1_GreaseTrap structure exactly
    // theSlipstream -> [navigateTo, applyTag, bringEnemyTo]
    // applyTag -> applyTagEffect -> [opApply, try(triggerFreeze), try(triggerSnare)]
    // triggerSnare fails, then bringEnemyTo should be sibling of applyTag (not child)
    TEST(SlipstreamScenario)
    {
        TreeTestHelper helper;

        string program = R"(
            terrain(oilRoom, oil).

            theSlipstream() :- if(), do(navigateTo, applyTag, bringEnemyTo).

            navigateTo() :- if(), do(opNavigate).
            opNavigate() :- del(), add().

            applyTag() :- if(), do(applyTagEffect).
            applyTagEffect() :- if(), do(opApply, try(triggerFreeze), try(triggerSnare)).

            triggerFreeze() :- if(terrain(oilRoom, oil)), do(opFreeze).
            triggerSnare() :- if(noEnemyHere), do(opSnare).

            opApply() :- del(), add().
            opFreeze() :- del(), add().

            bringEnemyTo() :- if(), do(opBring).
            opBring() :- del(), add().

            goals(theSlipstream()).
        )";

        auto solution = helper.FindFirstSolution(program);
        CHECK(solution != nullptr);
        if(!solution) return;

        const auto& tree = solution->decompositionTree;

        // Find theSlipstream and bringEnemyTo
        const DecompTreeNode* theSlipstream = helper.FindNodeByTaskPrefix(tree, "theSlipstream");
        const DecompTreeNode* bringEnemyTo = helper.FindNodeByTaskPrefix(tree, "bringEnemyTo");
        const DecompTreeNode* applyTag = helper.FindNodeByTaskPrefix(tree, "applyTag");

        CHECK(theSlipstream != nullptr);
        CHECK(bringEnemyTo != nullptr);
        CHECK(applyTag != nullptr);
        if(!theSlipstream || !bringEnemyTo || !applyTag) return;

        // bringEnemyTo should be a sibling of applyTag (both children of theSlipstream)
        // parentNodeID now refers to parent's treeNodeID, not nodeID
        CHECK_EQUAL(theSlipstream->treeNodeID, bringEnemyTo->parentNodeID);
        CHECK_EQUAL(theSlipstream->treeNodeID, applyTag->parentNodeID);

        // All treeNodeIDs should be unique
        std::set<int> treeNodeIDs;
        for(const auto& node : tree) {
            CHECK(treeNodeIDs.find(node.treeNodeID) == treeNodeIDs.end());
            treeNodeIDs.insert(node.treeNodeID);
        }

        // Check for duplicates
        std::map<std::pair<int, std::string>, int> entryCount;
        for(const auto& node : tree) {
            auto key = std::make_pair(node.nodeID, node.taskName);
            entryCount[key]++;
        }

        for(const auto& entry : entryCount) {
            if(entry.second > 1) {
                printf("DUPLICATE: nodeID=%d, taskName='%s', count=%d\n",
                       entry.first.first, entry.first.second.c_str(), entry.second);
            }
            CHECK_EQUAL(1, entry.second);
        }
    }

    // Test: No duplicate tree entries for the same task on the same node
    // When try() fails, the next task gets processed on the same node. We must not
    // create duplicate tree entries for the failed try() task.
    TEST(NoDuplicateTreeEntries)
    {
        TreeTestHelper helper;

        // Same domain as TryFailureSiblingTracking
        string program = R"(
            hasItem.

            mainGoal() :- if(), do(childA, childB, childC).

            childA() :- if(), do(opA).
            opA() :- del(), add(aDone).

            childB() :- if(), do(opB1, try(trySucceeds), try(tryFails)).
            trySucceeds() :- if(hasItem), do(opB2).
            tryFails() :- if(noSuchFact), do(opB3).
            opB1() :- del(), add().
            opB2() :- del(), add().

            childC() :- if(), do(opC).
            opC() :- del(), add(cDone).

            goals(mainGoal()).
        )";

        auto solution = helper.FindFirstSolution(program);
        CHECK(solution != nullptr);
        if(!solution) return;

        const auto& tree = solution->decompositionTree;

        // Check for duplicates: count occurrences of each (nodeID, taskName) pair
        std::map<std::pair<int, std::string>, int> entryCount;
        for(const auto& node : tree) {
            auto key = std::make_pair(node.nodeID, node.taskName);
            entryCount[key]++;
        }

        // Verify no duplicates
        for(const auto& entry : entryCount) {
            if(entry.second > 1) {
                // Print diagnostic info on failure
                printf("DUPLICATE: nodeID=%d, taskName='%s', count=%d\n",
                       entry.first.first, entry.first.second.c_str(), entry.second);
            }
            CHECK_EQUAL(1, entry.second);
        }
    }
}
