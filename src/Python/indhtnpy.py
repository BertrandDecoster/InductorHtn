import sys, platform
import ctypes, ctypes.util
from sys import platform
import json
import logging
from time import perf_counter_ns
perfLogger = logging.getLogger('indhtnpy.performance')


# Prolog json term format used by the code below is:
# A single Prolog term is either:
#  1. a dictionary with one key that is the name of the term
#       Arguments are in a list. E.g.:
#       { "TermName": [{"Arg1TermName":[]}, {"Arg2TermName":[]}] }
#  2. a Prolog list represented as a Python list (a list is also a term in Prolog):
#       [{ "TermName": [{"Arg1TermName":[]}, {"Arg2TermName":[]}] }]
def termArgs(term):
    if termIsList(term):
        # really should call termIsList() and not call termArgs
        return None
    elif not isinstance(term, dict):
        # handle variables as terms
        return None
    else:
        return list(term.values())[0]


def termIsConstant(term):
    if termIsList(term):
        # really should call termIsList() and not call termName
        return None
    else:
        args = termArgs(term)
        if args is None:
            # is a variable
            return True
        else:
            return len(args) == 0


def termName(term):
    if termIsList(term):
        # really should call termIsList() and not call termName
        return None
    else:
        return list(term)[0]


def termIsList(term):
    return isinstance(term, list)


# Properly converts all solutions (or errors) returned
# from a prolog query into a list of strings with Prolog predicates
def queryResultToPrologStringList(queryResult):
    jsonQuery = json.loads(queryResult)
    solutionList = []
    if "false" in jsonQuery[0]:
        # Query failed, so it is not a unification list it
        # is a term list
        solutionList.append(termListToString(jsonQuery))
    else:
        for solution in jsonQuery:
            assignmentList = []
            for variableName in solution.keys():
                assignmentList.append("{} = {}".format(variableName, termToString(solution[variableName])))
            solutionList.append(", ".join(assignmentList))

    return solutionList

# Properly converts all solutions (or errors) returned from FindAllPlans()
# into a list of strings with Prolog predicates
def findAllPlansResultToPrologStringList(queryResult):
    jsonSolutions = json.loads(queryResult)
    solutionList = []
    if "false" in jsonSolutions[0]:
        # failed, so it is not a list of solutions it
        # is a term list
        solutionList.append(termListToString(jsonSolutions))
    else:
        for solution in jsonSolutions:
            solutionList.append(termListToString(solution))

    return solutionList

def termListToString(termList):
    termStringList = []
    for term in termList:
        termStringList.append(termToString(term))
    return ", ".join(termStringList)


def termToString(term):
    if isinstance(term, str):
        return term
    elif termIsList(term):
        value = "["
        hasItem = False
        for listItem in term:
            if hasItem:
                value += ", "
            value += termToString(listItem)
            hasItem = True
        value += "]"
    else:
        value = termName(term)
        if not termIsConstant(term):
            value += "("
            hasArgs = False
            for argTerm in termArgs(term):
                if hasArgs:
                    value += ", "
                value += termToString(argTerm)
                hasArgs = True
            value += ")"
    return value


