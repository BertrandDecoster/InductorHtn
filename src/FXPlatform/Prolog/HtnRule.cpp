//
//  HtnRule.cpp
//  GameLib
//
//  Created by Eric Zinda on 1/15/19.
//  Copyright © 2019 Eric Zinda. All rights reserved.
//

#include "HtnRule.h"
#include "HtnRuleSet.h"
#include "HtnTerm.h"

std::shared_ptr<HtnRule> HtnRule::MakeVariablesUnique(HtnTermFactory *factory, const std::string &uniquifier, std::map<std::string, std::shared_ptr<HtnTerm>> &variableMap, bool onlyDontCareVariables) const
{
	// Don't care variables can't match
	int dontCareCount = 0;
    std::shared_ptr<HtnTerm> newHead = this->head()->MakeVariablesUnique(factory, onlyDontCareVariables, uniquifier, &dontCareCount, variableMap);
    std::vector<std::shared_ptr<HtnTerm>> newTail;
    for(std::shared_ptr<HtnTerm> term : this->tail())
    {
        newTail.push_back(term->MakeVariablesUnique(factory, onlyDontCareVariables, uniquifier, &dontCareCount, variableMap));
    }
    
    std::shared_ptr<HtnRule> newRule = std::shared_ptr<HtnRule>(new HtnRule(newHead, newTail));
    return newRule;
}

std::string HtnRule::ToString() const
{
    std::stringstream stream;
    stream << head()->ToString() << " => ";
    bool hasTail = false;
    for(std::shared_ptr<HtnTerm> term : tail())
    {
        stream << (hasTail ? ", " : "") << term->ToString();
        hasTail = true;
    }
    
    return stream.str();
}

std::string HtnRule::ToStringProlog() const
{
    std::stringstream stream;
    stream << head()->ToString() << " :- ";
    bool hasTail = false;
    for(std::shared_ptr<HtnTerm> term : tail())
    {
        stream << (hasTail ? ", " : "") << term->ToString();
        hasTail = true;
    }
    
    stream << ".";
    std::string result = stream.str();
    return result;
}
