//
//  HtnArithmeticOperators.cpp
//  GameLib
//
//  Created by Eric Zinda on 10/2/18.
//  Copyright © 2018 Eric Zinda. All rights reserved.
//
#include <algorithm>
#include "FXPlatform/Utilities.h"
#include "HtnArithmeticOperators.h"
#include "HtnTerm.h"
#include "HtnTermFactory.h"

std::shared_ptr<HtnTerm> HtnArithmeticOperators::Float(HtnTermFactory *factory, std::shared_ptr<HtnTerm> left)
{
    std::shared_ptr<HtnTerm> leftEval = left->Eval(factory);
    if(leftEval != nullptr)
    {
        return factory->CreateConstant(lexical_cast<std::string>(leftEval->GetDouble()));
    }
    
    return nullptr;
}

std::shared_ptr<HtnTerm> HtnArithmeticOperators::Integer(HtnTermFactory *factory, std::shared_ptr<HtnTerm> left)
{
    std::shared_ptr<HtnTerm> leftEval = left->Eval(factory);
    if(leftEval != nullptr)
    {
        return factory->CreateConstant(lexical_cast<std::string>(leftEval->GetInt()));
    }
    
    return nullptr;
}

std::shared_ptr<HtnTerm> HtnArithmeticOperators::Abs(HtnTermFactory *factory, std::shared_ptr<HtnTerm> left)
{
    std::shared_ptr<HtnTerm>leftEval = left->Eval(factory);
    if(leftEval != nullptr)
    {
        HtnTermType leftType = leftEval->GetTermType();
        if(leftType == HtnTermType::IntType)
        {
            return factory->CreateConstant(lexical_cast<std::string>(abs(leftEval->GetInt())));
        }
        else
        {
            return factory->CreateConstant(lexical_cast<std::string>(abs(leftEval->GetDouble())));
        }
    }
    
    return nullptr;
}

std::shared_ptr<HtnTerm> HtnArithmeticOperators::Divide(HtnTermFactory *factory, std::shared_ptr<HtnTerm> left, std::shared_ptr<HtnTerm> right)
{
    std::shared_ptr<HtnTerm>leftEval = left->Eval(factory);
    if(leftEval != nullptr)
    {
        HtnTermType leftType = leftEval->GetTermType();
        std::shared_ptr<HtnTerm>rightEval = right->Eval(factory);
        if(rightEval != nullptr)
        {
            HtnTermType rightType = rightEval->GetTermType();
            if(leftType == HtnTermType::IntType && rightType == HtnTermType::IntType)
            {
                return factory->CreateConstant(lexical_cast<std::string>(leftEval->GetInt() / rightEval->GetInt()));
            }
            else
            {
                return factory->CreateConstant(lexical_cast<std::string>(leftEval->GetDouble() / rightEval->GetDouble()));
            }
        }
    }
    
    return nullptr;
}

std::shared_ptr<HtnTerm> HtnArithmeticOperators::Equal(HtnTermFactory *factory, std::shared_ptr<HtnTerm> left, std::shared_ptr<HtnTerm> right)
{
    std::shared_ptr<HtnTerm>leftEval = left->Eval(factory);
    if(leftEval != nullptr)
    {
        HtnTermType leftType = leftEval->GetTermType();
        std::shared_ptr<HtnTerm>rightEval = right->Eval(factory);
        if(rightEval != nullptr)
        {
            HtnTermType rightType = rightEval->GetTermType();
            if(leftType == HtnTermType::IntType && rightType == HtnTermType::IntType)
            {
                return leftEval->GetInt() == rightEval->GetInt() ? factory->True() : factory->False();
            }
            else
            {
                return leftEval->GetDouble() == rightEval->GetDouble() ? factory->True() : factory->False();
            }
        }
    }
    
    return nullptr;
}

