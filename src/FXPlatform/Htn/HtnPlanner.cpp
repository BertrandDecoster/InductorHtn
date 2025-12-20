//
//  HtnPlanner.cpp
//  GameLib
//
//  Created by Eric Zinda on 1/7/19.
//  Copyright © 2019 Eric Zinda. All rights reserved.
//
#include <algorithm>
#include <functional>
#include "Logger.h"
#include "HtnGoalResolver.h"
#include "HtnMethod.h"
#include "HtnOperator.h"
#include "HtnPlanner.h"
#include "HtnRuleSet.h"
#include "HtnTerm.h"
#include "HtnTermFactory.h"
#include "FXPlatform/NanoTrace.h"

/** 
HtnPlanner works by having each node being focused on a single task. You can find this information in SOLVE
Node0 is the goal you asked the HTN

There is a lot of changing part inside a Node to prepare the child Nodes.
When you PUSH, you give the information of who is the child/parent

A task is either a method or an operator.


If it's a method, the node unifies the task with all the appropriate methods.
You get in each of one with METHOD. But not directly, first you get two unifiers, one for the head (substituted condition:) 
and one for the if/condition (condition:(?x = downtown, ?t = taxi1, ?d = 2) )
Only then do you PUSH / SOLVE
It's probably in PUSH that you need to get the two unifiers from your parent

If it's an operator, your task has to be grounded. Add the grounded operator, the added and removed facts to the node.
Note that some operators are dummy operators, they only exist to put information in the final plan. 
They start with m1_, m2_, m3_, ... The number is the arity

A node with no tasks is a SUCCESS

*/


uint8_t HtnPlanner::m_abort = 0;

const int indentSpaces = 11;
const int highNodeMemoryWarning = 1000000;

#define Trace0(status, trace, indent) \
TraceString("HtnPlanner::FindPlan " + string((indent) * indentSpaces, ' ') + status + trace, \
SystemTraceType::Planner, TraceDetail::Normal);

#define Trace1(status, trace, indent, arg1) \
TraceString1("HtnPlanner::FindPlan " + string((indent) * indentSpaces, ' ') + status + trace, \
SystemTraceType::Planner, TraceDetail::Normal, \
arg1);

#define Trace2(status, trace, indent, arg1, arg2) \
TraceString2("HtnPlanner::FindPlan " + string((indent) * indentSpaces, ' ') + status + trace, \
SystemTraceType::Planner, TraceDetail::Normal, \
arg1, arg2);

#define Trace3(status, trace, indent, arg1, arg2, arg3) \
TraceString3("HtnPlanner::FindPlan " + string((indent) * indentSpaces, ' ') + status + trace, \
SystemTraceType::Planner, TraceDetail::Normal, \
arg1, arg2, arg3);

#define Trace4(status, trace, indent, arg1, arg2, arg3, arg4) \
TraceString4("HtnPlanner::FindPlan " + string((indent) * indentSpaces, ' ') + status + trace, \
SystemTraceType::Planner, TraceDetail::Normal, \
arg1, arg2, arg3, arg4);

#define Trace5(status, trace, indent, arg1, arg2, arg3, arg4, arg5) \
TraceString5("HtnPlanner::FindPlan " + string((indent) * indentSpaces, ' ') + status + trace, \
SystemTraceType::Planner, TraceDetail::Normal, \
arg1, arg2, arg3, arg4, arg5);

#define Trace6(status, trace, indent, arg1, arg2, arg3, arg4, arg5, arg6) \
TraceString6("HtnPlanner::FindPlan " + string((indent) * indentSpaces, ' ') + status + trace, \
SystemTraceType::Planner, TraceDetail::Normal, \
arg1, arg2, arg3, arg4, arg5, arg6);

enum class PlanNodeContinuePoint
{
    Fail,
    NextTask,
    ReturnFromCheckForOperator,
    NextMethodThatApplies,
    NextNormalMethodCondition,
    OutOfMemory,
    ReturnFromNextNormalMethodCondition,
    ReturnFromHandleTryTerm,
    ReturnFromSetOfConditions,
    Abort
};

class PlanNode
{
public:
    PlanNode(int nodeID, shared_ptr<HtnRuleSet> stateArg, const vector<shared_ptr<HtnTerm>> &tasksArg, shared_ptr<vector<shared_ptr<HtnTerm>>> operatorsArg)
    {
        atLeastOneMethodHadSolution = false;
        conditionIndex = -1;
        continuePoint = PlanNodeContinuePoint::NextTask;
        m_nodeID = nodeID;
        method = pair<HtnMethod *, UnifierType>(nullptr, {});
        methodHadSolution = false;
        operators = operatorsArg;
        retry = false;
        state = stateArg;
        tasks = shared_ptr<vector<shared_ptr<HtnTerm>>>(new vector<shared_ptr<HtnTerm>>(tasksArg));
        totalMemoryAtNodePush = 0;
        tryAnyOfSuccessCount = 0;
#ifdef INDHTN_TREE_SIBLING_TRACKING
        // Stack-based sibling tracking for nested decompositions
        // Each entry is (siblingParentID, siblingRemainingCount)
        siblingStack = {};
#endif
    }
    
    void AddToOperators(shared_ptr<HtnTerm> operatorSubstituted)
    {
        if(operators == nullptr)
        {
            operators = shared_ptr<vector<shared_ptr<HtnTerm>>>(new vector<shared_ptr<HtnTerm>>);
        }
        
        operators->push_back(operatorSubstituted);
    }

    bool OutOfMemoryAtNodePush(PlanState *planState, shared_ptr<PlanNode> newNode)
    {
        newNode->totalMemoryAtNodePush = planState->dynamicSize();
        
        // Need to track when a node generates a ton of memory
        int64_t previousNodeMemory = newNode->totalMemoryAtNodePush - planState->stack->back()->totalMemoryAtNodePush;
        if(previousNodeMemory > highNodeMemoryWarning)
        {
            TraceString5("PlanState::dynamicSize *** High Node Memory *** total delta:{0}, node current size:{1}, planner total:{2}, term strings:{3}, term other:{4}",
                         SystemTraceType::Planner, TraceDetail::Normal,
                         previousNodeMemory, planState->stack->back()->dynamicSize(), newNode->totalMemoryAtNodePush, planState->factory->stringSize(), planState->factory->otherAllocationSize());
        }
        
        return newNode->totalMemoryAtNodePush > planState->memoryBudget;
    }
    
    void SearchNextNode(PlanState *planState, const vector<shared_ptr<HtnTerm>> &additionalTasks, PlanNodeContinuePoint returnPoint)
    {
        vector<shared_ptr<HtnTerm>> mergedTasks = *tasks;
        mergedTasks.insert(mergedTasks.begin(), additionalTasks.begin(), additionalTasks.end());
        shared_ptr<PlanNode> newNode = shared_ptr<PlanNode>(new PlanNode(planState->nextNodeID++, state, mergedTasks, operators));

        // Trying not to be too intrusive by checking for out of memory only when we create new nodes
        if(OutOfMemoryAtNodePush(planState, newNode))
        {
            newNode->continuePoint = PlanNodeContinuePoint::OutOfMemory;
        }

        planState->stack->push_back(newNode);
        Trace2("PUSH       ", "nodeID:{0} parentID:{1}", planState->stack->size(), newNode->nodeID(), nodeID());

#ifdef INDHTN_TREE_SIBLING_TRACKING
        // Copy sibling stack
        // (tree node creation is deferred to task resolution time in CreateTreeNodeForTask)
        newNode->siblingStack = siblingStack;
        // Pop any exhausted scopes first (count == 0 means last sibling already processed)
        while(!newNode->siblingStack.empty() && newNode->siblingStack.back().second == 0) {
            newNode->siblingStack.pop_back();
        }
        // Decrement sibling count - this task consumes a sibling slot
        if(!newNode->siblingStack.empty() && newNode->siblingStack.back().second > 0) {
            newNode->siblingStack.back().second--;
        }
#endif

        continuePoint = returnPoint;
    }

    // Create a new node with independent state and a union of current and new tasks (on the front)
    void SearchNextNodeBacktrackable(PlanState *planState, const vector<shared_ptr<HtnTerm>> &additionalTasks, PlanNodeContinuePoint returnPoint)
    {
        vector<shared_ptr<HtnTerm>> mergedTasks;
        // First add the additional tasks from method decomposition
        mergedTasks.insert(mergedTasks.end(), additionalTasks.begin(), additionalTasks.end());

#ifdef INDHTN_TREE_SIBLING_TRACKING
        // Insert scope end marker between additional tasks and remaining tasks.
        // When processed, this pops the sibling scope pushed for additionalTasks.
        // This ensures tasks from outer scopes get the correct tree parent.
        if(additionalTasks.size() > 0 && tasks->size() > 0) {
            mergedTasks.push_back(planState->factory->CreateFunctor("methodScopeEnd",
                {planState->factory->CreateConstant(lexical_cast<string>(nodeID()))}));
        }
#endif

        // Then add remaining tasks from parent scope
        mergedTasks.insert(mergedTasks.end(), tasks->begin(), tasks->end());

        shared_ptr<HtnRuleSet> stateCopy = state->CreateCopy();
        shared_ptr<vector<shared_ptr<HtnTerm>>> operatorsCopy;
        if(operators != nullptr)
        {
            operatorsCopy = shared_ptr<vector<shared_ptr<HtnTerm>>>(new vector<shared_ptr<HtnTerm>>(*operators));
        }

        shared_ptr<PlanNode> newNode = shared_ptr<PlanNode>(new PlanNode(planState->nextNodeID++, stateCopy, mergedTasks, operatorsCopy));

#ifdef INDHTN_TREE_SIBLING_TRACKING
        // Copy current sibling stack to new node (for nested decompositions)
        // (tree node creation is deferred to task resolution time in CreateTreeNodeForTask)
        newNode->siblingStack = siblingStack;

        // Pop any exhausted scopes first to prevent unbounded stack growth
        // This must happen for ALL cases (additionalTasks > 0 or empty do())
        while(!newNode->siblingStack.empty() && newNode->siblingStack.back().second == 0) {
            newNode->siblingStack.pop_back();
        }

        if(additionalTasks.size() > 0) {
            // Push new scope: parent is this node, count is N-1 (first task uses slot implicitly)
            // For single-task decompositions (N=1), count=0 means this scope will be popped
            // after the single child is processed
            newNode->siblingStack.push_back({nodeID(), (int)additionalTasks.size() - 1});
            Trace3("SIB_PUSH   ", "Pushed scope {{nodeID:{0}, count:{1}}} onto child nodeID:{2}", planState->stack->size(), nodeID(), (int)additionalTasks.size() - 1, newNode->nodeID());
        } else if(additionalTasks.size() == 0 && mergedTasks.size() > 0) {
            // Empty do() - decrement since we're continuing with existing tasks
            // (exhausted scopes already popped above)
            if(!newNode->siblingStack.empty() && newNode->siblingStack.back().second > 0) {
                newNode->siblingStack.back().second--;
            }
        }
#endif

        // Trying not to be too intrusive by checking for out of memory only when we create new nodes
        if(OutOfMemoryAtNodePush(planState, newNode))
        {
            newNode->continuePoint = PlanNodeContinuePoint::OutOfMemory;
        }
        planState->stack->push_back(newNode);
        Trace2("PUSH       ", "nodeID:{0} parentID:{1}", planState->stack->size(), newNode->nodeID(), nodeID());

        continuePoint = returnPoint;
    }

