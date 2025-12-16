# Build & Test Commands

## Windows

### Build (from Developer Command Prompt for VS 2022)
```cmd
cd C:\Users\bertr\Projects\InductorHtn
mkdir build
cd build
cmake -G "Visual Studio 17 2022" ../src
cmake --build ./ --config Release
```

### Test
```cmd
./build/Release/runtests.exe
```

### Run Interactive Mode
```cmd
./build/Release/indhtn.exe Examples/Taxi.htn
```

## macOS / Linux

### Build
```bash
mkdir build && cd build
cmake -G "Unix Makefiles" ../src
cmake --build ./ --config Release
```

### Test
```bash
./runtests
```

### Run Interactive Mode
```bash
./indhtn Examples/Taxi.htn
```

## Python Tests

```bash
cd src/Python
python PythonUsage.py
```

Requires `indhtnpy.dll` (Windows) or `libindhtnpy.dylib` (macOS) on system path.

## GUI

See `gui/README.md`

## MCP Server

See `mcp-server/README.md`
