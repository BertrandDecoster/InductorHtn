# InductorHTN Architecture Guide

## Origin: Exospecies AI Game Development

InductorHTN was originally developed by Eric Zinda for the **Exospecies** strategy game AI system. The project emerged from the practical need to create sophisticated game AI that could provide compelling single-player experiences while behaving naturally and predictably.

### Design Philosophy & Motivation

The engine was built with several key principles:

**Human-Like AI Behavior**: HTN was chosen because it "builds an AI that behaves like a human" by encoding human strategic thinking patterns rather than using machine learning approaches that might produce unpredictable behavior.

**Pragmatic Implementation**: The focus was on creating "simple, debuggable, understandable" code rather than academic completeness. The entire engine is approximately 6,300 lines - compact yet powerful.

**Cross-Platform Gaming**: Built in C++ for portability across gaming platforms (iOS, Windows, macOS) with memory-efficient design suitable for mobile environments.

**Rapid Prototyping**: Prolog integration provides "extremely low startup cost for prototyping" new AI behaviors and game mechanics.

## What is HTN Planning?

**Hierarchical Task Network (HTN) Planning** is an AI planning technique that mimics human problem-solving by breaking down complex tasks into simpler, manageable subtasks. Unlike classical planning that works forward from initial states to goals, HTN planning starts with high-level objectives and recursively decomposes them using domain knowledge.

### Key HTN Concepts

- **Tasks**: Abstract objectives to accomplish (e.g., "travel from A to B", "attack enemy base")
- **Methods**: Knowledge about how to decompose complex tasks into simpler subtasks with specific conditions
- **Operators**: Primitive actions that directly modify the world state (add/delete facts)
- **Hierarchical Decomposition**: Breaking down abstract tasks until all become executable operators
- **State of the World**: Current game/world conditions represented as Prolog facts

### SHOP Planner Model

InductorHTN follows the SHOP (Simple Hierarchical Ordered Planner) model, which processes tasks in order and uses Prolog-style logical reasoning for preconditions and world state representation.

### HTN Advantages for Game AI

**Predictable Behavior**: HTNs won't produce "surprising" behaviors - they only do what they're programmed to do, making them ideal for game AI where players expect logical opponent behavior.

**Natural Planning**: The hierarchical decomposition mirrors how humans naturally think about problem-solving, from high-level strategy down to specific actions.

**Guaranteed Solutions**: When a plan is found, the ordered sequence of operators is guaranteed to work (assuming the world model is accurate).

**Multiple Strategies**: Methods can encode multiple alternative approaches to the same high-level task, allowing flexible AI responses to different situations.

## Architecture Overview

InductorHTN combines HTN planning with Prolog reasoning in a memory-efficient, stackless design suitable for constrained environments.

