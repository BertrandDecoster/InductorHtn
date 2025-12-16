---
description: Python bindings via indhtnpy
globs: src/Python/**
---

# Python Bindings

Python interface to InductorHTN via ctypes.

## Files

```
src/Python/
├── indhtnpy.py      # Python wrapper class
├── PythonUsage.py   # Usage examples
└── PythonUsageBD.py # Additional examples
```

C++ side:
```
src/FXPlatform/PythonInterface.cpp  # DLL exports
```

## Adding a New Python Function

### Step 1: Add C++ Export
In `PythonInterface.cpp`, add function with `__declspec(dllexport)`:

```cpp
extern "C" __declspec(dllexport) const char* NewFunction(
    void* planner,
    const char* param
) {
    // Implementation
    return result;
}
```

### Step 2: Build Library
```bash
cmake --build ./build --config Release
```

Copy to path:
- Windows: Add to PATH or copy `indhtnpy.dll`
- macOS: `cp libindhtnpy.dylib /usr/local/lib/`
- Linux: `cp libindhtnpy.so /usr/lib/`

### Step 3: Declare in indhtnpy.py
Add metadata in `HtnPlanner.__init__`:

```python
# Argument types
self.indhtnLib.NewFunction.argtypes = [c_void_p, c_char_p]

# Return type
self.indhtnLib.NewFunction.restype = c_char_p
```

### Step 4: Create Wrapper Method
In `HtnPlanner` class:

```python
def NewFunction(self, param):
    result = self.indhtnLib.NewFunction(
        self.planner,
        param.encode('utf-8')
    )
    return result.decode('utf-8') if result else None
```

### Step 5: Use in Python
```python
from indhtnpy import HtnPlanner

planner = HtnPlanner(False)  # False = no debug
result = planner.NewFunction("param")
```

## Existing API

### HtnPlanner Class

```python
planner = HtnPlanner(debug=False)
```

Methods:
- `HtnCompile(program)` - Compile HTN program
- `PrologCompile(program)` - Compile Prolog program
- `FindAllPlans(goal)` - Find all HTN plans
- `PrologQuery(query)` - Execute Prolog query
- `HtnQuery(query)` - Execute query with HTN syntax

### Return Format

Results returned as JSON:
```python
# Terms are dicts with name as key, args as value
{"termName": [{"arg1": []}, {"arg2": []}]}

# Variables have ? prefix
{"?Who": {"socrates": []}}
```

Helper functions:
- `termName(term)` - Get term's functor name
- `termArgs(term)` - Get term's arguments

## Library Path Requirements

The shared library must be findable:

| Platform | Library | Location |
|----------|---------|----------|
| Windows | `indhtnpy.dll` | PATH or working directory |
| macOS | `libindhtnpy.dylib` | `/usr/local/lib` |
| Linux | `libindhtnpy.so` | `/usr/lib` or LD_LIBRARY_PATH |