// Both sides get evaluated, converted to float, then compared
std::shared_ptr<HtnTerm> HtnArithmeticOperators::GreaterThan(HtnTermFactory *factory, std::shared_ptr<HtnTerm> left, std::shared_ptr<HtnTerm> right)
{
    std::shared_ptr<HtnTerm>leftEval = left->Eval(factory);
    if(leftEval != nullptr)
    {
        std::shared_ptr<HtnTerm>rightEval = right->Eval(factory);
        if(rightEval != nullptr)
        {
            if(leftEval->GetDouble() > rightEval->GetDouble())
            {
                return factory->True();
            }
            else
            {
                return factory->False();
            }
        }
    }
    
    return nullptr;
}

// Both sides get evaluated, converted to float, then compared
std::shared_ptr<HtnTerm> HtnArithmeticOperators::GreaterThanOrEqual(HtnTermFactory *factory, std::shared_ptr<HtnTerm> left, std::shared_ptr<HtnTerm> right)
{
    std::shared_ptr<HtnTerm>leftEval = left->Eval(factory);
    if(leftEval != nullptr)
    {
        std::shared_ptr<HtnTerm>rightEval = right->Eval(factory);
        if(rightEval != nullptr)
        {
            if(leftEval->GetDouble() >= rightEval->GetDouble())
            {
                return factory->True();
            }
            else
            {
                return factory->False();
            }
        }
    }
    
    return nullptr;
}

// Both sides get evaluated, converted to float, then compared
std::shared_ptr<HtnTerm> HtnArithmeticOperators::LessThan(HtnTermFactory *factory, std::shared_ptr<HtnTerm> left, std::shared_ptr<HtnTerm> right)
{
    std::shared_ptr<HtnTerm>leftEval = left->Eval(factory);
    if(leftEval != nullptr)
    {
        std::shared_ptr<HtnTerm>rightEval = right->Eval(factory);
        if(rightEval != nullptr)
        {
            if(leftEval->GetDouble() < rightEval->GetDouble())
            {
                return factory->True();
            }
            else
            {
                return factory->False();
            }
        }
    }
    
    return nullptr;
}

// Both sides get evaluated, converted to float, then compared
std::shared_ptr<HtnTerm> HtnArithmeticOperators::LessThanOrEqual(HtnTermFactory *factory, std::shared_ptr<HtnTerm> left, std::shared_ptr<HtnTerm> right)
{
    std::shared_ptr<HtnTerm>leftEval = left->Eval(factory);
    if(leftEval != nullptr)
    {
        std::shared_ptr<HtnTerm>rightEval = right->Eval(factory);
        if(rightEval != nullptr)
        {
            if(leftEval->GetDouble() <= rightEval->GetDouble())
            {
                return factory->True();
            }
            else
            {
                return factory->False();
            }
        }
    }
    
    return nullptr;
}


std::shared_ptr<HtnTerm> HtnArithmeticOperators::Max(HtnTermFactory *factory, std::shared_ptr<HtnTerm> left, std::shared_ptr<HtnTerm> right)
{
    std::shared_ptr<HtnTerm>leftEval = left->Eval(factory);
    if(leftEval != nullptr)
    {
        HtnTermType leftType = leftEval->GetTermType();
        std::shared_ptr<HtnTerm>rightEval = right->Eval(factory);
        if(rightEval != nullptr)
        {
            HtnTermType rightType = rightEval->GetTermType();
            if(leftType == HtnTermType::IntType && rightType == HtnTermType::IntType)
            {
                return factory->CreateConstant(lexical_cast<std::string>(std::max(leftEval->GetInt(), rightEval->GetInt())));
            }
            else
            {
                return factory->CreateConstant(lexical_cast<std::string>(std::max(leftEval->GetDouble(), rightEval->GetDouble())));
            }
        }
    }
    
    return nullptr;
}