```
┌─────────────────────────────────────────────────────────────┐
│                      Application Layer                      │
├─────────────────────────────────────────────────────────────┤
│                   HTN Planning Engine                       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐  │
│  │   HtnPlanner    │  │   HtnMethod     │  │ HtnOperator  │  │
│  │   (Scheduler)   │  │ (Decomposition) │  │ (Primitive)  │  │
│  └─────────────────┘  └─────────────────┘  └──────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                   Prolog Reasoning Engine                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐  │
│  │ HtnGoalResolver │  │   HtnRuleSet    │  │   HtnTerm    │  │
│  │  (Resolution)   │  │   (Knowledge)   │  │ (Unification)│  │
│  └─────────────────┘  └─────────────────┘  └──────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                      Compiler Layer                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐  │
│  │  HtnCompiler    │  │ PrologCompiler  │  │    Parser    │  │
│  │ (HTN Specific)  │  │ (Base Logic)    │  │   (Lexing)   │  │
│  └─────────────────┘  └─────────────────┘  └──────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                     Platform Support                        │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐  │
│  │     Posix       │  │      iOS        │  │   Windows    │  │
│  │   (Linux/Mac)   │  │   (Mobile)      │  │   (Desktop)  │  │
│  └─────────────────┘  └─────────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. HTN Planning Engine (`src/FXPlatform/Htn/`)

#### HtnPlanner (`HtnPlanner.h/.cpp`)
- **Role**: Main planning orchestrator extending HtnDomain
- **Responsibilities**:
  - Schedules and executes HTN planning algorithm
  - Maintains collections of methods and operators
  - Manages memory budgets and planning state
  - Provides interfaces for finding single/multiple plans
- **Key Features**:
  - Stackless execution for memory efficiency
  - Configurable memory budgets with out-of-memory detection
  - Support for finding all possible solutions or just the first
  - Thread-safe abort mechanism

#### HtnMethod (`HtnMethod.h/.cpp`) 
- **Role**: Represents task decomposition knowledge
- **Structure**:
  - **Head**: The task being decomposed (e.g., `travel(?dest)`)
  - **Conditions**: Prolog queries that must be satisfied (preconditions)
  - **Tasks**: Ordered list of subtasks to execute
  - **Type**: Normal, AllSetOf, or AnySetOf for different execution semantics
- **Syntax Example**: `travel(?dest) :- if(at(?agent, ?start)), do(walk(?start, ?dest)).`

#### HtnOperator (`HtnOperator.h/.cpp`)
- **Role**: Primitive actions that modify world state
- **Structure**:
  - **Head**: The primitive task being executed
  - **Deletions**: Facts to remove from world state (`del()`)
  - **Additions**: Facts to add to world state (`add()`)
- **Syntax Example**: `walk(?from, ?to) :- del(at(?agent, ?from)), add(at(?agent, ?to)).`

#### HtnDomain (`HtnDomain.h`)
- **Role**: Abstract interface for HTN domain management
- **Purpose**: Defines contracts for adding/accessing methods and operators
- **Implementation**: Realized by HtnPlanner class

### 2. Prolog Reasoning Engine (`src/FXPlatform/Prolog/`)

#### HtnGoalResolver (`HtnGoalResolver.h/.cpp`)
- **Role**: Core Prolog-style resolution engine
- **Responsibilities**:
  - Unification of terms and variables
  - SLD resolution for logical queries
  - Built-in predicates (arithmetic, I/O, meta-predicates)
  - Custom rule registration and execution
- **Algorithm**: Uses SLD (Selective Linear Definite) resolution with backtracking
- **Memory Management**: Configurable budgets with graceful degradation

#### HtnRuleSet (`HtnRuleSet.h/.cpp`)
- **Role**: Knowledge base storage
- **Contents**:
  - Facts: Ground terms representing world state
  - Rules: Horn clauses for logical inference
  - Efficient indexing for fast rule lookup
- **Features**: Thread-safe, memory-efficient storage with rule management

#### HtnTerm & HtnTermFactory (`HtnTerm.h/.cpp`, `HtnTermFactory.h/.cpp`)
- **Role**: Term representation and management
- **HtnTerm Types**:
  - Constants: `at`, `player`, `gold`
  - Variables: `?agent`, `?location` (note: `?` prefix, not Prolog capitalization)
  - Functors: `at(?agent, ?location)`, `has(?player, ?item)`
  - Lists: `[item1, item2, item3]`
- **HtnTermFactory**: Manages term creation with interning for memory efficiency
- **Design Pattern**: Factory pattern ensures all terms come from same factory for unification

### 3. Compiler Layer (`src/FXPlatform/Parser/` & Prolog/)

#### HtnCompiler (`Htn/HtnCompiler.h/.cpp`)
- **Role**: HTN-specific language compiler extending PrologCompiler
- **Key Function**: `ParseRule()` - interprets HTN keywords:
  - `if()`: Method preconditions
  - `do()`: Method task decomposition  
  - `del()`: Operator deletions
  - `add()`: Operator additions
  - `else`, `allOf`, `anyOf`: Control flow modifiers
- **Error Detection**: `FindLogicErrors()` detects infinite loops and missing task definitions

#### PrologCompiler (`Prolog/PrologCompiler.h/.cpp`)
- **Role**: Base Prolog language compiler
- **Responsibilities**:
  - Parses Prolog syntax into term structures
  - Handles rules, facts, queries, and lists
  - Variable binding and scope management
- **Template Design**: Supports both standard Prolog (capitalized variables) and HTN-style (`?` prefixed variables)

#### Variable Type System
The system supports dual variable conventions through templates:
- **Standard Prolog**: `Player`, `Money` (capitalized = variable)
- **HTN Style**: `?player`, `?money` (`?` prefix = variable)

**Compiler Variants**:
- `HtnStandardCompiler`: HTN programs with standard Prolog variables
- `HtnCompiler`: HTN programs with `?` prefixed variables  
- `PrologStandardCompiler`: Pure Prolog with standard variables
- `PrologCompiler`: Pure Prolog with `?` prefixed variables

### 4. Parser Framework (`src/FXPlatform/Parser/`)

#### Parser (`Parser.h/.cpp`)
- **Role**: Generic recursive descent parser
- **Features**: Configurable grammar, error recovery, debug support

#### Lexer (`Lexer.h/.cpp`, `LexerReader.h/.cpp`) 
- **Role**: Tokenization of source code
- **Supports**: HTN/Prolog syntax, comments, strings, numbers, operators

## Planning Algorithm Flow

```
1. Initialize Planning State
   ├── Create initial world state (facts)
   ├── Set memory budget and goals
   └── Initialize empty plan