    void SetNextMethodThatUnifies()
    {
        // Reset the state that any method handling code uses
        conditionIndex = -1;
        conditionResolutions = nullptr;
        if(unifiedMethods->size() == 0)
        {
            method = pair<HtnMethod *, UnifierType>(nullptr, {});
        }
        else
        {
            method = unifiedMethods->front();
            unifiedMethods->erase(unifiedMethods->begin());
        }
    }
    
    // Get the task this node should solve
    void SetNodeTask()
    {
        if(tasks->size() > 0)
        {
            task = tasks->front();
            tasks->erase(tasks->begin());
        }
        else
        {
            task = nullptr;
        }
    }
    
    void SetNextCondition()
    {
        conditionIndex++;
    }
    
    UnifierType *condition()
    {
        if(conditionResolutions != nullptr && conditionIndex < conditionResolutions->size())
        {
            return &(conditionResolutions->at(conditionIndex));
        }
        else
        {
            return nullptr;
        }
    }
    
    int nodeID()
    {
        return m_nodeID;
    }

#ifdef INDHTN_TREE_SIBLING_TRACKING
    const std::vector<std::pair<int, int>>& getSiblingStack() const
    {
        return siblingStack;
    }

    std::vector<std::pair<int, int>>& getSiblingStackMutable()
    {
        return siblingStack;
    }

    // Pop the sibling scope if the top scope matches the given nodeID.
    // Used by tryEnd to exhaust the try() subtask scope.
    void popSiblingScopeIfMatches(int scopeNodeID)
    {
        if(!siblingStack.empty() && siblingStack.back().first == scopeNodeID) {
            siblingStack.pop_back();
        }
    }

    // Decrement the sibling count when moving to the next task on the same node,
    // and pop exhausted scopes. This ensures tasks from outer scopes (merged remainingTasks)
    // use the correct parent scope.
    // UNUSED
    void decrementAndCleanupSiblingScopes()
    {
        if(!siblingStack.empty() && siblingStack.back().second > 0) {
            siblingStack.back().second--;
        }
        while(!siblingStack.empty() && siblingStack.back().second == 0) {
            siblingStack.pop_back();
        }
    }
#endif

    // Relatively expensive to calculate!
    int64_t dynamicSize()
    {
        int64_t conditionResolutionsSize = 0;
        if(conditionResolutions != nullptr)
        {
            conditionResolutionsSize = sizeof(vector<UnifierType>) + conditionResolutions->size() * sizeof(UnifierType);
            for(UnifierType &unifier : *conditionResolutions)
            {
                conditionResolutionsSize += unifier.size() * sizeof(UnifierItemType);
            }
        }
        
        int64_t unifiedMethodsSize = 0;
        if(unifiedMethods != nullptr)
        {
            unifiedMethodsSize = sizeof(vector<pair<HtnMethod *, UnifierType>>) + unifiedMethods->size() * sizeof(pair<HtnMethod *, UnifierType>);
            for(pair<HtnMethod *, UnifierType> &currMethod : *unifiedMethods)
            {
                unifiedMethodsSize += currMethod.second.size() * sizeof(UnifierItemType);
            }
        }
        
        return sizeof(PlanNode) +
            conditionResolutionsSize +
            method.second.size() * sizeof(UnifierItemType) +
            (operators == nullptr ? 0 : sizeof(vector<shared_ptr<HtnTerm>>) + operators->size() * sizeof(shared_ptr<HtnTerm>)) +
            state->dynamicSize() +
            (tasks == nullptr ? 0 : sizeof(vector<shared_ptr<HtnTerm>>) + tasks->size() * sizeof(shared_ptr<HtnTerm>)) +
            unifiedMethodsSize;
    }

    // *** Remember to update dynamicSize() if you change any member variables!
    bool atLeastOneMethodHadSolution;
    int conditionIndex;
    shared_ptr<vector<UnifierType>> conditionResolutions;
    PlanNodeContinuePoint continuePoint;
    pair<HtnMethod *, UnifierType> method;
    bool methodHadSolution;
    shared_ptr<vector<shared_ptr<HtnTerm>>> operators;
    bool retry;
    shared_ptr<HtnRuleSet> state;
    shared_ptr<HtnTerm> task;
    shared_ptr<vector<shared_ptr<HtnTerm>>> tasks;
    int64_t totalMemoryAtNodePush;
    int tryAnyOfSuccessCount;
    shared_ptr<vector<pair<HtnMethod *, UnifierType>>> unifiedMethods;
    
private:
    int m_nodeID;
#ifdef INDHTN_TREE_SIBLING_TRACKING
    // Stack-based sibling tracking: each entry is (siblingParentID, siblingRemainingCount)
    // Top of stack is the current sibling scope; when all siblings processed, pop to outer scope
    std::vector<std::pair<int, int>> siblingStack;
#endif
};

// The value returned indicates whether the element passed as first argument is considered to go before the second in the specific strict weak ordering it defines.
// A Strict Weak Ordering is a Binary Predicate that compares two objects, returning true if the first precedes the second
// Sort so the first rules in the document are first in the list
bool MethodComparer(const pair<HtnMethod *, UnifierType> &left, const pair<HtnMethod *, UnifierType> &right)
{
    if(left.first != nullptr && right.first != nullptr)
    {
        return left.first->documentOrder() < right.first->documentOrder();
    }
    else
    {
        StaticFailFastAssertDesc(false, "Internal Error");
        return false;
    }
}

PlanState::PlanState(HtnTermFactory *factoryArg, shared_ptr<HtnRuleSet> initialStateArg, const vector<shared_ptr<HtnTerm>> &initialGoals, int64_t memoryBudgetArg) :
    furthestCriteriaFailure(-1),
    deepestTaskFailure(-1),
    factory(factoryArg),
    highestMemoryUsed(0),
    initialState(initialStateArg),
    memoryBudget(memoryBudgetArg),
    nextNodeID(0),
    nextTreeNodeID(0),
    returnValue(false),
    stack(shared_ptr<vector<shared_ptr<PlanNode>>>(new vector<shared_ptr<PlanNode>>())),
    currentSolutionID(0)
{
    // First node is the initial tasks with no solution
    shared_ptr<PlanNode> initialNode = shared_ptr<PlanNode>(new PlanNode(nextNodeID++, initialStateArg, initialGoals, nullptr));
    stack->push_back(initialNode);

    // Record root node in decomposition tree
    DecompTreeNode rootTreeNode;
    rootTreeNode.treeNodeID = nextTreeNodeID++;
    rootTreeNode.nodeID = initialNode->nodeID();
    rootTreeNode.parentNodeID = -1;  // Root has no parent
    rootTreeNode.taskName = (initialGoals.size() > 0 && initialGoals[0]) ? initialGoals[0]->ToString() : "";
    treeNodeIDToTreeIndex[rootTreeNode.treeNodeID] = 0;
    nodeIDToLastTreeNodeID[rootTreeNode.nodeID] = rootTreeNode.treeNodeID;
    decompositionTree.push_back(rootTreeNode);
}

void PlanState::CheckHighestMemory(int64_t currentMemory, string extra1Name, int64_t extra1Size)
{
    if(currentMemory > highestMemoryUsed)
    {
        highestMemoryUsed = currentMemory;
        Trace6("HIGHESTMEM ", "total:{0}, {1}:{2}, term strings:{3}, term other:{4}, shared rules: {5}", stack->size(), currentMemory, extra1Name, extra1Size, factory->stringSize(), factory->otherAllocationSize(), initialState->dynamicSharedSize());
    }
}

// *Approximate* memory used since it is surprisingly hard to determine exact amount
int64_t PlanState::dynamicSize()
{
    int64_t stackSize = 0;
    for(auto node : *stack)
    {
        stackSize += node->dynamicSize();
    }
    
    int64_t currentMemory = sizeof(PlanState) +
        // locked rules shared by all nodes
        initialState->dynamicSharedSize() +
        // memory used by all terms
        factory->dynamicSize() +
        // memory used for failurecontext
        furthestCriteriaFailureContext.size() * sizeof(std::shared_ptr<HtnTerm>) +
        // memory used by everything on the stack
        stack->size() * sizeof(shared_ptr<PlanNode>) + stackSize;
    
    FailFastAssertDesc(currentMemory >= 0, "Internal Error");
    CheckHighestMemory(currentMemory, "stackSize", stackSize);
    
    return currentMemory;
}

