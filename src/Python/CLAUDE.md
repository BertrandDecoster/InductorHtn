To add a new function in Python, here are the steps

#1 : PythonInterface.cpp, add your function with __declspec(dllexport) prefixed
#2 : build the lib (In VSCode : Cmake tab -> build all), and put in in the path. Typically, cp libindhtnpy.dylib /usr/local/lib/libindhtnpy.dylib
#3 : indhtnpy.py, in HtnPlanner, declare function metadata (arguments and return) self.indhtnLib.FunctionName.argtypes = ... and restype = ... 
#4 : indhtnpy.py, in HtnPlanner, create a function that calls the function from the lib (self.indhtnLib.FunctionName())
#5 : in your python script import HtnPlanner and call the function