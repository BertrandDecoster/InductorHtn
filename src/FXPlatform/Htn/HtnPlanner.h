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
#include <sstream>

// Decomposition tree node for exposing HTN structure to callers
// Captures both successful and failed branches for plan explanation
struct DecompTreeNode
{
    int nodeID;
    int parentNodeID;  // -1 for root
    std::vector<int> childNodeIDs;
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

    DecompTreeNode() : nodeID(-1), parentNodeID(-1), isOperator(false), isSuccess(false), isFailed(false), solutionID(-1), methodIndex(-1), failedConditionIndex(-1) {}

    std::string ToJson() const
    {
        std::stringstream ss;
        ss << "{";
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
    bool returnValue;
    std::shared_ptr<std::vector<std::shared_ptr<PlanNode>>> stack;

    // Decomposition tree - built incrementally during planning
    // Survives stack unwinding and captures both successful and failed branches
    std::vector<DecompTreeNode> decompositionTree;
    std::map<int, size_t> nodeIDToTreeIndex;  // Fast lookup: nodeID -> index in decompositionTree
    std::map<int, int> bookkeepingParents;  // Track parent relationships for bookkeeping tasks (tryEnd, etc.)
    int currentSolutionID;  // Incremented each time a solution is found
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
    virtual HtnOperator *AddOperator(std::shared_ptr<HtnTerm>head, const std::vector<std::shared_ptr<HtnTerm>> &addList, const std::vector<std::shared_ptr<HtnTerm>> &deleteList, bool hidden = false);
    virtual void ClearAll();
    // Always check factory->outOfMemory() after calling to see if we ran out of memory during processing and the plan might not be complete
    std::shared_ptr<SolutionsType> FindAllPlans(HtnTermFactory *factory, std::shared_ptr<HtnRuleSet> initialState, const std::vector<std::shared_ptr<HtnTerm>> &initialGoals, int memoryBudget = 5000000,
                                                int64_t *highestMemoryUsedReturn = nullptr, int *furthestFailureIndex = nullptr, std::vector<std::shared_ptr<HtnTerm>> *furthestFailureContext = nullptr);
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
    void CreateTreeNodeForTask(PlanState* planState, PlanNode* node);

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
