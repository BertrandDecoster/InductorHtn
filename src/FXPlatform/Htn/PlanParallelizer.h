//
//  PlanParallelizer.h
//  InductorHtn
//
//  Post-processor that analyzes operator dependencies within parallel scopes
//  and assigns timesteps for parallel execution.
//
//  Copyright © 2025 Bertrand Decoster. All rights reserved.
//
#pragma once
#include "FXPlatform/Prolog/HtnTerm.h"
#include "HtnOperator.h"
#include <vector>
#include <map>
#include <string>
#include <memory>

// Represents an operator with parallel execution metadata
struct ParallelizedOperator
{
    std::shared_ptr<HtnTerm> op;    // The operator term
    int timestep;                    // Execution timestep (0-based)
    int scopeId;                     // Parallel scope ID, or -1 if sequential
    std::vector<int> dependsOn;      // Indices of operators this depends on

    ParallelizedOperator() : timestep(0), scopeId(-1) {}
};

// Post-processor for extracting parallelism from plans with beginParallel/endParallel markers
class PlanParallelizer
{
public:
    // Takes a plan containing operators and beginParallel/endParallel markers.
    // Returns operators with timestep annotations for parallel execution.
    // Markers are consumed and not included in output.
    //
    // Parameters:
    //   plan - Vector of operator terms, may include beginParallel(id) and endParallel(id) markers
    //   operatorDefs - Map of operator name to operator definition (for del/add analysis)
    //
    // Returns:
    //   Vector of ParallelizedOperator with timesteps assigned.
    //   Within parallel scopes, independent operators share the same timestep.
    static std::vector<ParallelizedOperator> Parallelize(
        const std::vector<std::shared_ptr<HtnTerm>>& plan,
        const std::map<std::string, std::shared_ptr<HtnOperator>>& operatorDefs);

    // Convert parallelized plan to JSON string
    static std::string ToJson(const std::vector<ParallelizedOperator>& parallelizedPlan);

private:
    // Check if opB depends on opA based on del/add effects.
    // B depends on A if:
    //   - A adds a fact that B deletes (write-write conflict)
    //   - A deletes a fact that B adds (write-write conflict)
    //   - A adds a fact that B reads (but we don't track reads explicitly)
    static bool HasDependency(
        const std::shared_ptr<HtnOperator>& opA,
        const std::shared_ptr<HtnOperator>& opB);

    // Assign timesteps to operators within a parallel scope using topological sort.
    // Operators with no dependencies get the lowest timestep (can run in parallel).
    static void AssignTimesteps(
        std::vector<ParallelizedOperator>& ops,
        int scopeStart,
        int scopeEnd,
        const std::map<std::string, std::shared_ptr<HtnOperator>>& operatorDefs);
};
