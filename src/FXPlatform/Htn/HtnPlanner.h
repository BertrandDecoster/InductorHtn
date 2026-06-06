//
//  HtnPlanner.hpp
//  GameLib
//
//  Created by Eric Zinda on 1/7/19.
//  Copyright © 2019 Eric Zinda. All rights reserved.
//

#ifndef HtnPlanner_hpp
#define HtnPlanner_hpp

#include "HtnDomain.h"
#include "FXPlatform/Prolog/HtnGoalResolver.h"
#include <memory>
#include <vector>
#include <map>
#include <set>
#include <sstream>

// Decomposition tree node for exposing HTN structure to callers
// Captures both successful and failed branches for plan explanation
struct DecompTreeNode
{
    int treeNodeID;    // Unique ID for this tree entry (for parent-child relationships)
    int nodeID;        // PlanNode ID (may be shared when try() fails and next task runs on same node)
    int parentNodeID;  // Parent's treeNodeID, -1 for root
    std::vector<int> childNodeIDs;  // Children's treeNodeIDs
    std::string taskName;
    std::string methodSignature;  // Empty for operators
    std::string operatorSignature;  // Empty for methods
    std::vector<std::pair<std::string, std::string>> unifiers;  // head bindings
    std::vector<std::pair<std::string, std::string>> conditionBindings;  // if() clause bindings
    bool isOperator;
    bool isSuccess;  // Did this branch lead to a solution?
    bool isFailed;   // Did this branch fail?
    std::string failureReason;  // Why it failed (if applicable)
    int solutionID;  // Which solution this node contributed to (-1 = not yet assigned)

    // Structured data for programmatic access
    int methodIndex;                              // Document order (-1 for operators)
    std::vector<std::string> conditionTermsJson;  // Each condition term as structured JSON
    int failedConditionIndex;                     // Which condition term failed (-1 if none)
    std::string failedConditionTermJson;          // Structured JSON of the failing term

    DecompTreeNode() : treeNodeID(-1), nodeID(-1), parentNodeID(-1), isOperator(false), isSuccess(false), isFailed(false), solutionID(-1), methodIndex(-1), failedConditionIndex(-1) {}

    std::string ToJson() const
    {
        std::stringstream ss;
        ss << "{";
        ss << "\"treeNodeID\":" << treeNodeID << ",";
        ss << "\"nodeID\":" << nodeID << ",";
        ss << "\"parentNodeID\":" << parentNodeID << ",";
        ss << "\"childNodeIDs\":[";
        for(size_t i = 0; i < childNodeIDs.size(); i++) {
            ss << (i > 0 ? "," : "") << childNodeIDs[i];
        }
        ss << "],";
        // Escape special characters in strings
        auto escape = [](const std::string& s) {
            std::string result;
            for(char c : s) {
                if(c == '"') result += "\\\"";
                else if(c == '\\') result += "\\\\";
                else if(c == '\n') result += "\\n";
                else if(c == '\r') result += "\\r";
                else if(c == '\t') result += "\\t";
                else result += c;
            }
            return result;
        };
        ss << "\"taskName\":\"" << escape(taskName) << "\",";
        ss << "\"methodSignature\":\"" << escape(methodSignature) << "\",";
        ss << "\"operatorSignature\":\"" << escape(operatorSignature) << "\",";
        ss << "\"unifiers\":[";
        for(size_t i = 0; i < unifiers.size(); i++) {
            ss << (i > 0 ? "," : "") << "{\"" << escape(unifiers[i].first)
               << "\":\"" << escape(unifiers[i].second) << "\"}";
        }
        ss << "],";
        ss << "\"conditionBindings\":[";
        for(size_t i = 0; i < conditionBindings.size(); i++) {
            ss << (i > 0 ? "," : "") << "{\"" << escape(conditionBindings[i].first)
               << "\":\"" << escape(conditionBindings[i].second) << "\"}";
        }
        ss << "],";
        ss << "\"isOperator\":" << (isOperator ? "true" : "false") << ",";
        ss << "\"isSuccess\":" << (isSuccess ? "true" : "false") << ",";
        ss << "\"isFailed\":" << (isFailed ? "true" : "false") << ",";
        ss << "\"failureReason\":\"" << escape(failureReason) << "\",";
        ss << "\"solutionID\":" << solutionID << ",";
        // Structured data
        ss << "\"methodIndex\":" << methodIndex << ",";
        ss << "\"conditionTerms\":[";
        for(size_t i = 0; i < conditionTermsJson.size(); i++) {
            ss << (i > 0 ? "," : "") << conditionTermsJson[i];  // Already JSON, no quotes
        }
        ss << "],";
        ss << "\"failedConditionIndex\":" << failedConditionIndex << ",";
        ss << "\"failedConditionTerm\":" << (failedConditionTermJson.empty() ? "null" : failedConditionTermJson);
        ss << "}";
        return ss.str();
    }
};