class HtnPlanner(object):
    def __init__(self, debug=False):
        # Load the library
        if platform == "linux" or platform == "linux2":
            libname = "/usr/bin/libindhtnpy.so"
            self.indhtnLib = ctypes.CDLL(libname)
        else:
            if platform == "darwin":
                # OS X
                libname = "libindhtnpy.dylib"
            elif platform == "win32":
                # Windows...
                libname = "./indhtnpy"
            else:   
                print("Unknown OS: {}".format(platform))
                sys.exit()

            indhtnPath = ctypes.util.find_library(libname)
            if not indhtnPath:
                print("Unable to find the indhtnpy library, please make sure it is on your path.")
                sys.exit()
            try:
                self.indhtnLib = ctypes.CDLL(indhtnPath)
            except OSError:
                print("Unable to load the indhtnpy library.")
                sys.exit()

        # Declare all the function metadata
        self.indhtnLib.SetMemoryBudget.argtypes = [ctypes.c_void_p, ctypes.c_int64]
        self.indhtnLib.CreateHtnPlanner.restype = ctypes.c_void_p
        self.indhtnLib.CreateHtnPlanner.argtypes = [ctypes.c_bool]
        self.indhtnLib.DeleteHtnPlanner.argtypes = [ctypes.c_void_p]
        self.indhtnLib.HtnApplySolution.restype = ctypes.c_bool
        self.indhtnLib.HtnApplySolution.argtypes = [ctypes.c_void_p, ctypes.c_int64]
        self.indhtnLib.HtnCompile.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
        self.indhtnLib.HtnCompile.restype = ctypes.POINTER(ctypes.c_char)
        self.indhtnLib.PrologCompile.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
        self.indhtnLib.PrologCompile.restype = ctypes.POINTER(ctypes.c_char)
        self.indhtnLib.HtnCompileCustomVariables.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
        self.indhtnLib.HtnCompileCustomVariables.restype = ctypes.POINTER(ctypes.c_char)
        self.indhtnLib.PrologCompileCustomVariables.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
        self.indhtnLib.PrologCompileCustomVariables.restype = ctypes.POINTER(ctypes.c_char)
        self.indhtnLib.Compile.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
        self.indhtnLib.Compile.restype = ctypes.POINTER(ctypes.c_char)
        self.indhtnLib.FreeString.argtypes = [ctypes.POINTER(ctypes.c_char)]
        self.indhtnLib.HtnFindAllPlans.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.POINTER(ctypes.POINTER(ctypes.c_char))]
        self.indhtnLib.HtnFindAllPlans.restype = ctypes.POINTER(ctypes.c_char)
        self.indhtnLib.HtnFindAllPlansCustomVariables.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.POINTER(ctypes.POINTER(ctypes.c_char))]
        self.indhtnLib.HtnFindAllPlansCustomVariables.restype = ctypes.POINTER(ctypes.c_char)
        self.indhtnLib.PrologQuery.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.POINTER(ctypes.POINTER(ctypes.c_char))]
        self.indhtnLib.PrologQuery.restype = ctypes.POINTER(ctypes.c_char)
        self.indhtnLib.SetDebugTracing.argtypes = [ctypes.c_int64]
        self.indhtnLib.LogStdErrToFile.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
        self.indhtnLib.PrologQueryToJson.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.POINTER(ctypes.POINTER(ctypes.c_char))]
        self.indhtnLib.PrologQueryToJson.restype = ctypes.POINTER(ctypes.c_char)

        # Now create an instance of the object
        self.obj = self.indhtnLib.CreateHtnPlanner(debug)

    # debug = True to enable debug tracing, False to turn off
    def SetDebugTracing(self, debug):
        self.indhtnLib.SetDebugTracing(debug)

    # Sets the budget for the planner and prolog compiler to use in bytes
    # i.e. 1K budget should be budgetBytes = 1024
    def SetMemoryBudget(self, budgetBytes):
        self.indhtnLib.SetMemoryBudget(self.obj, budgetBytes)

    # In addition to logging to stderr, logs to this file.
    # Clears the file every time it is called
    # Pass "" to stop logging
    def LogToFile(self, fileNameAndPath):
        self.indhtnLib.LogStdErrToFile(self.obj, fileNameAndPath.encode('UTF-8', 'strict'))

    # Returns true if the index is in range, false otherwise
    def ApplySolution(self, index):
        return self.indhtnLib.HtnApplySolution(self.obj, index)

    def HtnCompile(self, value):
        startTime = perf_counter_ns()
        resultPtr = self.indhtnLib.HtnCompile(self.obj, value.encode('UTF-8', 'strict'))
        elapsedTimeNS = perf_counter_ns() - startTime
        perfLogger.info("HtnCompile %s ms", str(elapsedTimeNS / 1000000))

        resultBytes = ctypes.c_char_p.from_buffer(resultPtr).value
        if resultBytes is not None:
            self.indhtnLib.FreeString(resultPtr)
            return resultBytes.decode()
        return resultBytes
    
    def HtnCompileCustomVariables(self, value):
        startTime = perf_counter_ns()
        resultPtr = self.indhtnLib.HtnCompileCustomVariables(self.obj, value.encode('UTF-8', 'strict'))
        elapsedTimeNS = perf_counter_ns() - startTime
        perfLogger.info("HtnCompileCustomVariables %s ms", str(elapsedTimeNS / 1000000))

        resultBytes = ctypes.c_char_p.from_buffer(resultPtr).value
        if resultBytes is not None:
            self.indhtnLib.FreeString(resultPtr)
            return resultBytes.decode()
        return resultBytes

    def PrologCompile(self, value):
        startTime = perf_counter_ns()
        resultPtr = self.indhtnLib.PrologCompile(self.obj, value.encode('UTF-8', 'strict'))
        elapsedTimeNS = perf_counter_ns() - startTime
        perfLogger.info("PrologCompile %s ms", str(elapsedTimeNS / 1000000))

        resultBytes = ctypes.c_char_p.from_buffer(resultPtr).value
        if resultBytes is not None:
            self.indhtnLib.FreeString(resultPtr)
            return resultBytes.decode()
        return resultBytes

    def PrologCompileCustomVariables(self, value):
        startTime = perf_counter_ns()
        resultPtr = self.indhtnLib.PrologCompileCustomVariables(self.obj, value.encode('UTF-8', 'strict'))
        elapsedTimeNS = perf_counter_ns() - startTime
        perfLogger.info("PrologCompileCustomVariables %s ms", str(elapsedTimeNS / 1000000))

        resultBytes = ctypes.c_char_p.from_buffer(resultPtr).value
        if resultBytes is not None:
            self.indhtnLib.FreeString(resultPtr)
            return resultBytes.decode()
        return resultBytes

    def Compile(self, value):
        startTime = perf_counter_ns()
        resultPtr = self.indhtnLib.Compile(self.obj, value.encode('UTF-8', 'strict'))
        elapsedTimeNS = perf_counter_ns() - startTime
        perfLogger.info("PrologCompileCustomVariables %s ms", str(elapsedTimeNS / 1000000))

        resultBytes = ctypes.c_char_p.from_buffer(resultPtr).value
        if resultBytes is not None:
            self.indhtnLib.FreeString(resultPtr)
            return resultBytes.decode()
        return resultBytes

    # returns compileError, solutions
    # compileError = None if no compile error, or a string error message OR a string that starts with "out of memory:"
    #       if it runs out of memory. If it does run out of memory, call SetMemoryBudget() with a larger number and try again
    # solutions = will always be a json string that contains one of two cases:
    #   - If there were no solutions it will be a list of Prolog json terms, the Prolog equivalent is:
    #       False, failureIndex(-1), ...Any Terms in FailureContext...
    #       Unlike PrologQuery it will NOT give you an index of the initial goal that failed it will always be -1.  Just not implemented.
    #   - If there were solutions it will be a list containing all the solutions
    #       each solution is a list of terms which are the operations that represent the plan
    def FindAllPlans(self, value):
        # Pointer to pointer conversion: https://stackoverflow.com/questions/4213095/python-and-ctypes-how-to-correctly-pass-pointer-to-pointer-into-dll
        mem = ctypes.POINTER(ctypes.c_char)()

        startTime = perf_counter_ns()
        resultPtr = self.indhtnLib.HtnFindAllPlans(self.obj, value.encode('UTF-8', 'strict'), ctypes.byref(mem))
        elapsedTimeNS = perf_counter_ns() - startTime
        perfLogger.info("FindAllPlans %s ms: %s", str(elapsedTimeNS / 1000000), value)

        resultBytes = ctypes.c_char_p.from_buffer(resultPtr).value
        if resultBytes is not None:
            self.indhtnLib.FreeString(resultPtr)
            return resultBytes.decode(), None
        else:
            resultQuery = ctypes.c_char_p.from_buffer(mem).value.decode()
            self.indhtnLib.FreeString(mem)
            return None, resultQuery
        
        
    def FindAllPlansCustomVariables(self, value):
        # Pointer to pointer conversion: https://stackoverflow.com/questions/4213095/python-and-ctypes-how-to-correctly-pass-pointer-to-pointer-into-dll
        mem = ctypes.POINTER(ctypes.c_char)()

        startTime = perf_counter_ns()
        resultPtr = self.indhtnLib.HtnFindAllPlansCustomVariables(self.obj, value.encode('UTF-8', 'strict'), ctypes.byref(mem))
        elapsedTimeNS = perf_counter_ns() - startTime
        perfLogger.info("FindAllPlans %s ms: %s", str(elapsedTimeNS / 1000000), value)

        resultBytes = ctypes.c_char_p.from_buffer(resultPtr).value
        if resultBytes is not None:
            self.indhtnLib.FreeString(resultPtr)
            return resultBytes.decode(), None
        else:
            resultQuery = ctypes.c_char_p.from_buffer(mem).value.decode()
            self.indhtnLib.FreeString(mem)
            return None, resultQuery
        

    # returns compileError, solutions
    # compileError = None if no compile error, or a string error message OR a string that starts with "out of memory:"
    #       if it runs out of memory. If it does run out of memory, call SetMemoryBudget() with a larger number and try again
    # solutions = will always be a json string that contains one of two cases:
    #   - If there were no solutions it will be a list of Prolog json terms, the Prolog equivalent is:
    #       False, failureIndex(*Index of term in original query that failed*), ...Any Terms in FailureContext...
    #   - If there were solutions it will be a list containing all the solutions
    #       each is a dictionary where the keys are variable names and the values are what they are assigned to
    def PrologQuery(self, value):
        mem = ctypes.POINTER(ctypes.c_char)()

        startTime = perf_counter_ns()
        resultPtr = self.indhtnLib.PrologQuery(self.obj, value.encode('UTF-8', 'strict'), ctypes.byref(mem))
        elapsedTimeNS = perf_counter_ns() - startTime
        perfLogger.info("PrologQuery %s ms: %s", str(elapsedTimeNS / 1000000), value)

        resultBytes = ctypes.c_char_p.from_buffer(resultPtr).value
        if resultBytes is not None:
            self.indhtnLib.FreeString(resultPtr)
            return resultBytes.decode(), None
        else:
            resultQuery = ctypes.c_char_p.from_buffer(mem).value.decode()
            self.indhtnLib.FreeString(mem)
            return None, resultQuery


    # returns compileError, json
    # compileError = None if no compile error, or a string error message OR a string that starts with "out of memory:"
    #       if it runs out of memory. If it does run out of memory, call SetMemoryBudget() with a larger number and try again
    # json = will always be a json string that contains one of two cases:
    #   - If there were no solutions it will be a list of Prolog json terms, the Prolog equivalent is:
    #       False, failureIndex(*Index of term in original query that failed*), ...Any Terms in FailureContext...
    #   - If there were solutions it will be a list containing all the solutions
    #       each is a dictionary where the keys are variable names and the values are what they are assigned to
    def PrologQueryToJson(self, value):
        if value.strip() == "":
            return None, ""

        mem = ctypes.POINTER(ctypes.c_char)()

        startTime = perf_counter_ns()
        resultPtr = self.indhtnLib.PrologQueryToJson(self.obj, value.encode('UTF-8', 'strict'), ctypes.byref(mem))
        elapsedTimeNS = perf_counter_ns() - startTime
        perfLogger.info("PrologQueryToJson %s ms: %s", str(elapsedTimeNS / 1000000), value)

        resultBytes = ctypes.c_char_p.from_buffer(resultPtr).value
        if resultBytes is not None:
            self.indhtnLib.FreeString(resultPtr)
            return resultBytes.decode(), None
        else:
            resultQuery = ctypes.c_char_p.from_buffer(mem).value.decode()
            self.indhtnLib.FreeString(mem)
            return None, resultQuery

    def __del__(self): 
        self.indhtnLib.DeleteHtnPlanner(self.obj)

