"""Open task: plans exist exactly when the reference has plans, and every plan damages the target."""
import re


def check_instance(want, got, inst):
    target = re.match(r"damage\((\w+)\)", inst["goal"]).group(1)
    if bool(want["plans"]) != bool(got["plans"]):
        return False, (f"reference has {len(want['plans'])} plans, answer has {len(got['plans'])}")
    for i, final in enumerate(got["finals"]):
        if final is None:
            continue
        if f"damaged({target})" not in final:
            return False, f"plan {i + 1} does not leave damaged({target})"
        immune = {f[len('immune('):-1].split(',')[1] for f in final if f.startswith(f"immune({target},")}
        bad = [f for f in final if f.startswith(f"hasTag({target},") and f[:-1].split(',')[1] in immune]
        if bad:
            return False, f"plan {i + 1} gives an immune tag: {bad}"
    return True, ""
