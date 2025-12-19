//
//  PlanParallelizer.cpp
//  InductorHtn
//
//  Copyright © 2025 Bertrand Decoster. All rights reserved.
//
#include "PlanParallelizer.h"
#include <algorithm>
#include <queue>
#include <sstream>

using namespace std;

vector<ParallelizedOperator> PlanParallelizer::Parallelize(
    const vector<shared_ptr<HtnTerm>>& plan,
    const map<string, shared_ptr<HtnOperator>>& operatorDefs)
{
    vector<ParallelizedOperator> result;
    int currentTimestep = 0;
    int currentScope = -1;
    int scopeStartIndex = -1;

    for(size_t i = 0; i < plan.size(); i++)
    {
        const auto& term = plan[i];

        if(term->name() == "beginParallel")
        {
            // Start a parallel scope
            currentScope = stoi(term->arguments()[0]->name());
            scopeStartIndex = static_cast<int>(result.size());
            // Marker is consumed, not added to output
            continue;
        }
        else if(term->name() == "endParallel")
        {
            // End parallel scope - analyze dependencies and assign timesteps
            if(scopeStartIndex >= 0 && scopeStartIndex < static_cast<int>(result.size()))
            {
                AssignTimesteps(result, scopeStartIndex, static_cast<int>(result.size()), operatorDefs);

                // Update currentTimestep to be after the parallel scope
                int maxTimestep = currentTimestep;
                for(int j = scopeStartIndex; j < static_cast<int>(result.size()); j++)
                {
                    maxTimestep = max(maxTimestep, result[j].timestep);
                }
                currentTimestep = maxTimestep + 1;
            }
            currentScope = -1;
            scopeStartIndex = -1;
            // Marker is consumed, not added to output
            continue;
        }

        // Regular operator
        ParallelizedOperator pop;
        pop.op = term;
        pop.scopeId = currentScope;
        pop.timestep = currentTimestep;

        if(currentScope == -1)
        {
            // Sequential mode: each operator gets its own timestep
            currentTimestep++;
        }
        // Within parallel scope, timesteps are assigned by AssignTimesteps()

        result.push_back(pop);
    }

    return result;
}

bool PlanParallelizer::HasDependency(
    const shared_ptr<HtnOperator>& opA,
    const shared_ptr<HtnOperator>& opB)
{
    if(!opA || !opB)
    {
        return false;
    }

    // B depends on A if A modifies something B also modifies (write-write conflict)
    // or if A produces something B consumes (write-read, approximated by del/add overlap)

    // Check: A adds something that B deletes
    for(const auto& addTerm : opA->additions())
    {
        for(const auto& delTerm : opB->deletions())
        {
            // Compare functor names - if they match, there's a potential conflict
            if(addTerm->name() == delTerm->name())
            {
                return true;
            }
        }
    }

    // Check: A deletes something that B adds (both modifying same fact type)
    for(const auto& delTerm : opA->deletions())
    {
        for(const auto& addTerm : opB->additions())
        {
            if(delTerm->name() == addTerm->name())
            {
                return true;
            }
        }
    }

    // Check: A deletes something that B also deletes (both need the same precondition)
    for(const auto& delTermA : opA->deletions())
    {
        for(const auto& delTermB : opB->deletions())
        {
            if(delTermA->name() == delTermB->name())
            {
                return true;
            }
        }
    }

    return false;
}

void PlanParallelizer::AssignTimesteps(
    vector<ParallelizedOperator>& ops,
    int scopeStart,
    int scopeEnd,
    const map<string, shared_ptr<HtnOperator>>& operatorDefs)
{
    int n = scopeEnd - scopeStart;
    if(n <= 0) return;

    // Build dependency graph
    // deps[i] = list of indices (relative to scopeStart) that i depends on
    vector<vector<int>> deps(n);
    vector<int> indegree(n, 0);

    for(int i = 0; i < n; i++)
    {
        const string& nameI = ops[scopeStart + i].op->name();
        auto itI = operatorDefs.find(nameI);
        shared_ptr<HtnOperator> opDefI = (itI != operatorDefs.end()) ? itI->second : nullptr;

        for(int j = i + 1; j < n; j++)
        {
            const string& nameJ = ops[scopeStart + j].op->name();
            auto itJ = operatorDefs.find(nameJ);
            shared_ptr<HtnOperator> opDefJ = (itJ != operatorDefs.end()) ? itJ->second : nullptr;

            // Check if j depends on i (i comes before j in original order)
            if(HasDependency(opDefI, opDefJ))
            {
                deps[j].push_back(i);
                indegree[j]++;
            }
        }
    }

    // Topological sort with level assignment (BFS)
    // Operators with same level can run in parallel
    vector<int> level(n, 0);
    queue<int> q;

    // Start with nodes that have no dependencies
    for(int i = 0; i < n; i++)
    {
        if(indegree[i] == 0)
        {
            q.push(i);
            level[i] = 0;
        }
    }

    while(!q.empty())
    {
        int u = q.front();
        q.pop();

        // For each node that depends on u
        for(int i = 0; i < n; i++)
        {
            for(int dep : deps[i])
            {
                if(dep == u)
                {
                    indegree[i]--;
                    level[i] = max(level[i], level[u] + 1);
                    if(indegree[i] == 0)
                    {
                        q.push(i);
                    }
                }
            }
        }
    }

    // Assign timesteps based on levels
    // Base timestep is after the previous operator (or 0 if at start)
    int baseTimestep = (scopeStart > 0) ? ops[scopeStart - 1].timestep + 1 : 0;

    for(int i = 0; i < n; i++)
    {
        ops[scopeStart + i].timestep = baseTimestep + level[i];

        // Record dependencies (convert to absolute indices)
        for(int dep : deps[i])
        {
            ops[scopeStart + i].dependsOn.push_back(scopeStart + dep);
        }
    }
}

string PlanParallelizer::ToJson(const vector<ParallelizedOperator>& parallelizedPlan)
{
    stringstream ss;
    ss << "{\"operators\":[";

    for(size_t i = 0; i < parallelizedPlan.size(); i++)
    {
        if(i > 0) ss << ",";

        const auto& pop = parallelizedPlan[i];
        ss << "{";
        ss << "\"operator\":\"" << pop.op->ToString() << "\",";
        ss << "\"timestep\":" << pop.timestep << ",";
        ss << "\"scopeId\":" << pop.scopeId << ",";
        ss << "\"dependsOn\":[";

        for(size_t j = 0; j < pop.dependsOn.size(); j++)
        {
            if(j > 0) ss << ",";
            ss << pop.dependsOn[j];
        }

        ss << "]}";
    }

    ss << "]}";
    return ss.str();
}