#ifdef INDHTN_CHOICE_TRACKING
struct ChoiceRecord {
    std::string taskFunctor;          // e.g. "defeatEnemy"
    std::string taskFull;             // e.g. "defeatEnemy(guard1)"
    int depth;                        // stack depth when task was popped
    std::vector<std::string> unifyingMethods;  // all methods whose head unified
    std::vector<std::string> viableMethods;    // subset with satisfiable if()
};

// ---------------------------------------------------------------------------
// Cross-search choice-count tracking (richer than ChoiceRecord's sets).
//
// Accumulated over the ENTIRE backtracking search (not just successful plans).
// Two report views are projected from the same recorded events:
//   * "by atom"   - global rollup keyed by the task functor.
//   * "by method" - keyed by the parent method clause, with one entry per
//                   subtask position in its do() list.
//
// Counting model (unit = groundings, LOCAL completion):
//   For a normal method M with N body subtasks, each precondition grounding is
//   classified by the furthest subtask of M's OWN body that fully completed
//   (its whole subtree reached leaves), independent of anything downstream of M:
//     furthestCompleted[k] (0<=k<N) = # groundings that completed subtasks
//                                     0..k-1 but failed to complete subtask k.
//     furthestCompleted[N]          = # groundings whose entire body completed.
//   So sum(furthestCompleted) == groundingsN. The histogram answers, e.g. for
//   do(find_enemy, cast_spell, loot_body): did this method fail to find, to
//   cast, or to loot? "Completion" is signalled locally by reaching M's
//   methodScopeEnd marker (which sits before M's continuation), so a downstream
//   sibling's failure does NOT count against M.
//   For backward-compatible reporting, positions[k].failCount == furthestCompleted[k]
//   and successS == furthestCompleted[N].
//   anyOf/allOf clauses are excluded from the histogram (they merge groundings).
// ---------------------------------------------------------------------------

// Per (atom, resolving method): how many invocations of the atom had this
// method's precondition clear (boolean per invocation; methods can overlap so
// these can sum to more than the atom's testedCount).
struct AtomMethodClear {
    std::string methodSignature;
    int methodDocOrder;
    int clearCount;
};

// "by atom" rollup, keyed by task functor.
struct AtomStats {
    std::string atomFunctor;
    bool isOperator;                  // true for leaf operators (no clears)
    int testedCount;                  // # invocations across the whole search
    int failCount;                    // # groundings that failed at this atom
    std::vector<AtomMethodClear> clears;
};

// One subtask position of a parent method clause's do() list.
struct MethodPositionStats {
    int positionIndex;
    std::string atomFunctor;          // functor of the subtask at this position
    int testedCount;                  // # times this position's atom was resolved
    int failCount;                    // # parent groundings that failed here
    std::vector<AtomMethodClear> clears;
};

// "by method" rollup, keyed by parent clause documentOrder (-1 == goal).
struct MethodClauseStats {
    int clauseDocOrder;
    std::string clauseSignature;
    std::string methodType;           // "normal" | "anyOf" | "allOf" | "goal"
    int subtaskCount;                 // N: # body subtasks (real, non-bookkeeping)
    int groundingsN;                  // # precondition groundings (== sum of furthestCompleted)
    int successS;                     // groundings whose whole body completed (== furthestCompleted[N])
    int gateFailCount;                // times the precondition gate failed (N==0)
    std::vector<int> furthestCompleted;  // size N+1; furthest locally-completed subtask histogram
    std::vector<MethodPositionStats> positions;
};

// Emission-time tag attached to each bound subtask term so that, when the term
// is later resolved, we can attribute it to the parent clause + position that
// emitted it. Keyed by HtnTerm* (see csTermOrigin).
struct ChoiceOrigin {
    int clauseDocOrder;               // parent clause (-1 == goal)
    int slot;                         // position within parent's do()
    int parentNodeID;                 // parent PlanNode nodeID (for grounding keys)
};
#endif

class HtnMethod;
enum class HtnMethodType;
class HtnOperator;
class HtnTerm;
class HtnTermFactory;
class PlanNode;
enum class PlanNodeContinuePoint;