2. Task Selection & Processing
   ├── Select next task from task network
   ├── Check if task is primitive (operator)
   │   ├── Yes: Execute operator (add/del facts)
   │   └── No: Find applicable methods
   │
3. Method Application (if compound task)
   ├── Find all methods whose head unifies with task
   ├── Check method preconditions against current state
   ├── Apply method: replace task with subtasks
   └── Continue with updated task network

4. Backtracking & Search
   ├── If no applicable methods/operators found
   ├── Backtrack to previous choice point
   ├── Try alternative method/operator
   └── Continue until solution found or search exhausted

5. Solution Construction
   ├── Collect sequence of executed operators
   ├── Record final world state
   └── Return plan as operator sequence
```

## Memory Management Strategy

InductorHTN is designed for memory-constrained environments:

### Factory Pattern
- All terms created through `HtnTermFactory`
- Automatic interning prevents duplicate term storage
- Shared ownership via `shared_ptr` for safe memory management

### Memory Budgets  
- Configurable limits for planning operations
- Graceful degradation when limits exceeded
- `factory->outOfMemory()` status checking after operations

### Stackless Design
- Planning state stored in heap-allocated nodes rather than call stack
- Prevents stack overflow in deep planning scenarios
- Suitable for embedded/mobile environments

## Platform Abstraction

The codebase supports multiple platforms through abstraction:

### Platform-Specific Directories
- **Posix/**: Linux, macOS, Unix systems
- **iOS/**: Apple mobile platform
- **Win/**: Windows desktop

### Abstracted Services
- **Logger**: Platform-specific logging implementations
- **FileStream**: File I/O operations
- **Stopwatch**: High-precision timing
- **TraceError**: Error reporting and diagnostics
- **Directory**: Filesystem operations

## Key Design Patterns

### 1. Template-Based Compilation
Multiple compiler variants support different variable conventions without code duplication.

### 2. Factory Pattern (HtnTermFactory)
Centralized term creation with memory optimization through interning.

### 3. Strategy Pattern (Custom Rules)
`HtnGoalResolver` supports pluggable custom predicates via function registration.

### 4. Visitor Pattern (Rule Processing)
`AllRules()` and `AllMethods()` iterate over collections using visitor callbacks.

### 5. State Pattern (Planning)
`PlanState` encapsulates planner state for iterative/resumable planning.

## Variable Convention: `?` vs Standard Prolog

InductorHTN uses `?varname` syntax instead of Prolog's capitalization convention:

**Standard Prolog**:
```prolog
travel(Agent, Destination) :- 
    at(Agent, Start), 
    path(Start, Destination).
