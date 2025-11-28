# See GettingStarted.md for a whole bunch of pointers to understand HTNs, Prolog, etc. This
# file just describes how to use the framework
import json
import pprint
import re

from indhtnpy import *

# The only class for InductorHtn is called HtnPlanner
# Passing true as the (only) argument turns on debug mode
# Traces of what is happening are sent to the system debug output stream which can be
# seen on windows with https://docs.microsoft.com/en-us/sysinternals/downloads/debugview
# These traces are much like the standard Prolog traces and will help you understand how
# the queries and HTN tasks are running and what path they are taking
debugPlan = True
planner = HtnPlanner(debugPlan)

def stringToAcronym(s, keepFirstWord: bool = False):
    if keepFirstWord:
        start = re.split("[A-Z]", s)[0]
    else:
        start = s[0]
    return start + "".join([c for c in s if c.isupper()])


def shortenList(l):
    if len(l) == 1:
        return shorten(l[0])
    return [shorten(e) for e in l]


def shortenDict(d: dict):
    if len(d) == 1:
        v = list(d.values())[0]
        if not (v):
            return {list(d.keys())[0]}

    return {k: shorten(v) for (k, v) in d.items()}


def shorten(o):
    if type(o) == list:
        return shortenList(o)
    if type(o) == dict:
        return shortenDict(o)
    return o


def output(success, result, query, message="Query", verbosity=3):
    if success is not None:
        print(query + " // " + message + " error: " + success)
        sys.exit()

    solutions = json.loads(result)
    if len(solutions) == 1 and not solutions[0]:
        print(f"OUTPUT: Query {query} is true (if it's a plan, it requires nothing)")
        print()
        return

    # print(f"{message} result for \t{query} :")
    # pp = pprint.PrettyPrinter(indent=4)
    # pp.pprint(solutions)
    # s = shorten(solutions)
    # print(f"{message} short result for \t{query} :")
    # pp.pprint(shorten(solutions))

    if (
        len(solutions) == 2
        and "false" in solutions[0]
        and "failureIndex" in solutions[1]
    ):
        print(f"OUTPUT: No solution for query: {query}")
        print()
        return

    for i, solution in enumerate(solutions):
        print(f"OUTPUT #{i}\t: {prettySolution(solution, verbosity)}")
    print()


# Sentence example :
# - [{'companionE': []}, {'gob': []}] -> returns (companionE, gob)
def sentenceToString(l, verbosity):
    answer = []
    for i in range(len(l)):
        answer.append(termToString(l[i], verbosity))
        if i < len(l) - 1:
            answer.append(", ")
    return "(" + "".join(answer) + ")"