// State of the planner.  Is a separate class so the caller can call back for more plans or just get the first one
// Note: could be enhanced easily to allow the planner to be called *very* iteratively so that it performs one while loop per call
// This would be better for games that want to move the plan forward a tiny bit every frame, for example, since the calculation is very bounded
class PlanState
{
public:
    PlanState(HtnTermFactory *factoryArg, std::shared_ptr<HtnRuleSet> initialState, const std::vector<std::shared_ptr<HtnTerm>> &initialGoals, int64_t memoryBudgetArg);

private:
    // No public access to data only used by implentation of planner
    friend class HtnPlanner;
    friend class PlanNode;

    void CheckHighestMemory(int64_t currentMemory, std::string extra1Name, int64_t extra1Size);
    void RecordFailure(int furthestCriteriaFailure, std::vector<std::shared_ptr<HtnTerm>> &criteriaFailureContext);
    int64_t dynamicSize();

    // *** Remember to update dynamicSize() if you change any member variables!
    int furthestCriteriaFailure;
    std::shared_ptr<HtnTerm> furthestCriteriaFailureGoal;
    std::vector<std::shared_ptr<HtnTerm>> furthestCriteriaFailureContext;
    int deepestTaskFailure;
    HtnTermFactory *factory;
    int64_t highestMemoryUsed;
    std::shared_ptr<HtnRuleSet> initialState;
    double startTimeSeconds;
    int64_t memoryBudget;
    int nextNodeID;
    int nextTreeNodeID;  // Separate counter for unique tree node IDs
    bool returnValue;
    std::shared_ptr<std::vector<std::shared_ptr<PlanNode>>> stack;

    // Decomposition tree - built incrementally during planning
    // Survives stack unwinding and captures both successful and failed branches
    std::vector<DecompTreeNode> decompositionTree;
    std::map<int, size_t> treeNodeIDToTreeIndex;  // Fast lookup: treeNodeID -> index in decompositionTree
    std::map<int, int> nodeIDToLastTreeNodeID;    // PlanNode nodeID -> last treeNodeID created for it
    std::map<int, int> bookkeepingParents;  // Track parent relationships for bookkeeping tasks (tryEnd, etc.)
    int currentSolutionID;  // Incremented each time a solution is found

#ifdef INDHTN_CHOICE_TRACKING
    std::vector<ChoiceRecord> choiceData;
    std::map<int, size_t> treeNodeIDToChoiceIndex;  // treeNodeID -> index in choiceData (unique per task, handles try() same-node reuse)

    // Cross-search choice-count tracking (see struct comments above).
    std::map<std::string, AtomStats> atomStatsByFunctor;   // "by atom" rollup
    std::map<int, MethodClauseStats> methodStatsByClause;  // "by method", key = clause documentOrder (-1 == goal)
    // bound-subtask term -> emitting clause/position. Keyed by interned HtnTerm*.
    // KNOWN LIMITATION: the same fully-ground subtask at two positions of one do()
    // (e.g. do(foo(x), foo(x))) interns to one pointer, so both resolve to the last
    // slot tagged. Mis-slots within that one method only; by-atom counts stay exact.
    // A decomposition-tree fix was scoped and declined as too invasive for the payoff
    // (see docs/method-failure-analysis.md "Semantics caveats").
    // Each entry holds the origin tag PLUS a strong ref to the (arithmetic-resolved)
    // term it is keyed on. The strong ref keeps that interned term alive for the whole
    // search so the factory's weak_ptr interning cannot free it and re-intern the same
    // subtask at a different address (which would miss the tag). It lives in the map
    // (rather than a side vector) so re-tagging the SAME interned pointer overwrites in
    // place instead of accumulating — retention is bounded by the number of DISTINCT
    // tagged terms, not by groundings*subtasks.
    //
    // The lifetime is whole-search ON PURPOSE: groundings nest (a deeper grounding can
    // complete while an outer one is still mid-body), so clearing per-grounding would
    // free an outer grounding's not-yet-tested subtasks and break attribution. Keeping
    // everything alive is correct; the strong ref in the map only removes the redundant
    // duplication, it does not (and must not) shorten the lifetime.
    std::map<const HtnTerm*, std::pair<ChoiceOrigin, std::shared_ptr<HtnTerm>>> csTermOrigin;
    std::map<int, int> csGroundingDeepestPos;              // parent nodeID -> deepest slot reached this grounding
    std::map<int, bool> csGroundingBodyDone;               // parent nodeID -> reached methodScopeEnd (body fully completed) this grounding
    std::map<int, std::set<int>> csClearedCounted;         // atom-resolving nodeID -> method docOrders already counted this invocation
#endif
};