// We want to record error context for the failure that happened:
// Deepest in the "resolving tasks" stack
// and if there is more than one failure at the same level of that stack
// record the failure that happened farthest along in the list of terms in the criteria
void PlanState::RecordFailure(int furthestCriteriaFailure, std::vector<std::shared_ptr<HtnTerm>> &criteriaFailureContext)
{
    if((this->stack->size() == this->deepestTaskFailure && (furthestCriteriaFailure > this->furthestCriteriaFailure)) ||
       ((int) stack->size() > this->deepestTaskFailure))
    {
        this->deepestTaskFailure = (int) stack->size();
        this->furthestCriteriaFailure = furthestCriteriaFailure;
        this->furthestCriteriaFailureContext = criteriaFailureContext;
    }
}

HtnPlanner::HtnPlanner() :
    m_nextDocumentOrder(0),
    m_dynamicSize(0)
{
    HtnPlanner::m_abort = 0;
    m_resolver = shared_ptr<HtnGoalResolver>(new HtnGoalResolver());
}

HtnPlanner::~HtnPlanner()
{
    // No need to delete tasks since they are managed by TermFactory
    ClearAll();
}

HtnMethod *HtnPlanner::AddMethod(shared_ptr<HtnTerm> head, const vector<shared_ptr<HtnTerm>> &condition, const vector<shared_ptr<HtnTerm>> &tasks, HtnMethodType methodType, bool isDefault)
{
    m_nextDocumentOrder++;
    
    // methods are owned by the Htn planner and deleted in the destructor. Since they are immutable, we can just record size now
    HtnMethod *method = new HtnMethod(head, condition, tasks, methodType, isDefault, m_nextDocumentOrder);
    m_dynamicSize += method->dynamicSize();
    m_methods.insert(pair<HtnTerm::HtnTermID, HtnMethod *>(head->GetUniqueID(), method));
    return method;
}

HtnOperator *HtnPlanner::AddOperator(shared_ptr<HtnTerm> head, const vector<shared_ptr<HtnTerm>> &addList, const vector<shared_ptr<HtnTerm>> &deleteList, bool hidden)
{
    // operators are owned by the Htn planner and deleted in the destructor. Since they are immutable, we can just record it now
    HtnOperator *op = new HtnOperator(head, addList, deleteList, hidden);
    m_dynamicSize += op->dynamicSize();
    m_operators.insert(pair<string, HtnOperator *>(head->name(), op));
    return op;
}

bool HtnPlanner::CheckForOperator(PlanState *planState)
{
    // Make the code more readable and get rid of one pointer dereference
    HtnTermFactory *factory = planState->factory;
    shared_ptr<vector<shared_ptr<PlanNode>>> stack = planState->stack;
    
    shared_ptr<PlanNode> node = stack->back();
    
    // Is it an operator?
    OperatorsType::iterator foundOperator = m_operators.find(node->task->name());
    if(foundOperator != m_operators.end())
    {
        HtnOperator *op = (*foundOperator).second;
        
        // Get the "Most General Unifier" for the operator and the task and make sure it is ground (otherwise it is invalid)
        shared_ptr<UnifierType> mgu = HtnGoalResolver::Unify(factory, node->task, op->head());
        if(mgu != nullptr && HtnGoalResolver::IsGround(mgu.get()))
        {
            // Substitute the MGU into any variables in the operator
            shared_ptr<HtnTerm> operatorSubstituted = HtnGoalResolver::SubstituteUnifiers(factory, *mgu.get(), op->head());
            
            // And into the adds and deletes
            shared_ptr<vector<shared_ptr<HtnTerm>>> finalRemovals = HtnGoalResolver::SubstituteUnifiers(factory, *mgu, op->deletions());
            shared_ptr<vector<shared_ptr<HtnTerm>>> finalAdditions = HtnGoalResolver::SubstituteUnifiers(factory, *mgu, op->additions());
            
            // We don't have alternatives to try from this node if the branch fails, so we don't need to make a copy of the state so we can try alternatives
            // So, just update the state directly
            node->state->Update(factory, *finalRemovals, *finalAdditions);
            
            if(!op->isHidden())
            {
                // Add the operator to the current list
                node->AddToOperators(operatorSubstituted);
            }
            
            // Continue recursion: No additional tasks since this is an operator, don't make a copy of the state since we don't need to try alternatives when backtracking
            Trace3("OPERATOR   ", "nodeID:{0} Operator '{1}' unifies with '{2}'", stack->size(), node->nodeID(), op->head()->ToString(), node->task->ToString());
            Trace3("           ", "isHidden: {0}, deletes:'{1}', adds:'{2}'", stack->size(), op->isHidden(), HtnTerm::ToString(*finalRemovals), HtnTerm::ToString(*finalAdditions));

            // Record operator in decomposition tree
            RecordOperator(planState, node->nodeID(), op, *mgu);

            node->SearchNextNode(planState, {}, PlanNodeContinuePoint::ReturnFromCheckForOperator);
            return true;
        }
        else
        {
            // task was an operator but didn't properly unify, this should never happen in a well-written program since there is only ever one operator of a given name
            // and their whole point is to modify state
            Trace3("FAIL       ", "nodeID:{0} Operator '{1}' did not unify with '{2}'", stack->size(), node->nodeID(), op->head()->ToString(), node->task->ToString());

            // Record failure in decomposition tree
            string failReason = "Operator did not unify: " + op->head()->ToString() + " with " + node->task->ToString();
            MarkNodeFailed(planState, node->nodeID(), failReason);

            // Fail this node and backtrack(by returning false)
            Return(planState, false);
            return true;
        }
    }
    else
    {
        return false;
    }
}

bool HtnPlanner::CheckForSpecialTask(PlanState *planState)
{
    // Make the code more readable and get rid of one pointer dereference
    HtnTermFactory *factory = planState->factory;
    shared_ptr<vector<shared_ptr<PlanNode>>> stack = planState->stack;
    
    shared_ptr<PlanNode> node = stack->back();
    if(node->task->name() == "try")
    {
        // We model try() as a node which has two alternative branches: one where its subtasks are run and one where they aren't.
        // We only run the second alternative if the first fails. I.e.:
        //  - If we don't successfully resolve all the try() tasks, backtrack and try again but skipping the clause.
        //  - If the try() tasks do all resolve, we we are done (even if the branch failed after the try())
        // We need to distinguish between failure in the try() tasks and failure in tasks after it
        //    - tryEnd() does this by setting a bit in the try() node that says "At least one made it through"
        //    - So, we give each try() an id, and we add a tryEnd(id) at the end to accomplish this
        // Note: Tree node creation is now handled by CreateTreeNodeForTask at task resolution time

        shared_ptr<vector<shared_ptr<HtnTerm>>> tasks = shared_ptr<vector<shared_ptr<HtnTerm>>>(new vector<shared_ptr<HtnTerm>>());
        tasks->insert(tasks->begin(), node->task->arguments().begin(), node->task->arguments().end());
        tasks->push_back(factory->CreateFunctor("tryEnd", { factory->CreateConstant(lexical_cast<string>(node->nodeID()))}));
        Trace0("TRY        ", "", stack->size());

        // try() pushes a node because it needs a chance to backtrack if the branch fails
        node->SearchNextNodeBacktrackable(planState, *tasks, PlanNodeContinuePoint::ReturnFromHandleTryTerm);

        // Set the retryIfNoSolutions bit on this node.  tryEnd() will set to false if we get there
        node->retry = true;
        return true;
    }
    else if(node->task->name() == "tryEnd")
    {
        // tryEnd() is a system bookkeeping task which marks the end of a try clause.
        // Resolving a tryEnd() means we made it through the try() clause successfully
        int tryNodeID = lexical_cast<int>(node->task->arguments()[0]->name());

        // Tell the try() clause not to retry by finding the node that represents it and marking it
        FindNodeWithID(*stack, tryNodeID)->retry = false;

#ifdef INDHTN_TREE_SIBLING_TRACKING
        // Pop the sibling scope for the try() subtasks now that they're complete.
        // This ensures remaining tasks (siblings of the try()) use the correct outer scope.
        // The scope was pushed when try() expanded to [subtasks, tryEnd].
        // Now that tryEnd is reached, that scope is exhausted.
        node->popSiblingScopeIfMatches(tryNodeID);
#endif

        // Get the next task, no node is pushed because we were just doing bookkeeping
        node->continuePoint = PlanNodeContinuePoint::NextTask;
        return true;
    }
    else if(node->task->name() == "methodScopeEnd")
    {
        // methodScopeEnd is a bookkeeping task that marks the end of a method's subtasks.
        // When we encounter this, all subtasks from the method are done, and we're about
        // to process tasks from the outer (parent) scope.
        int scopeNodeID = lexical_cast<int>(node->task->arguments()[0]->name());

#ifdef INDHTN_TREE_SIBLING_TRACKING
        // Pop the sibling scope for this method's subtasks.
        // This ensures subsequent tasks (from parent scope) get the correct tree parent.
        node->popSiblingScopeIfMatches(scopeNodeID);
#endif

        // Get the next task, no node is pushed because we were just doing bookkeeping
        node->continuePoint = PlanNodeContinuePoint::NextTask;
        return true;
    }
    else if(node->task->name() == "countAnyOf")
    {
        // countAnyOf(nodeID) is a bookkeeping task that increments a count on an anyOf node to indicate that one of the conditions resolved
        // Analogous to the way tryEnd() works
        int anyOfNodeID = lexical_cast<int>(node->task->arguments()[0]->name());
        FindNodeWithID(*stack, anyOfNodeID)->tryAnyOfSuccessCount++;
        
        // Get the next task, no node is pushed because we were just doing bookkeeping
        node->continuePoint = PlanNodeContinuePoint::NextTask;
        return true;
    }
    else if(node->task->name() == "failIfNoneOf")
    {
        // failIfNoneOf is a bookkeeping task also used to implement anyOf
        // If none of the countAnyOf() clauses succeeded, then this clause fails since none of the conditions resolved
        int anyOfNodeID = lexical_cast<int>(node->task->arguments()[0]->name());
        if(FindNodeWithID(*stack, anyOfNodeID)->tryAnyOfSuccessCount == 0)
        {
            Trace0("FAIL       ", "AnyOf had zero solutions", stack->size());
            Return(planState, false);
        }
        else
        {
            // There was at least one solution.
            // Get the next task, no node is pushed because we were just doing bookkeeping
            node->continuePoint = PlanNodeContinuePoint::NextTask;
        }
        return true;
    }
    else if(node->task->name() == "parallel")
    {
        // parallel(task1, task2, ...) expands to:
        // [beginParallel(scopeID), task1, task2, ..., endParallel(scopeID), remaining tasks...]
        // Planning proceeds sequentially, but markers allow post-processing to identify parallel scopes

        shared_ptr<vector<shared_ptr<HtnTerm>>> expandedTasks(
            new vector<shared_ptr<HtnTerm>>());

        // Use current node's ID as scope ID for the parallel block
        int scopeID = node->nodeID();

        // Add beginParallel marker
        expandedTasks->push_back(factory->CreateFunctor("beginParallel",
            { factory->CreateConstant(lexical_cast<string>(scopeID)) }));

        // Add all subtasks from parallel(task1, task2, ...)
        for(auto& subtask : node->task->arguments())
        {
            expandedTasks->push_back(subtask);
        }

        // Add endParallel marker
        expandedTasks->push_back(factory->CreateFunctor("endParallel",
            { factory->CreateConstant(lexical_cast<string>(scopeID)) }));

        // Append remaining tasks (node->tasks already excludes the current parallel() task)
        if(node->tasks->size() > 0)
        {
            expandedTasks->insert(expandedTasks->end(),
                node->tasks->begin(), node->tasks->end());
        }

        Trace0("PARALLEL   ", "", stack->size());

        // Replace current task list with expanded tasks and continue
        // Don't use SearchNextNode because it would prepend to existing tasks,
        // leaving the parallel() term to be re-processed
        node->tasks = expandedTasks;
        node->continuePoint = PlanNodeContinuePoint::NextTask;
        return true;
    }
    else if(node->task->name() == "beginParallel" ||
            node->task->name() == "endParallel")
    {
        // These are bookkeeping markers - add to operators list for post-processing
        // but don't execute any state changes
        node->AddToOperators(node->task);

        // Get the next task, no node is pushed because we were just doing bookkeeping
        node->continuePoint = PlanNodeContinuePoint::NextTask;
        return true;
    }

    return false;
}