# Term example :
# - {'opMoveTo': [{'companionW': []}, {'inn': []}, {'hut': []}]} -> returns opMoveTo(companionW, inn, hut)
def termToString(d, verbosity):
    answer = []

    for k in sorted(d.keys()):
        # answer.append(k)
        v = verbosity
        childV = verbosity
        atom = k

        # m1_applyEffect(electrocute, gob) -> m1applyE(e, g)
        if re.match(r"^(m[0-9]+)_", k):
            term = k.split("_")[-1]
            atom = k[0:3] + atomToString(term, v - 1)
            childV = v - 2

        atomString = atomToString(atom, v)
        # if atomString.startswith('m1'):
        #     atomString = ''

        if d[k] and atomString:
            if isinstance(d[k], list):
                answer.append(atomString + sentenceToString(d[k], childV))
            elif isinstance(d[k], dict):
                if atomString:
                    answer.append(atomString + "(" + termToString(d[k], childV) + ")")
        else:
            # Ex : {'inn': []}
            answer.append(atomString)

    answer = sorted(answer)
    answerSorted = [
        answer[i // 2] if i % 2 == 0 else ", " for i in range(2 * len(answer) - 1)
    ]

    return "".join(answerSorted)


def atomToString(s, verbosity: int):
    if verbosity >= 3:
        return s
    elif verbosity == 2:
        return stringToAcronym(s, keepFirstWord=True)
    elif verbosity == 1:
        return stringToAcronym(s, keepFirstWord=False)
    else:
        return ""


def prettySolution(solution, verbosity):
    if isinstance(solution, list):
        return sentenceToString(solution, verbosity)[1:-1]
    elif isinstance(solution, dict):
        return termToString(solution, verbosity)
    else:
        raise Exception("Unknown")


# HtnPlanner.HtnCompile()
# Compile a program which includes both HTN and Prolog statements
# The HtnCompile() uses the standard Prolog syntax
# Calling HtnCompile() multiple times will keep adding statements to the database.
# You will get an error if some already exist


def preprocessRuleset(ruleset):
    def strip_after_percent(ruleset):
        lines = ruleset.splitlines()  # Split text into lines
        stripped_lines = []

        for line in lines:
            if "%" in line:
                stripped_lines.append(line.split("%")[0])  # Strip everything after '%'
            else:
                stripped_lines.append(line)

        return "\n".join(stripped_lines)  # Join lines back together

    def parse_parentheses(expression):
        # Use regular expression to tokenize the string, keeping parentheses and commas separate
        tokens = re.findall(r"[^\s(),]+|[(),]", expression)

        stack = []
        current = []

        for token in tokens:
            if token == "(":
                # Push the current list to the stack and start a new level
                stack.append(current)
                current = []
            elif token == ")":
                # Pop from the stack and append the current list to it
                if stack:
                    top = stack.pop()
                    top.append(current)
                    current = top
            elif token == ",":
                # Skip commas (they simply separate elements)
                continue
            else:
                # Append the token (whole name or element)
                current.append(token)

        # Return the tree structure
        return current

    def addMethodNameAndArity(text):
        lines = text.split("do(")  # Split text into lines
        dummyMethods = []
        for i in range(len(lines) - 1):
            line = lines[i]
            idx1 = line.rfind(":-")
            idx2 = line[:idx1].rfind("(")
            delta = re.search(r"\s", line[:idx2][::-1]).start()
            fullMethod = line[idx2 - delta : idx1]

            fakeNextLine = lines[i + 1]
            fakeNextLine = "do(" + fakeNextLine
            grammar = parse_parentheses(fakeNextLine)
            doArguments = grammar[1]
            arity = len(doArguments) // 2

            arguments = [
                a.strip() for a in fullMethod.split("(")[1].split(")")[0].split(",")
            ]
            variableArguments = ["?" in arg for arg in arguments]

            if all(variableArguments):
                dummyMethod = "m" + str(arity) + "_" + fullMethod
            else:
                inOpName = "_".join(
                    [
                        "-" if varArg else arg
                        for (arg, varArg) in zip(arguments, variableArguments)
                    ]
                )
                newArgs = ", ".join(
                    [
                        arg
                        for (arg, varArg) in zip(arguments, variableArguments)
                        if varArg
                    ]
                )
                dummyMethod = (
                    "m"
                    + str(arity)
                    + "_"
                    + inOpName
                    + "_"
                    + line[idx2 - delta : idx2]
                    + "("
                    + newArgs
                    + ")"
                )
                pass

            if fullMethod.startswith("castSkill("):
                pass
            dummyMethods.append(dummyMethod)
            lines[i + 1] = dummyMethod + (", " if arity else "") + lines[i + 1]

        lines = "do(".join(lines)  # Join lines back together
        lines + "\n"
        emptyOpForMethods = "\n".join([m + " :- del(), add()." for m in dummyMethods])
        return lines + "\n" + emptyOpForMethods

    # Remove comments
    answer = strip_after_percent(ruleset)

    # goToSameLocation(?a,?t) end with do(opMoveTo(?a, ?aOldLocation, ?tOldLocation))
    # It becomes -> do(m1_goToSameLocation(?a,?t), opMoveTo(?a, ?aOldLocation, ?tOldLocation))
    answer = addMethodNameAndArity(answer)

    # Remove op from all the operators
    # opMoveTo -> MoveTo
    answer = re.sub(r"op([A-Z])", "\\1", answer)

    return answer



# f = open("Examples/Taxi.htn", "r")
# prog_orig = f.read()

prog_orig = """
travel-to(Q) :- 
        if(at(P), walking-distance(P, Q)), 
        do(walk(P, Q)).
    walk(Here, There) :- 
        del(at(Here)), add(at(There)).
    walking-distance(U,V) :- weather-is(good), 
                               distance(U,V,W), =<(W, 3).
    walking-distance(U,V) :- failureContext(1, foo), distance(U,V,W), =<(W, 0.5).
    distance(downtown, park, 2).
    distance(downtown, uptown, 8).
    at(downtown).
    weather-is(good).
    
    """
prog = preprocessRuleset(prog_orig)

result = planner.Compile(prog)
if result is not None:
    print("HtnCompile Error:" + result)
    sys.exit()

# Add extra rules
# test.Compile("hasTag(gob, wet).")

####
# Now the database contains *all* of the facts, rules, and tasks from both programs above!
####

# HtnPlanner.FindAllPlans()
# Gets all possible plans that are generated by a query (will return a list of plans, each
# which is a list of terms)
# results are returned in Json format (described farther down)


with capture_traces(planner) as p:
    p.SetLogLevel(SystemTraceType.All, TraceDetail.Normal)
    query = "travel-to(park)."
    print(f"FIND PLAN FOR QUERY {query}")
    output(*p.FindAllPlansCustomVariables(query), query, "FindAllPlans", verbosity=4)

traces = planner.GetCapturedTraces()
print(traces)

# Import and use tree reconstructor
from HtnTreeReconstructor import HtnTreeReconstructor

print(f"Captured traces: {len(traces)} characters")

# Split traces into lines and reconstruct tree
trace_lines = traces.strip().split("\n") if traces.strip() else []
print(f"Processing {len(trace_lines)} trace lines")
for l in trace_lines:
    print(l)

reconstructor = HtnTreeReconstructor()
nodes = reconstructor.parse_traces(trace_lines)

print(f"\n" + "=" * 60)
print(f"TREE RECONSTRUCTION ANALYSIS")
print(f"=" * 60)

print(f"Reconstructed tree with {len(nodes)} nodes:")
reconstructor.print_tree()