class HtnPlanner : public HtnDomain
{
public:
    typedef std::vector<std::shared_ptr<HtnTerm>> GoalsType;
    typedef multimap<HtnTerm::HtnTermID, HtnMethod *> MethodsType;
    // Operators are indexed by their name only, not their name and arguments
    typedef map<string, HtnOperator *> OperatorsType;
    class SolutionType
    {
    public:
        SolutionType(const SolutionType &other) = default;
        SolutionType() {}
        SolutionType(std::vector<std::shared_ptr<HtnTerm>> operators, std::shared_ptr<HtnRuleSet> ruleSet) :
            first(operators),
            second(ruleSet)
        {
        }
        std::vector<std::shared_ptr<HtnTerm>> operators() { return first; }
        std::shared_ptr<HtnRuleSet> finalState() { return second; }
        
        // Public, and named first and second just for backwards compat with previous code
        std::vector<std::shared_ptr<HtnTerm>> first;
        std::shared_ptr<HtnRuleSet> second;
        double elapsedSeconds;
        int64_t highestMemoryUsed;

        // Decomposition tree - full tree including failed branches
        std::vector<DecompTreeNode> decompositionTree;
    };
    typedef std::vector<std::shared_ptr<SolutionType>> SolutionsType;
    
    HtnPlanner();
    virtual ~HtnPlanner();
    // Safe to call from another thread
    static void Abort() { m_abort = true; }
    virtual HtnMethod *AddMethod(std::shared_ptr<HtnTerm> head, const std::vector<std::shared_ptr<HtnTerm>> &condition, const std::vector<std::shared_ptr<HtnTerm>> &tasks, HtnMethodType methodType, bool isDefault);
    virtual HtnOperator *AddOperator(std::shared_ptr<HtnTerm>head,
                                     const std::vector<std::shared_ptr<HtnTerm>> &addList,
                                     const std::vector<std::shared_ptr<HtnTerm>> &deleteList,
                                     bool hidden = false,
                                     const std::vector<std::shared_ptr<HtnTerm>> &increaseList = std::vector<std::shared_ptr<HtnTerm>>(),
                                     const std::vector<std::shared_ptr<HtnTerm>> &decreaseList = std::vector<std::shared_ptr<HtnTerm>>());
    virtual void ClearAll();
    // Always check factory->outOfMemory() after calling to see if we ran out of memory during processing and the plan might not be complete
    std::shared_ptr<SolutionsType> FindAllPlans(HtnTermFactory *factory, std::shared_ptr<HtnRuleSet> initialState, const std::vector<std::shared_ptr<HtnTerm>> &initialGoals, int memoryBudget = 5000000,
                                                int64_t *highestMemoryUsedReturn = nullptr, int *furthestFailureIndex = nullptr, std::vector<std::shared_ptr<HtnTerm>> *furthestFailureContext = nullptr);
#ifdef INDHTN_CHOICE_TRACKING
    // Choice-count tracking results from the most recent FindAllPlans call. Retained
    // on the planner (like GetLastResolutionStepCount) rather than returned through
    // FindAllPlans' signature, so the macro never changes that public API's ABI.
    const std::vector<ChoiceRecord>& GetLastChoiceData() const { return m_lastChoiceData; }
    const std::vector<MethodClauseStats>& GetLastMethodStats() const { return m_lastMethodStats; }
    const std::vector<AtomStats>& GetLastAtomStats() const { return m_lastAtomStats; }
#endif
    // Always check factory->outOfMemory() after calling to see if we ran out of memory during processing and the plan might not be complete
    std::shared_ptr<SolutionType> FindPlan(HtnTermFactory *factory, std::shared_ptr<HtnRuleSet> initialState, std::vector<std::shared_ptr<HtnTerm>> &initialGoals, int memoryBudget = 5000000);
    // Always check factory->outOfMemory() after calling to see if we ran out of memory during processing and the plan might not be complete
    std::shared_ptr<SolutionType> FindNextPlan(PlanState *planState);
    bool HasGoal(const std::string &term);
    // Very inefficient but useful for testing
    bool DebugHasMethod(const std::string &head, const std::string &constraints, const std::string &tasks);
    bool HasOperator(const std::string &head, const std::string &deletions, const std::string &additions);
    static std::string ToStringSolution(std::shared_ptr<SolutionType> solution, bool json = false);
    static std::string ToStringSolutions(std::shared_ptr<SolutionsType> solutions, bool json = false);
    static std::string ToStringFacts(std::shared_ptr<SolutionType> solution);
    static std::string ToStringFacts(std::shared_ptr<SolutionsType> solutions);
    static std::string ToStringTree(std::shared_ptr<SolutionType> solution);