void HtnPlanner::ClearAll()
{
    for(auto op : m_operators)
    {
        m_dynamicSize -= op.second->dynamicSize();
        delete op.second;
    }
    m_operators.clear();

    for(auto method : m_methods)
    {
        m_dynamicSize -= method.second->dynamicSize();
        delete method.second;
    }
    m_methods.clear();
}

// Needs to return methods in the order they were entered into the file so that else clauses will work properly and so that rules get executed
// in the proper order so the best solution is first
shared_ptr<vector<pair<HtnMethod *, UnifierType>>> HtnPlanner::FindAllMethodsThatUnify(HtnTermFactory *termFactory, HtnRuleSet *prog, shared_ptr<HtnTerm> goal)
{
    shared_ptr<vector<pair<HtnMethod *, UnifierType>>> foundMethods = shared_ptr<vector<pair<HtnMethod *, UnifierType>>>(new vector<pair<HtnMethod *, UnifierType>>());
    for(map<HtnTerm::HtnTermID, HtnMethod *>::iterator iter = m_methods.begin(); iter != m_methods.end(); ++iter)
    {
        shared_ptr<UnifierType> sub = HtnGoalResolver::Unify(termFactory, iter->second->head(), goal);
        
        if(sub != nullptr)
        {
            foundMethods->push_back(pair<HtnMethod *, UnifierType>(iter->second, *sub));
        }
    }
    
    // Now sort the vector so the first rules are first in the list
    std::sort(foundMethods->begin(), foundMethods->end(), MethodComparer);
    return foundMethods;
}

shared_ptr<PlanNode> HtnPlanner::FindNodeWithID(vector<shared_ptr<PlanNode>> &stack, int id)
{
    for(vector<shared_ptr<PlanNode>>::iterator iter = stack.begin(); iter != stack.end(); ++iter)
    {
        if((*iter)->nodeID() == id)
        {
            return *iter;
        }
    }
    
    StaticFailFastAssertDesc(false, "Internal Error");
    return nullptr;
}

/*
 Definitions:
 From Prolog / First order logic
 - Term: The basic building block we use. Same as a Prolog term
    - has a name and zero or more arguments, which can themselves be terms.
 - Constant: A statement about something true in the world
    - Is a single term
 - Axiom: Declares that things are logically equivalent
    - has a head and a set of Terms.  The head and the Terms are equivalent
 - Variable: Used when running queries. Replace a term argument with a variable to ask a question of a set of Axioms and Constants
 - Ground Term: if a Term has no variables, it is considered "Ground"

 From Hierarchical Task Networks
 - Task: Declares that something needs to be *done*. It can be Primitive: it can be done simply by modifying state in the world with no further processing, or Compound: It must be further refined in order to be accomplished in the state
    - Has a Name, and a set of Terms
 - Operator: Describes how to accomplish a Primitive Task.
    - Has a Head which is a Primitive Task, a list of State to delete, and a list of State to Add. When executed, it changes the state of the world via its adds and deletes.
    - The Head of an operator uniquely defines the operator.  You can't have multiple operators with the same name
    - In order for a Task to match an operator, all the terms resulting from the unification of the two must be ground
 - Method: Describes how to refine a Compound Task.
    - has a Head which is a Compound Task, a Condition which must be true for it to work, and a list of Tasks (either Primitive or Compound) which, once refined or executed, will accomplish that Task
 - State: The collection of Constants and Axioms that are true about the world. Sometimes called Program in my code since Prolog uses that term
 - Domain: The collection of Methods and Operators used for the planning problem
 - Tasks: The collection of Tasks which need to be accomplished for the planning problem. Sometimes called goals
 - Planning Problem: A triple of State, Domain and Tasks which defines the entire planning problem
 - Plan: The final output of the algorithm is a Plan, which is a list of Operators which, once executed, solve the tasks. Specifically, it is a list of the Heads of the Operators (since that uniquely defines them)

 Assumptions:
 - Operators and Methods cannot share names.  Operators name will always shadow a Method name

 Algorithm:
    PlanList FindPlan(TaskList, State, Domain):
        - Get the first task off the list
        - If the task list is empty, this is a leaf node, return the solution that has built up
        - If the task name is an operator name and the task and operator head unify to ground it is a successful resolution.
            - Add the operators to the Plan
            - Modify the state as per the operator
            - FindPlan() the remaining task list
        - If the task name is a method name it may create multiple alternative branches to explore. Each branch represents a *different* solution
            - Find each Method head that Task can unify with
            - Take the unification result and apply it to the Method's Condition
            - Finally, Resolve the Condition: i.e. apply axioms to the Condition until it is "resolved" to a set of Constants (rules that are true about the world)
                - Because Axioms can contain variables, it is possible that there is more than one resolution
                - If there are > 0 resolutions, it is a successful resolution and ALL resolutions are returned. Each resolution represents a *different* solution
            - Go through each method/Resolution pair that got generated
                - Apply any unifications from the head and the resolution to the task list for the method
                - Add these tasks to the *beginning* of the task list
                - FindPlan() the new task list
        - If the task doesn't bind with anything return FAIL
 
        NOTE: Based on the above, there are two ways you can get multiple solutions back: if there are multiple methods that bind to a task and if a method condition returns multiple answers when resolved

This implementation has extensions that behave differently.  Certain types of nodes don't do the default behavior of simply searching the tree and returning:
- Arithmetic rules simply resolve immediately
- try() simply ignores failure in the do() clause which could be modelled as a special kind of node that returns success even if it fails
- AnyOf and AllOf modify how a Method handles method resolution. Instead of treating resolutions as separate solutions, they treat them as a single solution.
    - AllOf simply adds all resolutions as additional tasks and thus fails if any fails
    - AnyOf succeeds as long as one succeeds
- else Methods are only run if the rule before it fails.  There can be multiple else clauses.
 */

shared_ptr<HtnPlanner::SolutionType> HtnPlanner::FindPlan(HtnTermFactory *factory, shared_ptr<HtnRuleSet> initialState, vector<shared_ptr<HtnTerm>> &initialGoals, int memoryBudget)
{
    Trace1("FINDPLAN   ", "Goals:{0}", 0, HtnTerm::ToString(initialGoals));
    shared_ptr<PlanState> planState = shared_ptr<PlanState>(new PlanState(factory, initialState, initialGoals, memoryBudget));
    shared_ptr<HtnPlanner::SolutionType> solution = FindNextPlan(planState.get());
    Trace3("END        ", "Solution:'{0}', HighestMemory:{1}, ElapsedTime{2}", 0, HtnPlanner::ToStringSolution(solution), planState->highestMemoryUsed, lexical_cast<string>(solution == nullptr ? -1 : solution->elapsedSeconds));
    return solution;
}

