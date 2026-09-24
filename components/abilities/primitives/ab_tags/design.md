# Ab Tags

## Purpose

The tag store of the ability layer: what an entity carries and what it refuses. It uses composition
one level deep and never inheritance. A status is a bundle of atomic tags, as in Dota 2's Hex
(silenced + muted + disarmed + its own `hexed` identity), and belongs to any number of orthogonal
groups, like Baldur's Gate 3 status groups. A single-parent tag tree (GAS `State.Debuff.Stun`) forces
each status into one place; none of the status systems surveyed uses one to decide rules.

A tag has no kind. "Cannot be applied directly" is not a property of `dead`: it just means no ability
grants it. Whether an entity is out of the fight is a per-entity question, `stops(?e, ?t)`, so
freezing can be a finisher in one level and a setup in the next.

## Layer

primitive

## Dependencies

None.

## Operators

| Operator | Description |
|----------|-------------|
| `opGrant(?src, ?e, ?t)` | `?src` puts `?t` on `?e`. Callers guard with `canReceive`. |
| `opRemove(?src, ?e, ?t)` | `?src` takes `?t` off `?e`. |

## Methods

None. The methods that decide whether a tag lands live in `ab_effects`.

## Rules

| Rule | Description |
|------|-------------|
| `has(?e, ?x)` | `?e` carries `?x`, stored or bundled by a stored composite. Two clauses: inside `allOf`, use `holds/2`. |
| `holds(?e, ?x)` | `has/2`, first answer only. |
| `inGroup(?e, ?g)` / `gone(?e)` | A stored tag of `?e` is in group `?g`; `gone` is the group of what left the fight. |
| `suspended(?e, ?x)` / `immuneNow(?e, ?x)` | Immunity to `?x` holds unless a tag of `?e` suspends it (an unbalanced golem can be pushed). |
| `refuses(?e, ?x)` | Immune to `?x`, or to an atom `?x` bundles. |
| `receptive(?e, ?x)` | `?x` (tag, damage type or effect kind) can reach `?e` at all. |
| `canReceive(?e, ?t)` | Receptive, and `?t` is not already stored. |
| `warded(?e, ?x)` | A carried tag wards `?x` (`wards(?t, damage)` covers any `damageType`; `wards(?t, hostile)` any `hostile/1` tag). |
| `forbidden(?e, ?k)` | A carried tag forbids the kind `?k`, or `any`. |
| `stops(?e, ?t)` / `neutralized(?e)` | Out: a stored tag that stops it - anything in group `gone` (dead, frozen, fell); a level may add more. A controlled enemy is set up, not out. |

## Required Facts

| Fact | Description |
|------|-------------|
| `tag(?e, ?t)` | Initial tags (optional) |
| `bundles(?composite, ?atom)` | One level of composition |
| `group(?t, ?g)` | Orthogonal categories; `gone` is read by this layer |
| `immune(?e, ?x)` | `?x` is a tag, a damage type, or `forcedMove` (what "heavy" means) |
| `suspends(?t, ?x)` | While carrying `?t`, immunity to `?x` lapses |
| `stops(?e, ?t)` | Optional: more ways to take `?e` out of the fight |
| `wards(?t, ?x)` | Optional: immunity carried by a tag |
| `forbids(?t, ?kind)` | Optional: what a tag stops its bearer doing |
| `hostile(?t)` | Optional: the tags a `hostile` ward covers |

## Examples

### Example 1: A composite carries its atoms

**Given:** `bundles(frozen, rooted)`, `bundles(frozen, brittle)`, `tag(gob, frozen)`.

**When:** query `holds(gob, rooted)`, `holds(gob, brittle)`

**Then:** both hold; `tag(gob, rooted)` is not stored.

### Example 2: Immunity to an atom refuses the composite

**Given:** `immune(golem, rooted)`.

**When:** query `refuses(golem, frozen)`, `canReceive(golem, frozen)`, `canReceive(golem, wet)`

**Then:** the golem refuses frozen and cannot receive it; wet is fine.

### Example 3: A tag suspends an immunity

**Given:** `immune(golem, forcedMove)`, `suspends(offBalance, forcedMove)`, `bundles(frozen, offBalance)`.

**When:** query `receptive(golem, forcedMove)`, before and after `tag(golem, frozen)`

**Then:** not receptive before; receptive once frozen.

### Example 4: What stops an entity

**Given:** `group(fell, gone)`, `tag(gob, fell)`, `tag(wader, frozen)` with `stops(wader, frozen)`, `tag(tender, frozen)` with no such fact.

**When:** query `neutralized/1` for each

**Then:** gob and wader are neutralized; tender is not.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | Atoms are never stored | Granting and removing a composite stores and deletes only `tag(?e, composite)`. |
| P2 | The gone take nothing | An entity in group `gone` is receptive to nothing. |
| P3 | A stored tag is not stored twice | `canReceive` fails for a tag already stored (operator rule 3). |
| P4 | A tag wards | `wards(flying, fell)`: a flyer is not receptive to `fell`; `wards(invulnerable, damage)` covers every `damageType`. |
| P5 | A tag forbids | `forbids(silenced, spell)` forbids spells only; `forbids(stunned, any)` forbids everything. |
| P6 | Control is not out | A stunned enemy is not neutralized; `wards(invulnerable, hostile)` covers every `hostile/1` tag. |
