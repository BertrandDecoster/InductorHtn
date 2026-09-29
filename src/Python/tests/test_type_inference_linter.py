"""Tests for the HTN type-inference checker (TYP01x/TYP02x).

Types come from unary ground facts (skill(frostNova) => frostNova : skill).
Predicate-position types are inferred whole-program to a fixpoint. Arguments
are flagged (TYP010) only when their type is provably disjoint from a
well-determined position type (high-signal / near-zero false positives).
"""
import os
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))
python_dir = os.path.dirname(script_dir)
backend_dir = os.path.abspath(os.path.join(python_dir, '../../gui/backend'))
sys.path.insert(0, backend_dir)
sys.path.insert(0, python_dir)

from htn_linter import HtnLinter, TypeInference


def _codes(diags):
    return [d.get('code') if isinstance(d, dict) else d.code for d in diags]


def _of_code(diags, code):
    return [d for d in diags if (d.get('code') if isinstance(d, dict) else d.code) == code]


# --- Constant type extraction from unary facts --------------------------

def test_const_types_from_unary_facts():
    src = """
    skill(frostNova).
    equippableSkill(frostNova).
    effect(frozen).
    enemy(sentinel).
    invulnerable(sentinel).
    """
    ti = TypeInference.from_source(src)
    assert ti.const_types['frostNova'] == {'skill', 'equippableSkill'}
    assert ti.const_types['frozen'] == {'effect'}
    assert ti.const_types['sentinel'] == {'enemy', 'invulnerable'}
    assert {'skill', 'equippableSkill', 'effect', 'enemy', 'invulnerable'} <= ti.type_universe


def test_unary_fact_with_variable_is_not_a_type_source():
    """foo(?x). is not a ground type declaration."""
    src = "skill(?x)."
    ti = TypeInference.from_source(src)
    assert 'skill' not in ti.type_universe


def test_multiarg_facts_are_not_type_sources():
    src = "skillGrants(frostNova, frozen)."
    ti = TypeInference.from_source(src)
    # skillGrants is a relation, not a unary sort
    assert 'skillGrants' not in ti.type_universe
    # and its constants have no sort yet
    assert ti.const_types['frostNova'] == set()


# --- Position inference (fixpoint) --------------------------------------

def test_pos_types_from_fact_relations():
    src = """
    skill(frostNova). skill(lightningStep).
    effect(frozen). effect(electrified).
    skillGrants(frostNova, frozen).
    skillGrants(lightningStep, electrified).
    """
    ti = TypeInference.from_source(src)
    assert ti.pos_types[('skillGrants/2', 0)] == {'skill'}
    assert ti.pos_types[('skillGrants/2', 1)] == {'effect'}


def test_multihop_variable_flow_canuse():
    """?s:skill from equipped+skillGrants => ?e:effect => canUse:(agent,effect)."""
    src = """
    agent(player).
    skill(frostNova). effect(frozen).
    skillGrants(frostNova, frozen).
    equipped(player, frostNova).
    canUse(?w, ?e) :- equipped(?w, ?s), skillGrants(?s, ?e).
    """
    ti = TypeInference.from_source(src)
    assert ti.pos_types[('canUse/2', 1)] == {'effect'}
    assert 'agent' in ti.pos_types[('canUse/2', 0)]


def test_callsite_consensus_types_unused_param():
    """opUseSkill's body never uses arg 1 (the skill); its type comes purely
    from the consensus of call sites passing skill-bound variables."""
    src = """
    agent(player). agent(companion).
    skill(frostNova). skill(tidalWave). effect(frozen). effect(wet).
    skillGrants(frostNova, frozen). skillGrants(tidalWave, wet).
    equipped(player, frostNova). equipped(companion, tidalWave).
    opUseSkill(?w, ?s, ?e, ?t) :- del(), add(hasTag(?t, ?e)).
    useA() :- if(equipped(?w, ?s), skillGrants(?s, ?e)), do(opUseSkill(?w, ?s, ?e, player)).
    useB() :- if(equipped(?w2, ?s2), skillGrants(?s2, ?e2)), do(opUseSkill(?w2, ?s2, ?e2, companion)).
    """
    ti = TypeInference.from_source(src)
    # arg 1 (?s) inferred as skill from call sites despite body not using it
    assert ti.pos_types[('opUseSkill/4', 1)] == {'skill'}
    assert ti.pos_types[('opUseSkill/4', 2)] == {'effect'}


# --- TYP010: disjoint-argument flagging ---------------------------------

def test_disjoint_constant_arg_flagged():
    """The headline case: position is consistently effect; an area is wrong."""
    src = """
    skill(fireball). skill(frostbolt).
    effect(burning). effect(chilled).
    area(town).
    skillApplyEffect(fireball, burning).
    skillApplyEffect(frostbolt, chilled).
    castWrong() :- if(), do(skillApplyEffect(fireball, town)).
    """
    diags = HtnLinter(src).lint()
    typ = _of_code(diags, 'TYP010')
    assert len(typ) == 1
    msg = typ[0].get('message') if isinstance(typ[0], dict) else typ[0].message
    assert 'town' in msg


def test_clean_calls_no_false_positive():
    src = """
    skill(fireball). skill(frostbolt).
    effect(burning). effect(chilled).
    skillApplyEffect(fireball, burning).
    skillApplyEffect(frostbolt, chilled).
    castOk() :- if(), do(skillApplyEffect(fireball, chilled)).
    """
    diags = HtnLinter(src).lint()
    assert _of_code(diags, 'TYP010') == []