shared_ptr<HtnPlanner::SolutionsType> HtnPlanner::FindAllPlans(HtnTermFactory *factory, shared_ptr<HtnRuleSet> initialState, const vector<shared_ptr<HtnTerm>> &initialGoals, int memoryBudget,
                                                               int64_t *highestMemoryUsedReturn, int *furthestFailureIndex, std::vector<std::shared_ptr<HtnTerm>> *furthestFailureContext)
{
    Trace1("ALL BEGIN  ", "Goals:{0}", 0, HtnTerm::ToString(initialGoals));
    shared_ptr<HtnPlanner::SolutionsType> finalSolutions;
    shared_ptr<PlanState> planState = shared_ptr<PlanState>(new PlanState(factory, initialState, initialGoals, memoryBudget));
    Trace0("BEGIN      ", "Find next plan", 0);
    shared_ptr<HtnPlanner::SolutionType> nextSolution = FindNextPlan(planState.get());
    while(nextSolution != nullptr)
    {
        if(finalSolutions == nullptr)
        {
            finalSolutions = shared_ptr<HtnPlanner::SolutionsType>(new HtnPlanner::SolutionsType());
        }
        finalSolutions->push_back(nextSolution);
        Trace4("END        ", "Solution:'{0}', Budget:{1}, HighestMemory:{2}, ElapsedTime{3}", 0, HtnPlanner::ToStringSolution(nextSolution), memoryBudget, planState->highestMemoryUsed, lexical_cast<string>(nextSolution == nullptr ? -1 : nextSolution->elapsedSeconds));
        
        if(planState->factory->outOfMemory())
        {
            // If we ran out of memory getting that solution, abort afterward
            // The caller can decide whether to ignore the partial solution or not
            break;
        }

        Trace0("BEGIN      ", "Find next plan", 0);
        nextSolution = FindNextPlan(planState.get());
    }
    
    if(highestMemoryUsedReturn != nullptr)
    {
        *highestMemoryUsedReturn = planState->highestMemoryUsed;
    }
    
    if(finalSolutions == nullptr)
    {
        // There were no solutions, set the error
        if(furthestFailureIndex != nullptr)
        {
            *furthestFailureIndex = planState->deepestTaskFailure;
        }
        
        if(furthestFailureContext != nullptr)
        {
            *furthestFailureContext = planState->furthestCriteriaFailureContext;
        }
    }
    
    Trace3("ALL END    ", "Solution:'{0}', Budget:{1}, HighestMemory:{2}", 0, HtnPlanner::ToStringSolutions(finalSolutions), memoryBudget, planState->highestMemoryUsed);
    return finalSolutions;
}

// Finds the next solution to the planning problem represented by planState and returns it (or null if there are none)
// Updates planState so it can be called over and over to get more solutions
// Since this is a depth first search, every node is responsible for resolving a single task and then passing the rest to a child to resolve
// The only exception to this is "bookkeeping" tasks like countAnyOf() that don't actually contribute to the solution. They may iterate through a few bookkeeping tasks in the same node
// Implementation Notes: This function has been written to avoid recursion since plans can recurse quite deeply and stacks are often *way* more limited in space than the heap. This also makes it easier
// to track how much memory we are using. This also means it avoids declaring any stack based variables that aren't trivial. It puts everything on the heap.
// If the program memory goes over the budget, we set the factory->outOfMemory() bit and return the current partial solution
shared_ptr<HtnPlanner::SolutionType> HtnPlanner::FindNextPlan(PlanState *planState)
{
    // Make the code more readable and get rid of one pointer dereference
    HtnTermFactory *factory = planState->factory;
    int64_t &memoryBudget = planState->memoryBudget;
    bool &returnValue = planState->returnValue;
    shared_ptr<vector<shared_ptr<PlanNode>>> stack = planState->stack;
    planState->startTimeSeconds = HighPerformanceGetTimeInSeconds();
    while(stack->size() > 0)
    {
        shared_ptr<PlanNode> node = stack->back();
        PlanNodeContinuePoint continuePoint = node->continuePoint;
        if(HtnPlanner::m_abort)
        {
            continuePoint = PlanNodeContinuePoint::Abort;
        }
        
        switch(continuePoint)
        {
            case PlanNodeContinuePoint::Fail:
            {
                FailFastAssertDesc(false, "Internal Error");
            }
            break;
                
            case PlanNodeContinuePoint::Abort:
            {
                Trace0("PARTIAL    ", "***** Aborted", stack->size());

                // Don't allow to continue since we can't guarantee the tree is correct still
                node->continuePoint = PlanNodeContinuePoint::Fail;
                return SolutionFromCurrentNode(planState, node);
            }
            break;
                
            case PlanNodeContinuePoint::OutOfMemory:
            {
                // Only happens when a new node is pushed and we detect we are out of memory
                Trace2("PARTIAL    ", "***** Out Of Memory: Current:{0}, Budget:{1}", stack->size(), planState->dynamicSize(), planState->memoryBudget);
                node->continuePoint = PlanNodeContinuePoint::NextTask;
                factory->outOfMemory(true);
                
                // Don't allow to continue since we can't guarantee the tree is correct still
                node->continuePoint = PlanNodeContinuePoint::Fail;
                return SolutionFromCurrentNode(planState, node);
            }
            break;
                
            case PlanNodeContinuePoint::NextTask:
            {
                // Grab the next task off the current node list and remove it
                node->SetNodeTask();


                if(node->task == nullptr)
                {
                    // There are no more tasks, we have found a leaf and a solution
                    Trace4("SUCCESS    ", "nodeID:{0} no tasks remain. Memory: Current:{1}, Highest:{2}, Budget:{3}", stack->size(), node->nodeID(), planState->dynamicSize(), planState->highestMemoryUsed, planState->memoryBudget);

                    // Mark success path in decomposition tree (must be done before Return() unwinds stack)
                    MarkPathSuccess(planState, node->nodeID());

                    // Start undoing the recursion so we can find the next solution next time
                    Return(planState, true);

                    return SolutionFromCurrentNode(planState, node);
                }
                else
                {
                    // Resolve any arithmetic parts of it
                    node->task = node->task->ResolveArithmeticTerms(factory);

                    // Create tree node at task resolution time - sibling scope is now correct
                    CreateTreeNodeForTask(planState, node.get());

                    Trace3("SOLVE      ", "nodeID:{0} task:'{1}' remaining:'{2}'", stack->size(), node->nodeID(), node->task->ToString(), HtnTerm::ToString(*node->tasks));

                    // Is it an operator?
                    if(CheckForOperator(planState))
                    {
                        continue;
                    }
                    else if(CheckForSpecialTask(planState))
                    {
                        continue;
                    }
                    else
                    {
                        // No operators or special tasks, so try methods
                        node->unifiedMethods = FindAllMethodsThatUnify(factory, node->state.get(), node->task);
                        if(node->unifiedMethods->size() == 0)
                        {
                            Trace2("FAIL       ", "nodeID:{0} No methods unify with '{1}'", stack->size(), node->nodeID(), node->task->ToString());
                            Return(planState, false);
                            continue;
                        }
                        else
                        {
                            Trace3("           ", "nodeID:{0} {1} methods unify with '{2}'", stack->size(), node->nodeID(), node->unifiedMethods->size(), node->task->ToString());

                            // Each method that unifies represents a branch of the tree that could be an alternative solution
                            // So we iterate through them
                            node->continuePoint = PlanNodeContinuePoint::NextMethodThatApplies;
                            continue;
                        }
                    }
                }
            }
            break;
                
            // Explore all the alternative methods that the task unifies with
            case PlanNodeContinuePoint::NextMethodThatApplies:
            {
                node->SetNextMethodThatUnifies();
                
                // Skip past any consecutive else clauses if we've already found a solution
                // before them in the file
                if(node->methodHadSolution)
                {
                    // Remember this so we know whether to return
                    node->atLeastOneMethodHadSolution = true;
                    
                    // This assumes that methods are sorted in the order they were entered in the file
                    while(node->method.first != nullptr && node->method.first->isDefault())
                    {
                        Trace1("           ", "skipping else method '{0}'", stack->size(), node->method.first->ToString());
                        node->SetNextMethodThatUnifies();
                    }
                    
                    // reset after we skip else clauses so we can interleave if() else() if() else()
                    node->methodHadSolution = false;
                }
                
                // If there are no more methods that apply, returns true if we found at least one solution among the alternatives
                if(node->method.first == nullptr)
                {
                    Return(planState, node->atLeastOneMethodHadSolution);
                    continue;
                }
                else
                {
                    Trace3("METHOD     ", "nodeID:{0} resolve next{1} method '{2}'", stack->size(), node->nodeID(), (node->method.first->isDefault() ? " ELSE" : ""), node->method.first->ToString());

                    // Record method choice in decomposition tree
                    RecordMethodChoice(planState, node->nodeID(), node->method.first, node->method.second);

                    // See if the constraints are met for this method by applying the unifier above to the constraint and then seeing if it is satisfied by the current
                    // state (meaning reducing it returns only ground state)
                    shared_ptr<vector<shared_ptr<HtnTerm>>> substitutedCondition;
                    std::vector<std::shared_ptr<HtnTerm>> farthestCriteriaFailureContext;
                    int furthestCriteriaFailureIndex = -1;
                    if(node->method.first->condition().size() == 0)
                    {
                        // Empty condition, resolves to ground by definition
                        node->conditionResolutions = shared_ptr<vector<UnifierType>>(new vector<UnifierType>());
                        node->conditionResolutions->push_back(UnifierType());
                    }
                    else
                    {
                        // Find all of the ways the constraints are met
                        substitutedCondition = HtnGoalResolver::SubstituteUnifiers(factory, node->method.second, node->method.first->condition());
                        Trace3("           ", "nodeID:{0} substituted condition:'{1}' with unifier '{2}'", stack->size(), node->nodeID(), HtnTerm::ToString(*substitutedCondition), HtnGoalResolver::ToString(node->method.second));

                        // Subtract off current memory usage from budget to tell Resolve how much it has to work with
                        int64_t currentMemory = planState->dynamicSize();
                        int64_t resolverMemory = 0;
                        node->conditionResolutions = m_resolver->ResolveAll(factory, node->state.get(), *substitutedCondition, (int) (stack->size() + 1), (int) (memoryBudget - currentMemory),
                                                                            &resolverMemory, &furthestCriteriaFailureIndex, &farthestCriteriaFailureContext);
                        planState->CheckHighestMemory(currentMemory + resolverMemory, "Resolver", resolverMemory);
                        if(factory->outOfMemory())
                        {
                            node->continuePoint = PlanNodeContinuePoint::OutOfMemory;
                            continue;
                        }
                    }
                    
                    if(node->conditionResolutions == nullptr)
                    {
                        // Constraints are not met for this method, try the next one
                        Trace2("FAIL       ", "nodeID:{0} 0 condition alternatives for method '{1}'", stack->size(), node->nodeID(), node->method.first->ToString());
                        Trace1("           ", "substituted condition '{0}'", stack->size(), HtnTerm::ToString(*substitutedCondition));
                        node->continuePoint = PlanNodeContinuePoint::NextMethodThatApplies;

                        // Record failure in decomposition tree with structured term info
                        string failReason = "Condition failed: " + HtnTerm::ToString(*substitutedCondition);
                        shared_ptr<HtnTerm> failedTerm = nullptr;
                        if(furthestCriteriaFailureIndex >= 0 &&
                           furthestCriteriaFailureIndex < (int)substitutedCondition->size()) {
                            failedTerm = (*substitutedCondition)[furthestCriteriaFailureIndex];
                        }
                        MarkNodeFailed(planState, node->nodeID(), failReason, furthestCriteriaFailureIndex, failedTerm);

                        // Remember the failure context if this is deepest
                        planState->RecordFailure(furthestCriteriaFailureIndex, farthestCriteriaFailureContext);
                        continue;
                    }
                    else
                    {
                        Trace2("           ", "{0} condition alternatives for method '{1}'", stack->size(), node->conditionResolutions->size(), node->method.first->ToString());
                        if(node->method.first->methodType() == HtnMethodType::Normal)
                        {
                            // Every resolution is treated as a potential separate solution
                            node->continuePoint = PlanNodeContinuePoint::NextNormalMethodCondition;
                        }
                        else if(node->method.first->methodType() == HtnMethodType::AnySetOf)
                        {
                            // All of the resolutions are each wrapped in try() and merged together into a single solution. If at least one resolution succeeds, it succeeds
                            HandleAnyOf(planState);
                            continue;
                        }
                        else if(node->method.first->methodType() == HtnMethodType::AllSetOf)
                        {
                            // All of the resolutions are merged together into a single solution. They must all succeed.
                            HandleAllOf(planState);
                            continue;
                        }
                        else
                        {
                            // There should be no other method types
                            FailFastAssertDesc(false, "Internal Error");
                            continue;
                        }
                    }
                    
                    continue;
                }
            }
            break;
                
            // Treat each condition as a separate solution
            case PlanNodeContinuePoint::NextNormalMethodCondition:
            {
                node->SetNextCondition();
                UnifierType *condition = node->condition();
                if(condition == nullptr)
                {
                    // No more conditions, try the next method
                    node->continuePoint = PlanNodeContinuePoint::NextMethodThatApplies;
                    continue;
                }
                else
                {
                    Trace2("           ", "nodeID:{0} condition:'{1}'", stack->size(), node->nodeID(), HtnGoalResolver::ToString(*condition));

                    // Record condition bindings in decomposition tree
                    RecordConditionBindings(planState, node->nodeID(), *condition);

                    // First bind the variables from the method head to the subtasks
                    shared_ptr<vector<shared_ptr<HtnTerm>>> headBoundSubtasks = HtnGoalResolver::SubstituteUnifiers(factory, node->method.second, node->method.first->tasks());

                    // Then bind the variables from the condition to the subtasks
                    shared_ptr<vector<shared_ptr<HtnTerm>>> boundSubtasks = HtnGoalResolver::SubstituteUnifiers(factory, *condition, *headBoundSubtasks);

                    // Create a node by adding the subtasks from this method/condition combination and recurse
                    // Make it backtrackable so we can try alternatives without the state being changed by other solutions
                    shared_ptr<HtnRuleSet> stateCopy = node->state->CreateCopy();
                    node->SearchNextNodeBacktrackable(planState, *boundSubtasks, PlanNodeContinuePoint::ReturnFromNextNormalMethodCondition);
                    continue;
                }
            }
            break;
                
            case PlanNodeContinuePoint::ReturnFromNextNormalMethodCondition:
            {
                if(returnValue == true)
                {
                    // Found a solution!
                    node->methodHadSolution = true;
                }
                
                // Try the next condition
                node->continuePoint = PlanNodeContinuePoint::NextNormalMethodCondition;
                continue;
            }
            break;
                
            case PlanNodeContinuePoint::ReturnFromCheckForOperator:
            {
                // Since this is an operator, there are no alternatives to explore so we always just continue to return
                // whatever the child said
                Return(planState, returnValue);
                continue;
            }
            break;
                
            case PlanNodeContinuePoint::ReturnFromHandleTryTerm:
            {
                // If no solutions were generated and we didn't get past the try() clause, try again but
                // skip the try clause this time
                if(returnValue == false && node->retry)
                {
                    Trace1("IGNORE     ", "Ignore and skip TRY tasks: '{0}'", stack->size(), HtnTerm::ToString(node->task->arguments()));

#ifdef INDHTN_TREE_SIBLING_TRACKING
                    // Pop the sibling scope that was pushed when try() expanded.
                    // The success path pops this in tryEnd, but failure path must also clean up.
                    node->popSiblingScopeIfMatches(node->nodeID());
#endif

                    // Ignore the try() node by skipping to the next task, no node is pushed because we are changing what the current task is for this node
                    node->continuePoint = PlanNodeContinuePoint::NextTask;
                    continue;
                }
                
                // If we made it past the try() clause (even if we didn't ultimately find a solution), we don't retry and we just return whatever happened
                Return(planState, returnValue);
                continue;
            }
            break;
                
            case PlanNodeContinuePoint::ReturnFromSetOfConditions:
            {
                if(returnValue == true)
                {
                    // Found a solution to either an anyOf or allOf node.
                    node->methodHadSolution = true;
                }
                
                // Try the next method
                node->continuePoint = PlanNodeContinuePoint::NextMethodThatApplies;
                continue;
            }
            break;
        }
    }
    
    return nullptr;
}

