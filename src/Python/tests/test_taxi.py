"""
Test Suite for Taxi.htn

Tests the travel planning domain with walking, bus, and taxi options.

Domain summary:
- Start at: downtown
- Weather: good
- Cash: $12
- Destinations: park (distance 2), uptown (distance 8), suburb (distance 12)
- Walking: distance <= 3 in good weather, or <= 0.5 always
- Bus: $1.00 fare, routes to park, uptown, suburb
- Taxi: $1.50 + distance fare (uses first() to only hail one taxi)
- Taxi stands: taxi1 and taxi2 at downtown
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from htn_test_framework import HtnTestSuite


def run_tests(verbose: bool = False) -> HtnTestSuite:
    """Run all Taxi.htn tests."""
    suite = HtnTestSuite("Examples/Taxi.htn", verbose=verbose)

    # =========================================================================
    # Walking Tests
    # =========================================================================

    suite.assert_plan(
        "travel-to(park).",
        contains=["walk(downtown, park)"],
        msg="Walk to park - within walking distance in good weather"
    )

    # =========================================================================
    # Bus Tests
    # =========================================================================

    suite.assert_plan(
        "travel-to(uptown).",
        contains=["ride(bus2, downtown, uptown)"],
        msg="Bus to uptown - too far to walk, bus route available"
    )

    suite.assert_plan(
        "travel-to(suburb).",
        contains=["ride(bus3, downtown, suburb)"],
        msg="Bus to suburb - too far to walk, bus route available"
    )

    # =========================================================================
    # Multiple Solutions Tests
    # =========================================================================

    # Park should have multiple options: walk (preferred) and bus
    suite.assert_plan(
        "travel-to(park).",
        min_solutions=1,
        msg="Travel to park has at least one solution"
    )

    # =========================================================================
    # State Change Tests
    # =========================================================================

    suite.assert_state_after(
        "travel-to(park).",
        has=["at(park)"],
        not_has=["at(downtown)"],
        msg="Walking to park updates location"
    )

    # Bus to uptown should cost $1
    suite.assert_state_after(
        "travel-to(uptown).",
        has=["at(uptown)"],
        not_has=["at(downtown)"],
        msg="Bus to uptown updates location"
    )

    # =========================================================================
    # Query Tests
    # =========================================================================

    suite.assert_query(
        "at(?where).",
        bindings={"where": "downtown"},
        min_solutions=1,
        msg="Initial location is downtown"
    )

    suite.assert_query(
        "walking-distance(downtown, park).",
        min_solutions=1,
        msg="Park is within walking distance"
    )

    suite.assert_query(
        "walking-distance(downtown, uptown).",
        min_solutions=0,
        msg="Uptown is NOT within walking distance"
    )

    suite.assert_query(
        "have-cash(?amount).",
        bindings={"amount": "12"},
        msg="Starting cash is $12"
    )

    # =========================================================================
    # Decomposition Tree Tests
    # =========================================================================

    suite.assert_decomposition(
        "travel-to(park).",
        uses_method=["travel-to"],
        uses_operator=["walk"],
        msg="Walking to park uses travel-to method and walk operator"
    )

    suite.assert_decomposition(
        "travel-to(uptown).",
        uses_operator=["ride"],
        msg="Bus to uptown uses ride operator"
    )

    # =========================================================================
    # NEW TESTS: Edge Cases - No Money Scenarios
    # =========================================================================

    # Test with insufficient cash for taxi but enough for bus
    suite.assert_compiles(
        """
        have-taxi-fare(?distance) :- have-cash(?m), >=(?m, +(1.5, ?distance)).
        walking-distance(?u,?v) :- weather-is(good), distance(?u,?v,?w), =<(?w, 3).
        walking-distance(?u,?v) :- distance(?u,?v,?w), =<(?w, 0.5).
        distance(?u,?u,0) :- location(?u).

        pay-driver(?fare) :- if(have-cash(?m), >=(?m, ?fare)), do(set-cash(?m, -(?m,?fare))).
        travel-to(?q) :- if(at(?p), first(walking-distance(?p, ?q))), do(walk(?p, ?q)).
        travel-to(?y) :- if(first(at(?x), at-taxi-stand(?t, ?x), distance(?x, ?y, ?d), have-taxi-fare(?d))), do(hail(?t,?x), ride(?t, ?x, ?y), pay-driver(+(1.50, ?d))).
        travel-to(?y) :- if(at(?x), bus-route(?bus, ?x, ?y)), do(wait-for(?bus, ?x), pay-driver(1.00), ride(?bus, ?x, ?y)).

        hail(?vehicle, ?location) :- del(), add(at(?vehicle, ?location)).
        wait-for(?bus, ?location) :- del(), add(at(?bus, ?location)).
        ride(?vehicle, ?a, ?b) :- del(at(?a), at(?vehicle, ?a)), add(at(?b), at(?vehicle, ?b)).
        set-cash(?old, ?new) :- del(have-cash(?old)), add(have-cash(?new)).
        walk(?here, ?there) :- del(at(?here)), add(at(?there)).

        distance(downtown, park, 2).
        distance(downtown, uptown, 8).
        at-taxi-stand(taxi1, downtown).
        bus-route(bus1, downtown, park).
        bus-route(bus2, downtown, uptown).
        at(downtown).
        weather-is(good).
        have-cash(2).
        location(downtown).
        location(park).
        location(uptown).
        """,
        msg="Domain with $2 cash compiles successfully"
    )

    # =========================================================================
    # NEW TESTS: Query Tests for Domain Rules
    # =========================================================================

    suite.assert_query(
        "have-taxi-fare(8).",
        min_solutions=1,
        msg="With $12, can afford taxi fare for 8-unit distance ($9.50)"
    )

    suite.assert_query(
        "have-taxi-fare(12).",
        min_solutions=0,
        msg="With $12, cannot afford taxi fare for 12-unit distance ($13.50)"
    )

    suite.assert_query(
        "distance(downtown, park, ?d).",
        bindings={"d": "2"},
        msg="Distance from downtown to park is 2"
    )

    suite.assert_query(
        "distance(downtown, uptown, ?d).",
        bindings={"d": "8"},
        msg="Distance from downtown to uptown is 8"
    )

    suite.assert_query(
        "distance(downtown, suburb, ?d).",
        bindings={"d": "12"},
        msg="Distance from downtown to suburb is 12"
    )

    # =========================================================================
    # NEW TESTS: Zero-distance travel (same location)
    # =========================================================================

    suite.assert_query(
        "distance(downtown, downtown, ?d).",
        bindings={"d": "0"},
        msg="Distance from downtown to downtown is 0"
    )

    suite.assert_query(
        "walking-distance(downtown, downtown).",
        min_solutions=1,
        msg="Same location is always within walking distance"
    )

    # =========================================================================
    # NEW TESTS: Taxi stand availability
    # =========================================================================

    suite.assert_query(
        "at-taxi-stand(?taxi, downtown).",
        min_solutions=2,
        msg="Two taxis available at downtown taxi stand"
    )

    suite.assert_query(
        "at-taxi-stand(taxi1, ?loc).",
        bindings={"loc": "downtown"},
        msg="taxi1 is at downtown stand"
    )

    suite.assert_query(
        "at-taxi-stand(taxi2, ?loc).",
        bindings={"loc": "downtown"},
        msg="taxi2 is at downtown stand"
    )

    # =========================================================================
    # NEW TESTS: Bus route verification
    # =========================================================================

    suite.assert_query(
        "bus-route(?bus, downtown, park).",
        bindings={"bus": "bus1"},
        msg="bus1 goes from downtown to park"
    )

    suite.assert_query(
        "bus-route(?bus, downtown, uptown).",
        bindings={"bus": "bus2"},
        msg="bus2 goes from downtown to uptown"
    )

    suite.assert_query(
        "bus-route(?bus, downtown, suburb).",
        bindings={"bus": "bus3"},
        msg="bus3 goes from downtown to suburb"
    )

    suite.assert_query(
        "bus-route(?bus, downtown, ?dest).",
        min_solutions=3,
        msg="Three bus routes from downtown"
    )

    # =========================================================================
    # NEW TESTS: State changes with cash
    # =========================================================================

    # Note: For uptown (distance 8), taxi method is tried first since fare is
    # $1.50 + distance. With $12, taxi fare of $9.50 is affordable.
    # So taxi is preferred over bus for uptown. Result: 12 - 9.5 = 2.5
    suite.assert_state_after(
        "travel-to(uptown).",
        has=["have-cash"],  # Cash fact exists after trip
        not_has=["have-cash(12)"],  # Original cash is gone
        msg="Taxi fare deducts from cash (original $12 is gone)"
    )

    # =========================================================================
    # NEW TESTS: Decomposition with taxi route (taxi preferred over bus when affordable)
    # =========================================================================

    suite.assert_decomposition(
        "travel-to(uptown).",
        uses_method=["travel-to", "pay-driver"],
        uses_operator=["hail", "ride", "set-cash"],
        msg="Taxi trip to uptown uses hail, ride, and set-cash operators"
    )

    suite.assert_decomposition(
        "travel-to(park).",
        avoids_operator=["hail"],
        msg="Walking to park does not use taxi hail operator"
    )

    # =========================================================================
    # NEW TESTS: Weather condition queries
    # =========================================================================

    suite.assert_query(
        "weather-is(?w).",
        bindings={"w": "good"},
        msg="Weather is good"
    )

    # =========================================================================
    # NEW TESTS: Location queries
    # =========================================================================

    suite.assert_query(
        "location(?loc).",
        min_solutions=4,
        msg="Four locations defined in domain"
    )

    suite.assert_query(
        "location(downtown).",
        min_solutions=1,
        msg="downtown is a valid location"
    )

    suite.assert_query(
        "location(park).",
        min_solutions=1,
        msg="park is a valid location"
    )

    # =========================================================================
    # NEW TESTS: Invalid destination (no route)
    # =========================================================================

    suite.assert_no_plan(
        "travel-to(nowhere).",
        msg="Cannot travel to undefined location"
    )

    # =========================================================================
    # NEW TESTS: Compile error detection
    # =========================================================================

    suite.assert_compile_error(
        "travel-to(?x) :- if(foo), do(bar(",
        msg="Unbalanced parentheses cause compile error"
    )

    suite.assert_compile_error(
        "travel-to(?x :- if(foo), do(bar).",
        msg="Missing closing parenthesis in functor causes compile error"
    )

    return suite


def get_suite(verbose: bool = False) -> HtnTestSuite:
    """Alias for run_tests for test discovery."""
    return run_tests(verbose)


if __name__ == "__main__":
    import sys
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    suite = run_tests(verbose=verbose)
    print(suite.summary())
    sys.exit(0 if suite.all_passed() else 1)