    HtnGoalResolver *goalResolver() { return m_resolver.get(); }
    virtual void AllMethods(std::function<bool(HtnMethod *)> handler)
    {
        for(auto method : m_methods)
        {
            if(!handler(method.second))
            {
                break;
            }
        }
    }

    virtual void AllOperators(std::function<bool(HtnOperator *)> handler)
    {
        for(auto op : m_operators)
        {
            if(!handler(op.second))
            {
                break;
            }
        }
    }

private:
    bool CheckForOperator(PlanState *planState);
    bool CheckForSpecialTask(PlanState *planState);
    std::shared_ptr<std::vector<pair<HtnMethod *, UnifierType>>> FindAllMethodsThatUnify(HtnTermFactory *termFactory, HtnRuleSet *prog, std::shared_ptr<HtnTerm> goal);
    std::shared_ptr<PlanNode> FindNodeWithID(std::vector<std::shared_ptr<PlanNode>> &stack, int id);
    void HandleAllOf(PlanState *planState);
    void HandleAnyOf(PlanState *planState);
    void Return(PlanState *planState, bool returnValue);
    std::shared_ptr<HtnPlanner::SolutionType> SolutionFromCurrentNode(PlanState *planState, std::shared_ptr<PlanNode> node);

    // Decomposition tree recording methods
    void RecordTreeNode(PlanState* planState, int nodeID, int parentID, std::shared_ptr<HtnTerm> task);
    void RecordMethodChoice(PlanState* planState, int nodeID, HtnMethod* method, const UnifierType& unifiers);
    void RecordConditionBindings(PlanState* planState, int nodeID, const UnifierType& condition);
    void RecordOperator(PlanState* planState, int nodeID, HtnOperator* op, const UnifierType& unifiers);
    void MarkPathSuccess(PlanState* planState, int leafNodeID);
    void MarkNodeFailed(PlanState* planState, int nodeID, const std::string& reason, int failedIndex = -1, std::shared_ptr<HtnTerm> failedTerm = nullptr);

    // Deferred tree node creation (creates tree nodes at task resolution time)
    int DetermineTreeParent(PlanState* planState, PlanNode* node);
    static int NodeIDToTreeNodeID(PlanState* planState, int nodeID);
    void CreateTreeNodeForTask(PlanState* planState, PlanNode* node);

#ifdef INDHTN_CHOICE_TRACKING
    // Cross-search choice-count tracking helpers (see struct comments above)
    static bool csIsBookkeeping(const std::string& name);
    static MethodClauseStats& csClause(PlanState* planState, int docOrder, const std::string& sig, const std::string& methodType);
    static MethodPositionStats& csPosition(MethodClauseStats& clause, int slot, const std::string& atomFunctor);
    static AtomStats& csAtom(PlanState* planState, const std::string& functor, bool isOperator);
    static void csBumpClear(std::vector<AtomMethodClear>& clears, const std::string& sig, int docOrder);
    // Tag each non-bookkeeping bound subtask with its emitting clause/position.
    void csTagBody(PlanState* planState, int clauseDocOrder, const std::string& clauseSig, int parentNodeID,
                   const std::string& methodType, const std::vector<std::shared_ptr<HtnTerm>>& boundSubtasks);
    bool csIsOperatorTask(const std::string& name);
    void csRecordTested(PlanState* planState, PlanNode* node);          // Hook A
    void csRecordClear(PlanState* planState, PlanNode* node);           // Hook B
    void csRecordGrounding(PlanState* planState, PlanNode* node, bool success);  // Hook C/D
    void csRecordGateFail(PlanState* planState, PlanNode* node);        // gate failure (N==0)

    // Retained results of the most recent FindAllPlans (copied from PlanState before
    // it is destroyed); exposed via GetLast* accessors. *** Update dynamicSize? No —
    // these belong to the planner, not the per-search PlanState. ***
    std::vector<ChoiceRecord> m_lastChoiceData;
    std::vector<MethodClauseStats> m_lastMethodStats;
    std::vector<AtomStats> m_lastAtomStats;
#endif

    // *** Remember to update dynamicSize() if you change any member variables!
    // Awful hack making this static. necessary because it was too late in schedule to properly plumb through an Abort
    static uint8_t m_abort;
    MethodsType m_methods;
    int m_nextDocumentOrder;
    OperatorsType m_operators;
    shared_ptr<HtnGoalResolver> m_resolver;
    int64_t m_dynamicSize;
};

#endif /* HtnPlanner_hpp */