std::shared_ptr<HtnTerm> HtnArithmeticOperators::Min(HtnTermFactory *factory, std::shared_ptr<HtnTerm> left, std::shared_ptr<HtnTerm> right)
{
    std::shared_ptr<HtnTerm>leftEval = left->Eval(factory);
    if(leftEval != nullptr)
    {
        HtnTermType leftType = leftEval->GetTermType();
        std::shared_ptr<HtnTerm>rightEval = right->Eval(factory);
        if(rightEval != nullptr)
        {
            HtnTermType rightType = rightEval->GetTermType();
            if(leftType == HtnTermType::IntType && rightType == HtnTermType::IntType)
            {
                return factory->CreateConstant(lexical_cast<std::string>(std::min(leftEval->GetInt(), rightEval->GetInt())));
            }
            else
            {
                return factory->CreateConstant(lexical_cast<std::string>(std::min(leftEval->GetDouble(), rightEval->GetDouble())));
            }
        }
    }
    
    return nullptr;
}

// Keep the type the same if we can.  If we can't, convert to double
std::shared_ptr<HtnTerm> HtnArithmeticOperators::Minus(HtnTermFactory *factory, std::shared_ptr<HtnTerm> left, std::shared_ptr<HtnTerm> right)
{
    std::shared_ptr<HtnTerm>leftEval = left->Eval(factory);
    if(leftEval != nullptr)
    {
        HtnTermType leftType = leftEval->GetTermType();
        std::shared_ptr<HtnTerm>rightEval = right->Eval(factory);
        if(rightEval != nullptr)
        {
            HtnTermType rightType = rightEval->GetTermType();
            if(leftType == HtnTermType::IntType && rightType == HtnTermType::IntType)
            {
                return factory->CreateConstant(lexical_cast<std::string>(leftEval->GetInt() - rightEval->GetInt()));
            }
            else
            {
                return factory->CreateConstant(lexical_cast<std::string>(leftEval->GetDouble() - rightEval->GetDouble()));
            }
        }
    }
    
    return nullptr;
}

std::shared_ptr<HtnTerm> HtnArithmeticOperators::Multiply(HtnTermFactory *factory, std::shared_ptr<HtnTerm> left, std::shared_ptr<HtnTerm> right)
{
    std::shared_ptr<HtnTerm>leftEval = left->Eval(factory);
    if(leftEval != nullptr)
    {
        HtnTermType leftType = leftEval->GetTermType();
        std::shared_ptr<HtnTerm>rightEval = right->Eval(factory);
        if(rightEval != nullptr)
        {
            HtnTermType rightType = rightEval->GetTermType();
            if(leftType == HtnTermType::IntType && rightType == HtnTermType::IntType)
            {
                return factory->CreateConstant(lexical_cast<std::string>(leftEval->GetInt() * rightEval->GetInt()));
            }
            else
            {
                return factory->CreateConstant(lexical_cast<std::string>(leftEval->GetDouble() * rightEval->GetDouble()));
            }
        }
    }
    
    return nullptr;
}

// Keep the type the same if we can.  If we can't, convert to double
std::shared_ptr<HtnTerm> HtnArithmeticOperators::Plus(HtnTermFactory *factory, std::shared_ptr<HtnTerm> left, std::shared_ptr<HtnTerm> right)
{
    std::shared_ptr<HtnTerm> leftEval = left->Eval(factory);
    if(leftEval != nullptr)
    {
        HtnTermType leftType = leftEval->GetTermType();
        std::shared_ptr<HtnTerm> rightEval = right->Eval(factory);
        if(rightEval != nullptr)
        {
            HtnTermType rightType = rightEval->GetTermType();
            if(leftType == HtnTermType::IntType && rightType == HtnTermType::IntType)
            {
                return factory->CreateConstant(lexical_cast<std::string>(leftEval->GetInt() + rightEval->GetInt()));
            }
            else
            {
                return factory->CreateConstant(lexical_cast<std::string>(leftEval->GetDouble() + rightEval->GetDouble()));
            }
        }
    }
    
    return nullptr;
}

