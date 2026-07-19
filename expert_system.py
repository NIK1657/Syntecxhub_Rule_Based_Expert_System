import json
import os

def positive_conditions(rule):
    return [c for c in rule["conditions"] if not c.startswith("!")]

def negative_conditions(rule):
    return [c[1:] for c in rule["conditions"] if c.startswith("!")]

def rule_is_satisfied(rule, facts):
    return all(c in facts for c in positive_conditions(rule)) and \
           all(c not in facts for c in negative_conditions(rule))

def pretty_conditions(rule):
    return " AND ".join(
        (f"NOT {c[1:]}" if c.startswith("!") else c) for c in rule["conditions"])

def load_knowledge_base(path):
    with open(path, "r") as f:
        data = json.load(f)
    rules = [
        {
            "id": r["id"],
            "conditions": r["conditions"],
            "conclusion": r["conclusion"],
            "explanation": r["explanation"],
        }
        for r in data["rules"]
    ]
    demo_cases = data.get("cases", {})
    return rules, demo_cases

def all_conclusions(rules):
    return {r["conclusion"] for r in rules}

def all_symptoms(rules):
    all_conditions = {c for r in rules for c in positive_conditions(r)}
    all_conditions |= {c for r in rules for c in negative_conditions(r)}
    return all_conditions - all_conclusions(rules)

def forward_chain(rules, initial_facts):
    facts = set(initial_facts)
    trace = []
    fired_ids = set()
    step = 0
    changed = True
    while changed:
        changed = False
        for rule in rules:
            if rule["id"] in fired_ids:
                continue
            if rule["conclusion"] in facts:
                continue
            if rule_is_satisfied(rule, facts):
                facts.add(rule["conclusion"])
                fired_ids.add(rule["id"])
                step += 1
                trace.append({
                    "step": step,
                    "rule_id": rule["id"],
                    "conditions": list(rule["conditions"]),
                    "conclusion": rule["conclusion"],
                    "explanation": rule["explanation"],
                })
                changed = True  # keep looping - new fact might unlock more rules
    return facts, trace

def explain(fact, trace):
    by_conclusion = {t["conclusion"]: t for t in trace}
    chain = []
    seen = set()
    def backtrack(f):
        entry = by_conclusion.get(f)
        if not entry or entry["rule_id"] in seen:
            return
        seen.add(entry["rule_id"])
        for cond in entry["conditions"]:
            cond = cond[1:] if cond.startswith("!") else cond
            backtrack(cond)
        chain.append(entry)
    backtrack(fact)
    return chain

DIAGNOSIS_PREFIX = "diagnosis_"
RECOMMEND_PREFIX = "recommend_"

def human(fact):
    return fact.replace("_", " ")

def print_trace(trace):
    if not trace:
        print("  (no rules fired - not enough facts to derive anything new)")
        return
    for t in trace:
        print(f"  Step {t['step']:>2} [{t['rule_id']}]: "
              f"IF {' AND '.join(c.replace('!', 'NOT ') for c in t['conditions'])} "
              f"THEN {t['conclusion']}")
        print(f"->{t['explanation']}")

def run_session(rules, facts):
    print("\nFacts entered:", ", ".join(sorted(facts)) if facts else "(none)")
    final_facts, trace = forward_chain(rules, facts)
    print("\nInference trace (forward chaining)")
    print_trace(trace)
    diagnoses = sorted(f for f in final_facts if f.startswith(DIAGNOSIS_PREFIX))
    recommendations = sorted(f for f in final_facts if f.startswith(RECOMMEND_PREFIX))
    print("\n Conclusions ")
    if diagnoses:
        for d in diagnoses:
            print(f"  * {human(d)}")
    else:
        print("  No specific condition could be inferred from the given facts.")
    print("\n Recommendations ")
    if recommendations:
        for r in recommendations:
            print(f"  * {human(r)}")
    else:
        print("  (none)")
    derivable = {t["conclusion"] for t in trace}
    if derivable:
        print("\nYou can ask why any derived fact was reached, e.g.:")
        print(f"  explain {sorted(derivable)[-1]}")
        while True:
            cmd = input("\n> explain <fact> (or press Enter to skip): ").strip()
            if not cmd:
                break
            fact = cmd[len("explain"):].strip() if cmd.startswith("explain") else cmd
            fact = fact.replace(" ", "_")
            if fact not in derivable:
                print(f"  '{fact}' wasn't derived this session. "
                      f"Derivable facts: {', '.join(sorted(derivable))}")
                continue
            chain = explain(fact, trace)
            print(f"\n  Reasoning path to '{fact}':")
            for i, t in enumerate(chain, 1):
                print(f"    {i}. [{t['rule_id']}] "
                      f"{' AND '.join(c.replace('!', 'NOT ') for c in t['conditions'])} "
                      f"=> {t['conclusion']}")
                print(f"       ({t['explanation']})")

    print("\nDisclaimer: this is not medical advice.")

def manual_entry(rules):
    symptoms = sorted(all_symptoms(rules))
    print("\nRecognized symptoms this knowledge base knows about:")
    for i, s in enumerate(symptoms, 1):
        end = "\n" if i % 4 == 0 else "  "
        print(f"{human(s):<22}", end=end)
    print("\n\nEnter the symptoms you have, separated by commas")
    print("(you can use spaces or underscores, e.g. 'fever, sore throat, cough'):")
    line = input("> ").strip().lower()
    facts = {tok.strip().replace(" ", "_") for tok in line.split(",") if tok.strip()}
    unknown = facts - all_symptoms(rules)
    if unknown:
        print(f"(note: not in the knowledge base, but keeping them anyway: "
              f"{', '.join(sorted(unknown))})")
    return facts

def main():
    here = os.path.dirname(os.path.abspath(__file__))
    rules, demo_cases = load_knowledge_base(os.path.join(here, "knowledge_base.json"))
    print("=" * 60)
    print("  RULE-BASED EXPERT SYSTEM - forward chaining")
    print("=" * 60)
    while True:
        print("\nWhat would you like to do?")
        print("  m) Enter your own symptoms")
        for key, case in sorted(demo_cases.items(), key=lambda kv: int(kv[0])):
            print(f"  {key}) Run case: {case['label']}")
        print("  q) Quit")
        choice = input("> ").strip().lower()
        if choice == "q":
            break
        elif choice == "m":
            facts = manual_entry(rules)
        elif choice in demo_cases:
            facts = set(demo_cases[choice]["facts"])
        else:
            print("Not a valid option, try again.")
            continue
        run_session(rules, facts)

if __name__ == "__main__":
    main()