bool HtnPlanner::HasOperator(const string &head, const string &deletions, const string &additions)
{
    string composed = head + " => del(" + deletions + "), add(" + additions + ")";
    string justTheName = head.substr(0, head.find("("));
    OperatorsType::iterator  iter = m_operators.find(justTheName);
    if(iter != m_operators.end())
    {
        string item = iter->second->ToString();
        return item == composed;
    }
    else
    {
        return false;
    }
}

bool HtnPlanner::DebugHasMethod(const string &head, const string &constraints, const string &tasks)
{
    string composed = head + " => if(" + constraints + "), do(" + tasks + ")";
    
    for(auto method : m_methods)
    {
        if(composed == method.second->ToString())
        {
            return true;
        }
    }
    
    return false;
}

// All of the resolutions are merged together into a single solution. They must all succeed.
void HtnPlanner::HandleAllOf(PlanState *planState)
{
    // Make the code more readable and get rid of one pointer dereference
    HtnTermFactory *factory = planState->factory;
    shared_ptr<vector<shared_ptr<PlanNode>>> stack = planState->stack;
    
    shared_ptr<PlanNode> node = stack->back();
    shared_ptr<vector<shared_ptr<HtnTerm>>> combinedSubtasks = shared_ptr<vector<shared_ptr<HtnTerm>>>(new vector<shared_ptr<HtnTerm>>());
    for(auto condition : *node->conditionResolutions)
    {
        // First bind the variables from the method head to the subtasks
        shared_ptr<vector<shared_ptr<HtnTerm>>> headBoundSubtasks = HtnGoalResolver::SubstituteUnifiers(factory, node->method.second, node->method.first->tasks());
        
        // Then bind the variables from the condition to the subtasks
        shared_ptr<vector<shared_ptr<HtnTerm>>> boundSubtasks = HtnGoalResolver::SubstituteUnifiers(factory, condition, *headBoundSubtasks);
        
        // Then combine these with the other conditions
        combinedSubtasks->insert(combinedSubtasks->end(), boundSubtasks->begin(), boundSubtasks->end());
    }
    
    // Nothing special needs to be done to track success here because the default behavior of our depth first search is that all tasks in the list
    // must find a solution or the branch fails, which is the behavior that we want.
    
    // Finally Create a node by adding the subtasks from all of the conditions at once and recurse using a copy of current state so we can backtrack
    Trace1("ALLOF      ", "Treat ALL method condition alternatives as new tasks", stack->size(), HtnTerm::ToString(*combinedSubtasks));
    node->SearchNextNodeBacktrackable(planState, *combinedSubtasks, PlanNodeContinuePoint::ReturnFromSetOfConditions);
}

