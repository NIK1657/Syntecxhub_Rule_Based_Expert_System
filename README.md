# Rule-Based Expert System 

A small expert system: a knowledge base of IF-THEN rules, a working
memory of facts, and an inference engine that applies **forward
chaining** to derive new facts from symptoms you provide, one rule
firing at a time, until nothing new can be concluded.

This version is written **without classes or OOP** — everything is a
plain function operating on plain data (dicts, lists, sets). No
`class`, no `self`, no objects.

## Files

| File                          | Role                                                          |
|--------------------------------|----------------------------------------------------------------|
| `knowledge_base.json`          | The rules (IF-THEN) and a few ready-made demo cases            |
| `expert_system_procedural.py`  | The engine (plain functions) + a CLI                           |

Keeping rules in JSON, separate from the engine, is standard expert-system
design: you (or a "domain expert") can add/edit rules without touching
the inference code.

## How to run

```bash
python3 expert_system_procedural.py
```

You'll get a menu: enter your own symptoms, or pick one of the built-in
demo cases (flu-like, COVID-like, dengue-like, common cold,
gastroenteritis, TB-like, or a standalone emergency symptom).

## Data shapes (no classes — just dicts, lists, sets)

**A rule** is a plain dict, e.g.:

```python
{ "id": "R7",
  "conditions": ["respiratory_symptoms", "loss_of_taste_smell"],
  "conclusion": "covid_pattern",
  "explanation": "Respiratory symptoms plus loss of taste or smell is a pattern often associated with COVID-19." }
```

**The knowledge base** is just a list of these rule dicts (`rules`), loaded
straight from JSON with `json.load()` — no wrapper object.

**Working memory** is a plain `set()` of fact strings, e.g.
`{"fever", "cough", "respiratory_symptoms"}`.

**A trace step** (one fired rule) is also a plain dict: `{"step", "rule_id",
"conditions", "conclusion", "explanation"}`.

A condition prefixed with `!` means "this fact must be absent"
(e.g. `"!fever"`), giving simple negation-as-failure. In this knowledge
base, negated conditions only ever reference raw input symptoms (never
a derived fact), so their truth value can't change mid-inference — that
keeps the forward-chaining loop safe. This engine doesn't do truth
maintenance/retraction, so a negated condition on a *derivable* fact
could behave oddly if that fact appeared late in the chase — worth
knowing if you extend the rule set.

## How the engine works — all functions, no objects

- `load_knowledge_base(path)` — reads the JSON file, returns
  `(rules, demo_cases)` as a plain list and dict.
- `positive_conditions(rule)` / `negative_conditions(rule)` — split a
  rule's conditions into the "must be true" and "must be false" parts.
- `is_satisfied_by(rule, facts)` — checks whether a rule's conditions
  currently hold against a facts set.
- `forward_chain(rules, initial_facts)` — the inference engine itself.
  Starting from your input facts, it repeatedly scans every rule; if a
  rule's conditions are already true and its conclusion isn't known
  yet, it fires: the conclusion is added to the facts set and logged
  to the trace. It keeps re-scanning because a newly added fact can
  satisfy *other* rules' conditions — that's what produces multi-step
  inference, e.g.:
  `cough+sore_throat+runny_nose` → `respiratory_symptoms` →
  (`+loss_of_taste_smell`) → `covid_pattern` → `diagnosis_covid19_suspected`
  → `recommend_isolate_and_test`, a 4-step chain from raw symptoms to
  a recommendation. It stops when a full pass fires nothing new (a
  fixpoint), which is guaranteed to terminate since each rule can only
  fire once.
- `explain(fact, trace)` — walks the trace backwards from one fact to
  return just the rules that were actually needed to derive it, in
  firing order.

**Logging** happens automatically: every fired rule is appended to a
`trace` list with its id, the conditions that were matched, the
conclusion, and a plain-language explanation. `run_session()` prints
this trace top to bottom, and the `explain <fact>` command in the CLI
lets you request the backward-chained reasoning path for just one
conclusion.

## Extending it

To add a new rule, just add an entry to the `rules` array in
`knowledge_base.json` — no code changes needed. To add a new demo case,
add an entry to `demo_cases`.

## Disclaimer

The symptom/diagnosis content here is for demonstrating how an
expert system reasons, not real medical guidance.