def test_polymorphic_position_no_false_positive():
    """A position legitimately holding two disjoint sorts is silenced."""
    src = """
    agent(hero). agent(ally). item(box). item(crate).
    near(hero, x1). near(ally, x2). near(box, x3). near(crate, x4).
    chk() :- if(), do(near(box, x5)).
    """
    diags = HtnLinter(src).lint()
    assert _of_code(diags, 'TYP010') == []


def test_single_evidence_position_no_flag():
    """One defining fact is not enough to authoritatively flag."""
    src = """
    skill(frostNova). effect(frozen). area(town).
    rel(frostNova, frozen).
    chk() :- if(), do(rel(frostNova, town)).
    """
    diags = HtnLinter(src).lint()
    assert _of_code(diags, 'TYP010') == []


def test_variable_carrying_wrong_type_flagged():
    """Multi-hop teeth: a variable bound to the wrong sort is flagged even
    though no literal constant is wrong at the call site."""
    src = """
    enemy(gob). enemy(orc).
    effect(frozen). effect(burning).
    disableEnemy(?e) :- if(enemy(?e)), do(opKO(?e)).
    opKO(?x) :- del(), add(down(?x)).
    misuse() :- if(effect(?f)), do(disableEnemy(?f)).
    """
    diags = HtnLinter(src).lint()
    typ = _of_code(diags, 'TYP010')
    # ?f is an effect; disableEnemy expects an enemy -> disjoint
    assert len(typ) >= 1


# --- Integration: a real, clean ruleset must produce no TYP010 ----------

def test_fortress_loadout_lints_clean():
    """The migrated working ruleset must be free of TYP010 false positives."""
    path = os.path.abspath(os.path.join(
        python_dir, '../../prototypes/fortress-loadout/level.htn'))
    with open(path, 'r', encoding='utf-8') as f:
        src = f.read()
    diags = HtnLinter(src).lint()
    typ = _of_code(diags, 'TYP010')
    msgs = '\n'.join(
        (d.get('message') if isinstance(d, dict) else d.message) for d in typ)
    assert typ == [], f"unexpected TYP010 in fortress-loadout:\n{msgs}"


# --- Optional overrides: %:: comment directives -------------------------

def test_directive_override_flags_swapped_constants():
    src = (
        "agent(hero). cell(c5).\n"
        "%:: moveTo(?a: agent, ?c: cell)\n"
        "moveTo(?a, ?c) :- del(), add(at(?a, ?c)).\n"
        "go() :- if(), do(moveTo(c5, hero)).\n"
    )
    diags = HtnLinter(src).lint()
    assert len(_of_code(diags, 'TYP010')) == 2  # both args swapped


def test_directive_override_clean_call():
    src = (
        "agent(hero). cell(c5).\n"
        "%:: moveTo(?a: agent, ?c: cell)\n"
        "moveTo(?a, ?c) :- del(), add(at(?a, ?c)).\n"
        "go() :- if(), do(moveTo(hero, c5)).\n"
    )
    diags = HtnLinter(src).lint()
    assert _of_code(diags, 'TYP010') == []


def test_legacy_signature_fact_is_ignored():
    """signature/2 is legacy (like type/2): the linter no longer reads it,
    so a swapped call backed only by signature/2 produces nothing."""
    src = """
    agent(hero). cell(c5).
    signature(moveTo, [agent, cell]).
    go() :- if(), do(moveTo(c5, hero)).
    """
    diags = HtnLinter(src).lint()
    assert _of_code(diags, 'TYP010') == []

def test_directive_anchors_position_and_flags():
    """The directive supplies a contract a body-less method couldn't infer."""
    src = (
        "enemy(gob). effect(frozen).\n"
        "%:: disableEnemy(?e: enemy)\n"
        "disableEnemy(?e) :- if(), do(opKO(?e)).\n"
        "opKO(?x) :- del(), add(down(?x)).\n"
        "bad() :- if(effect(?f)), do(disableEnemy(?f)).\n"
    )
    diags = HtnLinter(src).lint()
    assert len(_of_code(diags, 'TYP010')) >= 1


def test_guard_not_inferred_from_do_clause_task():
    """A type guard is a PRECONDITION. A do() task whose name happens to match
    a sort (`open`) must not become a type contract on the head parameter."""
    src = (
        "item(i1). open(o1). open(o2).\n"          # 'open' is a sort
        "unlock(?x) :- if(), do(open(?x)).\n"      # do() task name == sort
        "go() :- if(item(?i)), do(unlock(?i)).\n"  # caller passes an item
    )
    diags = HtnLinter(src).lint()
    assert _of_code(diags, 'TYP010') == []


def test_guard_not_inferred_from_forall_condition():
    """A `forall(Cond, _)` condition binds quantifier-local variables; a type
    goal there must not become a contract on a same-named head parameter."""
    src = (
        "room(r1). room(r2). enemy(e1). enemy(e2).\n"
        "sweep(?e) :- if(forall(enemy(?e), cleared(?e))), do(noop(?e)).\n"
        "noop(?x) :- del(), add(done(?x)).\n"
        "go() :- if(room(?r)), do(sweep(?r)).\n"   # caller passes a room
    )
    diags = HtnLinter(src).lint()
    assert _of_code(diags, 'TYP010') == []


def test_directive_clean_call_no_flag():
    src = (
        "enemy(gob).\n"
        "%:: disableEnemy(?e: enemy)\n"
        "disableEnemy(?e) :- if(), do(opKO(?e)).\n"
        "opKO(?x) :- del(), add(down(?x)).\n"
        "ok() :- if(enemy(?g)), do(disableEnemy(?g)).\n"
    )
    diags = HtnLinter(src).lint()
    assert _of_code(diags, 'TYP010') == []