```

**InductorHTN Style**:
```prolog
travel(?agent, ?destination) :- 
    at(?agent, ?start), 
    path(?start, ?destination).
```

This makes variables explicit and avoids confusion with constants, particularly useful in gaming and simulation domains where both `Player` and `player` might be meaningful.

## InductorHTN Unique Features

InductorHTN extends standard HTN planning with several innovations designed for game AI and practical applications:

### Advanced Control Flow

**try() Operator**: Best-effort task execution that allows graceful handling of optional or potentially failing operations without terminating the entire plan.

**anyOf/allOf Methods**: Handle scenarios with multiple solution paths:
- `anyOf`: Execute the first method that succeeds (OR logic)
- `allOf`: Execute all applicable methods (AND logic)

**else Keyword**: Provides fallback method selection, allowing more sophisticated method prioritization and execution control.

### Prolog Integration Innovations

**Hybrid Syntax**: Seamlessly combines HTN planning constructs with full Prolog capabilities:
```prolog
; HTN Method with Prolog reasoning
buildArmy(?player) :- 
    if(hasResources(?player, ?amount), ?amount >= 1000),
    do(createUnit(?player, tank), createUnit(?player, infantry)).

; Prolog rule used in HTN conditions  
hasResources(?player, ?total) :-
    gold(?player, ?goldAmt),
    food(?player, ?foodAmt), 
    is(?total, ?goldAmt + ?foodAmt).
```

**State as Facts**: World state represented as Prolog facts enables complex querying:
```prolog
; Game state facts
tile(0,0). tile(0,1). tile(1,0).
unit(Inducer1, Inducer, Player1).
life(Inducer1, 66).
at(Inducer1, tile(0,0)).

; Complex state queries work naturally
nearbyEnemies(?unit, ?count) :- 
    at(?unit, ?pos), 
    findall(?enemy, (enemyUnit(?enemy), at(?enemy, ?enemyPos), adjacent(?pos, ?enemyPos)), ?enemies),
    length(?enemies, ?count).
```

### Game-Specific Enhancements

**Exospecies State Examples**: Real-world usage patterns from the original game:
```prolog
; Unit management
walkingDistance(?from, ?to) :- 
    weatherIs(good), 
    distance(?from, ?to, ?dist), 
    =<(?dist, 2).

; Resource management
canAfford(?player, ?unitType) :-
    unitCost(?unitType, ?cost),
    currentResources(?player, ?available),
    >=(?available, ?cost).
```

### Parsing & Compilation Features

**PEG-Based Parser**: Uses Parsing Expression Grammar for flexible syntax extension and clear grammar definition.

**FailFast Philosophy**: Aggressive error detection during development to catch programmer mistakes early, with detailed diagnostic information.

**Modular Grammar**: Template-based parser allows easy extension and modification of syntax rules.

### Development & Debugging Support

**Comprehensive Tracing**: Built-in verbose tracing system helps understand planning failures and method selection.

**Memory Budget Management**: Explicit memory limits with graceful degradation prevent runaway planning in resource-constrained environments.

**Logic Error Detection**: `FindLogicErrors()` automatically detects potential infinite loops and missing task definitions during compilation.

### Real-World Performance

**Compact Codebase**: Despite powerful features, the entire engine is only ~6,300 lines of C++ code.

**Cross-Platform Deployment**: Successfully deployed in production games across iOS, Windows, and macOS platforms.

**Lightweight Prolog**: Custom Prolog implementation optimized for HTN planning use cases rather than general-purpose logic programming.

## Integration Points

### C++ Application Integration
```cpp
// Create factory and planner
HtnTermFactory factory;
HtnPlanner planner;

// Load domain knowledge
HtnCompiler compiler(&factory, state.get(), &planner);
compiler.LoadFile("domain.htn");

// Find plan
auto solution = planner.FindPlan(&factory, initialState, goals);
```

### Python Integration
The system provides Python bindings through `libindhtnpy` for scripting and rapid prototyping.

This architecture provides a clean separation between HTN-specific planning logic and general Prolog reasoning, making the system both powerful and maintainable while supporting diverse deployment environments.