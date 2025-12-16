---
description: Build environment setup and troubleshooting
globs: CMakeLists.txt, src/**
---

# Build Setup & Troubleshooting

## Windows Setup (One-Time)

### Required Installation
- **Visual Studio 2022 Build Tools** with:
  - MSVC v143 - VS 2022 C++ x64/x86 build tools
  - Windows SDK (Windows 11 SDK 10.0.26100.0 or Windows 10 SDK)

### Environment Setup
Use **Developer Command Prompt for VS 2022** - it automatically configures PATH, INCLUDE, LIB.

Alternative: Run vcvars64.bat manually:
```cmd
"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
```

### Finding Visual Studio Installation
```cmd
"C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe" -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
```

## macOS/Linux Setup

### Required
- CMake
- GCC or Clang
- Make

Ubuntu: `apt-get install cmake build-essential`
macOS: `xcode-select --install` + Homebrew CMake

## CMake Configuration

### Generators
```bash
cmake -help  # List available generators

# Windows
cmake -G "Visual Studio 17 2022" ../src

# macOS/Linux
cmake -G "Unix Makefiles" ../src
cmake -G "Xcode" ../src  # macOS alternative
```

### Build Configurations
```bash
cmake --build ./ --config Release  # Optimized
cmake --build ./ --config Debug    # With debug symbols
```

**Important**: Debug builds have extensive error checking that significantly impacts performance. Always use Release for performance evaluation.

## Troubleshooting

### "cl is not recognized"
**Cause**: Not in Developer Command Prompt
**Solution**: Open "Developer Command Prompt for VS 2022" or run vcvars64.bat

### "fatal error C1034: iostream: no include path set"
**Cause**: Environment not configured
**Solution**: Use Developer Command Prompt or run vcvars64.bat

### CMake can't find compiler
**Cause**: Visual Studio components not installed
**Solution**: Run Visual Studio Installer, add "Desktop development with C++"

### Python bindings not found
**Cause**: Library not on system path
**Solution**:
- Windows: Add build/Release/ to PATH or copy indhtnpy.dll
- macOS: Copy libindhtnpy.dylib to /usr/local/lib
- Linux: Copy libindhtnpy.so to /usr/lib or set LD_LIBRARY_PATH

## Compiler Flags Reference

Windows (cl.exe):
- `/EHsc` - Enable C++ exceptions (required for STL)
- `/O2` - Optimize for speed
- `/Zi` - Debug info
- `/W3` or `/W4` - Warning levels

## Directory Structure

```
build/
├── Debug/
│   ├── indhtn.exe      # Interactive REPL
│   ├── runtests.exe    # Unit tests
│   └── indhtnpy.dll    # Python bindings
├── Release/
│   └── (same as Debug)
└── *.vcxproj           # Visual Studio projects
```