// All of the resolutions are each wrapped in try() and merged together into a single solution. If at least one resolution succeeds, it succeeds
void HtnPlanner::HandleAnyOf(PlanState *planState)
{
    // Make the code more readable and get rid of one pointer dereference
    HtnTermFactory *factory = planState->factory;
    int &nextNodeID = planState->nextNodeID;
    shared_ptr<vector<shared_ptr<PlanNode>>> stack = planState->stack;
    
    shared_ptr<PlanNode> node = stack->back();
    shared_ptr<vector<shared_ptr<HtnTerm>>> combinedSubtasks = shared_ptr<vector<shared_ptr<HtnTerm>>>(new vector<shared_ptr<HtnTerm>>());
    
    // Because we want to ignore failure, but succeed the whole group only if at least one condition succeeds.
    // We take advantage of the fact that we're doing a depth-first search, and thus we can just add bookkeeping tasks into the task list to do the work.
    // First, wrap each condition with a try() term and put a countAnyOf(anyOfNodeID) term as the last part of the try() condition.
    // This which makes sure the anyOf node is aware if a single try() clause succeeds.
    // Then, follow the whole group of try() clauses by failIfNoneOf(anyOfNodeID) which will fail if none of them succeeded
    int anyOfNodeID = nextNodeID;
    for(auto condition : *node->conditionResolutions)
    {
        // First bind the variables from the method head to the subtasks
        shared_ptr<vector<shared_ptr<HtnTerm>>> headBoundSubtasks = HtnGoalResolver::SubstituteUnifiers(factory, node->method.second, node->method.first->tasks());
        
        // Then bind the variables from the condition to the subtasks
        shared_ptr<vector<shared_ptr<HtnTerm>>> boundSubtasks = HtnGoalResolver::SubstituteUnifiers(factory, condition, *headBoundSubtasks);
        
        // And add an countAnyOf() after so we count if it succeded
        boundSubtasks->push_back(factory->CreateFunctor("countAnyOf", { factory->CreateConstant(lexical_cast<string>(anyOfNodeID)) }));
        
        // Then wrap them in try
        combinedSubtasks->push_back(factory->CreateFunctor("try", *boundSubtasks));
    }
    
    // Then add a final check at the end to make sure at least one of the try() blocks worked
    combinedSubtasks->push_back(factory->CreateFunctor("failIfNoneOf", { factory->CreateConstant(lexical_cast<string>(anyOfNodeID)) }));
    
    // Here is where we track how many succeeded
    node->tryAnyOfSuccessCount = 0;
    
    Trace1("ANYOF      ", "Treat ALL method condition alternatives as new tasks", stack->size(), HtnTerm::ToString(*combinedSubtasks));
    
    // Recurse with the combined set of conditions added to the task list, and using a copy of current state so we can try alternatives without
    // tainted state
    node->SearchNextNodeBacktrackable(planState, *combinedSubtasks, PlanNodeContinuePoint::ReturnFromSetOfConditions);
}

void HtnPlanner::Return(PlanState *planState, bool returnValue)
{
    shared_ptr<PlanNode> node = planState->stack->back();
    Trace2("POP        ", "nodeID:{0} returnValue:{1}", planState->stack->size(), node->nodeID(), returnValue);
    planState->stack->pop_back();
    planState->returnValue = returnValue;
}

shared_ptr<HtnPlanner::SolutionType> HtnPlanner::SolutionFromCurrentNode(PlanState *planState, shared_ptr<PlanNode> node)
{
    shared_ptr<HtnPlanner::SolutionType> solution = shared_ptr<HtnPlanner::SolutionType>(new HtnPlanner::SolutionType());
    if(node->operators != nullptr)
    {
        solution->first = *node->operators;
    }

    solution->second = node->state;

    // Copy only the nodes that belong to this solution (solutionID was set in MarkPathSuccess)
    // currentSolutionID was incremented after marking, so use currentSolutionID - 1
    int thisSolutionID = planState->currentSolutionID - 1;
    for(const auto& treeNode : planState->decompositionTree)
    {
        if(treeNode.solutionID == thisSolutionID)
        {
            solution->decompositionTree.push_back(treeNode);
        }
    }

    // Now roll up all the stats
    solution->highestMemoryUsed = planState->highestMemoryUsed;
    solution->elapsedSeconds = HighPerformanceGetTimeInSeconds() - planState->startTimeSeconds;
    return solution;
}

string HtnPlanner::ToStringFacts(shared_ptr<SolutionType> solution)
{
    if(solution == nullptr)
    {
        return "null";
    }
    else
    {
        return solution->second->ToStringFacts();
    }
}

string HtnPlanner::ToStringFacts(shared_ptr<SolutionsType> solutions)
{
    if(solutions == nullptr)
    {
        return "null";
    }
    else
    {
        stringstream result;
        result << "[ ";
        for(shared_ptr<SolutionType> solution : *solutions)
        {
            result << "{ " + ToStringFacts(solution) + " } ";
        }
        result << "]";
        
        return result.str();
    }
}

string HtnPlanner::ToStringSolution(shared_ptr<SolutionType> solution, bool json)
{
    if(solution == nullptr)
    {
        return json ? "" : "null";
    }
    else
    {
        return HtnTerm::ToString(solution->first, json ? false : true, json);
    }
}

string HtnPlanner::ToStringSolutions(shared_ptr<SolutionsType> solutions, bool json)
{
    if(solutions == nullptr)
    {
        return json ? "" : "null";
    }
    else
    {
        stringstream result;
        result << "[ ";
        bool hasSolution = false;
        for(shared_ptr<SolutionType> solution : *solutions)
        {
            if (json)
            {
                result << (hasSolution ? "," : "") << "[ " + ToStringSolution(solution, true) + " ] ";
            }
            else
            {
                result << "{ " + ToStringSolution(solution) + " } ";
            }
            hasSolution = true;
        }
        result << "]";

        return result.str();
    }
}

// Decomposition tree recording methods

// Helper to convert PlanNode nodeID to the most recent treeNodeID for that node
int HtnPlanner::NodeIDToTreeNodeID(PlanState* planState, int nodeID)
{
    auto it = planState->nodeIDToLastTreeNodeID.find(nodeID);
    if(it != planState->nodeIDToLastTreeNodeID.end()) {
        return it->second;
    }
    return -1;
}

void HtnPlanner::RecordTreeNode(PlanState* planState, int nodeID, int parentID, shared_ptr<HtnTerm> task)
{
    // NOTE: This function is likely obsolete with the new CreateTreeNodeForTask approach.
    // Kept for backward compatibility but may need removal.
    int treeNodeID = planState->nextTreeNodeID++;
    int parentTreeNodeID = (parentID == -1) ? -1 : NodeIDToTreeNodeID(planState, parentID);

    DecompTreeNode node;
    node.treeNodeID = treeNodeID;
    node.nodeID = nodeID;
    node.parentNodeID = parentTreeNodeID;
    node.taskName = task ? task->ToString() : "";
    node.isOperator = false;
    node.isSuccess = false;
    node.isFailed = false;

    size_t index = planState->decompositionTree.size();
    planState->treeNodeIDToTreeIndex[treeNodeID] = index;
    planState->nodeIDToLastTreeNodeID[nodeID] = treeNodeID;
    planState->decompositionTree.push_back(node);

    // Update parent's children list
    if(parentTreeNodeID >= 0) {
        auto parentIt = planState->treeNodeIDToTreeIndex.find(parentTreeNodeID);
        if(parentIt != planState->treeNodeIDToTreeIndex.end()) {
            planState->decompositionTree[parentIt->second].childNodeIDs.push_back(treeNodeID);
        }
    }
}

void HtnPlanner::RecordMethodChoice(PlanState* planState, int nodeID, HtnMethod* method, const UnifierType& unifiers)
{
    int treeNodeID = NodeIDToTreeNodeID(planState, nodeID);
    if(treeNodeID == -1) return;

    auto it = planState->treeNodeIDToTreeIndex.find(treeNodeID);
    if(it != planState->treeNodeIDToTreeIndex.end()) {
        auto& node = planState->decompositionTree[it->second];
        node.methodSignature = method->ToString();
        node.isOperator = false;
        node.methodIndex = method->documentOrder();

        // Store condition terms as structured JSON
        node.conditionTermsJson.clear();
        for(const auto& term : method->condition()) {
            node.conditionTermsJson.push_back(term->ToJson());
        }

        // Clear/reset failure info for new method attempt
        node.failedConditionIndex = -1;
        node.failedConditionTermJson = "";

        node.unifiers.clear();  // Clear old bindings from previous method attempts
        node.conditionBindings.clear();  // Clear old condition bindings
        for(const auto& u : unifiers) {
            node.unifiers.push_back({u.first->ToString(), u.second->ToString()});
        }
    }
}

void HtnPlanner::RecordConditionBindings(PlanState* planState, int nodeID, const UnifierType& condition)
{
    int treeNodeID = NodeIDToTreeNodeID(planState, nodeID);
    if(treeNodeID == -1) return;

    auto it = planState->treeNodeIDToTreeIndex.find(treeNodeID);
    if(it != planState->treeNodeIDToTreeIndex.end()) {
        auto& node = planState->decompositionTree[it->second];
        for(const auto& u : condition) {
            node.conditionBindings.push_back({u.first->ToString(), u.second->ToString()});
        }
    }
}

void HtnPlanner::RecordOperator(PlanState* planState, int nodeID, HtnOperator* op, const UnifierType& unifiers)
{
    int treeNodeID = NodeIDToTreeNodeID(planState, nodeID);
    if(treeNodeID == -1) return;

    auto it = planState->treeNodeIDToTreeIndex.find(treeNodeID);
    if(it != planState->treeNodeIDToTreeIndex.end()) {
        auto& node = planState->decompositionTree[it->second];
        node.operatorSignature = op->head()->ToString();
        node.isOperator = true;
        for(const auto& u : unifiers) {
            node.unifiers.push_back({u.first->ToString(), u.second->ToString()});
        }
    }
}

