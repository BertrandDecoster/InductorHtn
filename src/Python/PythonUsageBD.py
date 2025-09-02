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
test = HtnPlanner(debugPlan)


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


prog2 = """

"""

facts = ["at(?a,?l).", "hasMana(?a,?m).", "hasTag(?a,?tag).", "allyEffort(?a, ?e)."]


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


f = open("Examples/GameHack8AgentAtTop.htn", "r")
f = open("Examples/Taxi.htn", "r")
prog = f.read()
# prog = prog2

prog = preprocessRuleset(prog)
# print(prog)
result = test.Compile(prog)
if result is not None:
    print("HtnCompile Error:" + result)
    sys.exit()

# Add extra rules
# test.Compile("hasTag(gob, wet).")

####
# Now the database contains *all* of the facts, rules, and tasks from both programs above!
####


query = ""
# query = "aggro(?t, ?a)."
if query:
    output(*test.PrologQuery(query), query, "PrologQuery")
    sys.exit()
if not debugPlan:
    for fact in facts:
        #        pass
        output(*test.PrologQuery(fact), fact, "Fact before")

# HtnPlanner.FindAllPlans()
# Gets all possible plans that are generated by a query (will return a list of plans, each
# which is a list of terms)
# results are returned in Json format (described farther down)


query = "castSkill(player,?s,mimic)."
query = "castSpellToTarget(player,?s,mimic)."
query = "burn2(?x)."
query = "doBlo(?a)."

query = "travel-to(park)."
query = "castTargetedSkill(?s, ?a, ?t)."
query = "planToDamage(?t)."
query = "doElectrocute2(player,gob)."
query = "applyElectrocute(player, gob)."
query = "doWet(gob)."
query = "stunAndBurn(gob)."
query = "skill(?s)."
query = "doElectrocute(gob)."
query = "aggroTarget(gob, player)."
query = "applyEffect(wet, gob)."
query = "applyEffect(electrocute, gob)."
query = "goToSameLocation(companionE,gob)."
query = "castSkill(companionE, gob, electrocute)."
query = "castSpellToTargetSafe(companionE, electrocute, gob)."
query = "stunAndBurn(gob)."
query = "useSkillOnTarget(companionE,electrocute,gob)."
query = "useSkillOnTargetSafe(companionW,wet,gob)."
query = "applySkillTags(waterSkill, gob)."
query = "goToLocation(player, lake)."
query = "applyTag(electrocute, gob)."
query = "applyTagNotPresent(wet, gob)."
query = "planToDamage(gob)."
query = "bringMobToLocation(gob, lake)."
query = "applyTag(electrocute, gob)."
query = "wetAndElectrocute(gob)."
query = "prepareToUseSkill(player, iceBlastSkill, gob)."
query = "stunAndSlowSkillDebug(gob, player, companionF)."
query = "stunAndSlowSkillDebug(gob, companionI, companionF)."
query = "prepareToUseSkill(companionF, fireballSkill, gob)."
query = "prepareToUseSkill(companionI, fireballSkill, gob)."
query = "prepareToApplyTag(companionI, stun, gob)."
query = "stunAndSlowSkillDebug(gob, player, companionF)."
query = "stunAndSlowSkill(gob)."

test.SetLogLevel(SystemTraceType.None_, TraceDetail.Diagnostic)

query = "travel-to(downtown)."
print(f"FIND PLAN FOR QUERY {query}")
output(*test.FindAllPlansCustomVariables(query), query, "FindAllPlans", verbosity=4)
query = "travel-to(park)."

test.SetLogLevel(SystemTraceType.All, TraceDetail.Normal)
query = "travel-to(park)."
print(f"FIND PLAN FOR QUERY {query}")
output(*test.FindAllPlansCustomVariables(query), query, "FindAllPlans", verbosity=4)
# sys.exit()


planNumber = 0
success = test.ApplySolution(planNumber)
print(f"Apply plan {planNumber}")

if not debugPlan:
    for fact in facts:
        output(*test.PrologQuery(fact), fact, "Fact after")


# HtnPlanner.HtnQuery()
# Run a standard Prolog query using the Htn syntax where variables don't have to be
# capitalized, but must have a ? in front
# results are returned in Json format (described farther down)

# HtnPlanner.PrologQuery()
# Run a standard Prolog query
# results are always returned with a ? in front of the name, however
# results are returned in Json format (described farther down)


# Results are always returned as Json.
# Terms are just dictionaries with one key, the name of the term, and one value: a list
# of more terms
# termName(arg1, arg2) => {"termName":[ {"arg1":[]}, {"arg2":[]} ]}

# Here are some examples:
# term that is a constant (aka a term name with no arguments): e.g. tile
term = json.loads('{"tile" : [] }')

# term that is a variable always has a ? in front of it: ?tile
term = json.loads('{"?tile" : [] }')

# term with arguments: tile(position(1), 1)
term = {"tile": [{"position": [1]}, 1]}

# first arg of known term "tile"
# print(term["tile"][0])

# There are some helper functions to make accessing things "prettier"
# foo(bar, goo), tile(position(1), 1)
termList = json.loads(
    '[{"foo" : ["bar", "goo"]}, {"tile" : ["firstArg", "secondArg"] }]'
)

# termName() gives the name of the term
# print(termName(termList[0]))

# termArgs() gets the args for a term
# print(termArgs(termList[0])[0])
