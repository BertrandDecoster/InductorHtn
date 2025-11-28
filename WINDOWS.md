# Windows C++ Compilation Guide

## How to Compile C++ on Windows

### Required Installation
- **Visual Studio 2022 Build Tools** with:
  - MSVC v143 - VS 2022 C++ x64/x86 build tools
  - Windows SDK (Windows 11 SDK 10.0.26100.0 or Windows 10 SDK)

### How to Compile

**Step 1**: Open Developer Command Prompt
- Press Windows key and type "developer command prompt"
- Select "**Developer Command Prompt for VS 2022**"

**Step 2**: Navigate to your project
```cmd
cd C:\Users\bertr\Projects\InductorHtn
```

**Step 3**: Compile
```cmd
cl /EHsc hello.cpp
```

**Step 4**: Run
```cmd
hello.exe
```

That's it! The Developer Command Prompt automatically sets up all environment variables for you.

## Common Compiler Flags

- `/EHsc` - Enable C++ exception handling (required for iostream and STL)
- `/Fe:filename.exe` - Specify output executable name
- `/O2` - Optimize for speed (release builds)
- `/Zi` - Generate debug information
- `/W3` - Warning level 3 (recommended)
- `/W4` - Warning level 4 (stricter)

## Example: Hello World

```cpp
#include <iostream>

int main() {
    std::cout << "Hello, World!" << std::endl;
    return 0;
}
```

Compile and run:
```cmd
cl /EHsc hello.cpp
hello.exe
```

## Debugging Information

### System Configuration (This Machine)
- **Location**: `C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools`
- **MSVC Version**: 14.44.35207
- **Compiler Version**: 19.44.35221
- **Compiler Path**: `C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Tools\MSVC\14.44.35207\bin\Hostx64\x64\cl.exe`

### vcvars64.bat Location (for debugging/automation)
```
C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat
```

This batch file sets up all necessary environment variables (PATH, INCLUDE, LIB) if you need to compile from a regular command prompt instead of the Developer Command Prompt.

### Troubleshooting

**Issue: "cl is not recognized"**
- Solution: You're not in a Developer Command Prompt. Either open Developer Command Prompt for VS 2022, or run the vcvars64.bat file first.

**Issue: "fatal error C1034: iostream: no include path set"**
- Solution: Environment not set up correctly. Use Developer Command Prompt or run vcvars64.bat.

### Finding Visual Studio Installation

To locate your Visual Studio installation:
```bash
"C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe" -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
```

## Notes

- For CMake builds, see [CLAUDE.md](CLAUDE.md)
- Always use `/EHsc` flag when compiling C++ code that uses exceptions or STL