void HtnPlanner::MarkPathSuccess(PlanState* planState, int leafNodeID)
{
    // Convert PlanNode nodeID to treeNodeID, then walk up the tree
    int currentTreeNodeID = NodeIDToTreeNodeID(planState, leafNodeID);

    // If no tree node for this PlanNode, try to find via bookkeeping parents
    while(currentTreeNodeID == -1 && leafNodeID >= 0) {
        auto bookkeepIt = planState->bookkeepingParents.find(leafNodeID);
        if(bookkeepIt != planState->bookkeepingParents.end()) {
            leafNodeID = bookkeepIt->second;
            currentTreeNodeID = NodeIDToTreeNodeID(planState, leafNodeID);
        } else {
            // Try stack
            bool found = false;
            for(int i = (int)planState->stack->size() - 1; i >= 0; i--) {
                if((*planState->stack)[i]->nodeID() == leafNodeID && i > 0) {
                    leafNodeID = (*planState->stack)[i - 1]->nodeID();
                    currentTreeNodeID = NodeIDToTreeNodeID(planState, leafNodeID);
                    found = true;
                    break;
                }
            }
            if(!found) break;
        }
    }

    // Walk up from leaf to root, marking all nodes as successful
    while(currentTreeNodeID >= 0) {
        auto it = planState->treeNodeIDToTreeIndex.find(currentTreeNodeID);
        if(it == planState->treeNodeIDToTreeIndex.end()) {
            break;
        }
        auto& node = planState->decompositionTree[it->second];
        node.isSuccess = true;
        node.solutionID = planState->currentSolutionID;

#ifdef INDHTN_TREE_SIBLING_TRACKING
        // Recursively mark all descendants
        std::function<void(int)> markDescendants = [&](int treeNodeID) {
            auto nodeIt = planState->treeNodeIDToTreeIndex.find(treeNodeID);
            if(nodeIt == planState->treeNodeIDToTreeIndex.end()) return;
            auto& descendant = planState->decompositionTree[nodeIt->second];
            descendant.isSuccess = true;
            descendant.solutionID = planState->currentSolutionID;
            for(int childTreeNodeID : descendant.childNodeIDs) {
                markDescendants(childTreeNodeID);
            }
        };
        for(int childTreeNodeID : node.childNodeIDs) {
            markDescendants(childTreeNodeID);
        }
#endif

        currentTreeNodeID = node.parentNodeID;  // parentNodeID is now treeNodeID of parent
    }
    planState->currentSolutionID++;
}

void HtnPlanner::MarkNodeFailed(PlanState* planState, int nodeID, const string& reason, int failedIndex, shared_ptr<HtnTerm> failedTerm)
{
    int treeNodeID = NodeIDToTreeNodeID(planState, nodeID);
    if(treeNodeID == -1) return;

    auto it = planState->treeNodeIDToTreeIndex.find(treeNodeID);
    if(it != planState->treeNodeIDToTreeIndex.end()) {
        auto& node = planState->decompositionTree[it->second];
        node.isFailed = true;
        node.failureReason = reason;
        node.failedConditionIndex = failedIndex;
        node.failedConditionTermJson = failedTerm ? failedTerm->ToJson() : "";
    }
}

// Determine correct tree parent from sibling stack at task resolution time
// Returns PlanNode nodeID (not treeNodeID) - caller converts using NodeIDToTreeNodeID
int HtnPlanner::DetermineTreeParent(PlanState* planState, PlanNode* node)
{
#ifdef INDHTN_TREE_SIBLING_TRACKING
    // Read-only access - sibling stack management is handled in SearchNextNode/SearchNextNodeBacktrackable
    const auto& sibStack = node->getSiblingStack();

    int parentPlanNodeID;
    if(!sibStack.empty()) {
        // After SearchNextNode/Backtrackable processing, back() is the current scope
        parentPlanNodeID = sibStack.back().first;
    } else {
        // Fall back to stack parent
        auto& stack = planState->stack;
        parentPlanNodeID = (stack->size() > 1) ? (*stack)[stack->size() - 2]->nodeID() : -1;
    }

    // Walk up bookkeeping parents if needed (for parents that are tryEnd, countAnyOf, etc.)
    while(planState->nodeIDToLastTreeNodeID.find(parentPlanNodeID) == planState->nodeIDToLastTreeNodeID.end()) {
        auto it = planState->bookkeepingParents.find(parentPlanNodeID);
        if(it != planState->bookkeepingParents.end()) {
            parentPlanNodeID = it->second;
        } else {
            break;
        }
    }
    return parentPlanNodeID;
#else
    auto& stack = planState->stack;
    return (stack->size() > 1) ? (*stack)[stack->size() - 2]->nodeID() : -1;
#endif
}


// Create tree node at task resolution time (deferred from PlanNode creation)
//
// Each tree entry gets a unique treeNodeID. Multiple tasks can be processed on
// the same PlanNode (e.g., when try() fails), and each gets its own tree entry.
// Parent-child relationships use treeNodeID, not PlanNode nodeID.
void HtnPlanner::CreateTreeNodeForTask(PlanState* planState, PlanNode* node)
{
    if(node->task == nullptr) {
        return;
    }

    // Skip bookkeeping tasks - they don't get tree nodes but we track their parent
    string taskName = node->task->name();
    if(taskName == "tryEnd" || taskName == "methodScopeEnd" || taskName == "countAnyOf" ||
       taskName == "failIfNoneOf" || taskName == "beginParallel" || taskName == "endParallel") {
#ifdef INDHTN_TREE_SIBLING_TRACKING
        // Get parent PlanNode nodeID without consuming a sibling slot
        const auto& sibStack = node->getSiblingStack();
        int parentNodeID;
        if(!sibStack.empty()) {
            parentNodeID = sibStack.back().first;
        } else {
            auto& stack = planState->stack;
            parentNodeID = (stack->size() > 1) ? (*stack)[stack->size() - 2]->nodeID() : -1;
        }
        // Walk up bookkeeping parents if needed to find a real tree node
        while(planState->nodeIDToLastTreeNodeID.find(parentNodeID) == planState->nodeIDToLastTreeNodeID.end()) {
            auto it = planState->bookkeepingParents.find(parentNodeID);
            if(it != planState->bookkeepingParents.end()) {
                parentNodeID = it->second;
            } else {
                break;
            }
        }
        planState->bookkeepingParents[node->nodeID()] = parentNodeID;
#else
        auto& stack = planState->stack;
        planState->bookkeepingParents[node->nodeID()] = (stack->size() > 1) ? (*stack)[stack->size() - 2]->nodeID() : -1;
#endif
        return;
    }

    // Skip if tree node already exists for this nodeID with the same task.
    // This prevents duplicates while still allowing different tasks on the same
    // nodeID (which happens when try() fails and we process remaining tasks).
    string fullTaskName = node->task->ToString();
    auto existingTreeNodeIt = planState->nodeIDToLastTreeNodeID.find(node->nodeID());
    if(existingTreeNodeIt != planState->nodeIDToLastTreeNodeID.end()) {
        auto treeIndexIt = planState->treeNodeIDToTreeIndex.find(existingTreeNodeIt->second);
        if(treeIndexIt != planState->treeNodeIDToTreeIndex.end()) {
            auto& existingNode = planState->decompositionTree[treeIndexIt->second];
            if(existingNode.taskName == fullTaskName) {
                return; // Same task on same node - skip duplicate
            }
        }
        // Different task on same nodeID - allowed (try() failure case)
    }

    // Determine parent's treeNodeID (uses DetermineTreeParent which returns PlanNode nodeID)
    int parentPlanNodeID = DetermineTreeParent(planState, node);
    int parentTreeNodeID = (parentPlanNodeID == -1) ? -1 : NodeIDToTreeNodeID(planState, parentPlanNodeID);

    // Create tree node with unique treeNodeID
    DecompTreeNode treeNode;
    treeNode.treeNodeID = planState->nextTreeNodeID++;
    treeNode.nodeID = node->nodeID();
    treeNode.parentNodeID = parentTreeNodeID;
    treeNode.taskName = fullTaskName;

#ifdef INDHTN_TREE_SIBLING_TRACKING
    // Debug trace: show siblingStack state when tree node is created
    {
        const auto& sibStack = node->getSiblingStack();
        std::string stackStr = "[";
        for(size_t i = 0; i < sibStack.size(); i++) {
            if(i > 0) stackStr += ", ";
            stackStr += "{" + std::to_string(sibStack[i].first) + "," + std::to_string(sibStack[i].second) + "}";
        }
        stackStr += "]";
        Trace5("TREE_NODE  ", "Created tree node: treeNodeID={0}, nodeID={1}, taskName='{2}', parentTreeNodeID={3}, sibStack={4}",
               planState->stack->size(), treeNode.treeNodeID, node->nodeID(), fullTaskName, parentTreeNodeID, stackStr);
    }
#endif

    planState->treeNodeIDToTreeIndex[treeNode.treeNodeID] = planState->decompositionTree.size();
    planState->nodeIDToLastTreeNodeID[node->nodeID()] = treeNode.treeNodeID;
    planState->decompositionTree.push_back(treeNode);

    // Update parent's children list (using treeNodeID)
    if(parentTreeNodeID != -1) {
        auto parentIt = planState->treeNodeIDToTreeIndex.find(parentTreeNodeID);
        if(parentIt != planState->treeNodeIDToTreeIndex.end()) {
            auto& children = planState->decompositionTree[parentIt->second].childNodeIDs;
            if(std::find(children.begin(), children.end(), treeNode.treeNodeID) == children.end()) {
                children.push_back(treeNode.treeNodeID);
            }
        }
    }
}

string HtnPlanner::ToStringTree(shared_ptr<SolutionType> solution)
{
    if(solution == nullptr || solution->decompositionTree.empty())
    {
        return "[]";
    }

    stringstream result;
    result << "[";
    bool first = true;
    for(const auto& node : solution->decompositionTree)
    {
        if(!first) result << ",";
        result << node.ToJson();
        first = false;
    }
    result << "]";

    return result.str();
}
