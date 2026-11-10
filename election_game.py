import json
import math
import os
import random
import webbrowser
from pathlib import Path

# State data: (immigration, trade, partisanship, abortion, electoral_votes, foreign_policy[, gun_policy])
# immigration:  1 = open borders,  10 = strict control
# trade:        1 = free market,   10 = protectionist
# partisanship: 1 = very Republican, 10 = very Democratic
# abortion:     1 = pro-life,      10 = pro-choice
# foreign:      1 = dovish,        10 = hawkish
# gun:          1 = pro-gun (fewest restrictions), 10 = strict gun control
# State values are loaded from scenarios.json (made with state_editor.html).
STATES = {}               # the scenario currently being played (set in main)
DEFAULT_GUN = 5           # gun policy used for a state that has no value (old files)

# Two-letter codes used by the results map (map_template.html). The names must be
# spelled exactly like the state names in the game data / scenarios.json.
STATE_CODES = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR", "California": "CA",
    "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE", "Florida": "FL", "Georgia": "GA",
    "Hawaii": "HI", "Idaho": "ID", "Illinois": "IL", "Indiana": "IN", "Iowa": "IA",
    "Kansas": "KS", "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD",
    "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS",
    "Missouri": "MO", "Montana": "MT", "Nebraska": "NE", "Nevada": "NV", "New Hampshire": "NH",
    "New Jersey": "NJ", "New Mexico": "NM", "New York": "NY", "North Carolina": "NC",
    "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK", "Oregon": "OR", "Pennsylvania": "PA",
    "Rhode Island": "RI", "South Carolina": "SC", "South Dakota": "SD", "Tennessee": "TN",
    "Texas": "TX", "Utah": "UT", "Vermont": "VT", "Virginia": "VA", "Washington": "WA",
    "Washington DC": "DC", "West Virginia": "WV", "Wisconsin": "WI", "Wyoming": "WY",
}


def read_issue_text(raw_texts):
    """Names and questions for one election. Anything missing or empty falls back to the default."""
    out = {}
    for key, (name, low, high) in DEFAULT_ISSUE_TEXT.items():
        entry = raw_texts.get(ISSUE_JSON_KEYS[key]) if isinstance(raw_texts, dict) else None
        entry = entry if isinstance(entry, dict) else {}

        def pick(field, default):
            value = entry.get(field)
            return value.strip() if isinstance(value, str) and value.strip() else default
        if key == "partisanship":
            out[key] = (pick("label", name), low, high)   # the scale text stays fixed
        else:
            out[key] = (pick("label", name), pick("low", low), pick("high", high))
    return out


def read_senate(raw_year, state_names):
    """The Senate data of one election, or None if it has none. Raises ValueError for a bad value."""
    if not isinstance(raw_year, dict):
        return None
    hold = raw_year.get("holdover", {})
    holdover = {}
    for p in ("R", "D"):
        n = hold.get(p, 0) if isinstance(hold, dict) else 0
        if not isinstance(n, int) or isinstance(n, bool) or not 0 <= n <= 100:
            raise ValueError(f"seats not up for election must be a whole number from 0 to 100")
        holdover[p] = n
    caucuses, seen = [], set()
    for c in raw_year.get("caucuses") or []:
        if not isinstance(c, dict):
            continue
        cname = c.get("name")
        cname = cname.strip() if isinstance(cname, str) else ""
        if not cname or cname.lower() == LOYALISTS.lower() or cname.lower() in seen:
            raise ValueError(f"caucus name {cname!r} is empty, used twice or reserved")
        seen.add(cname.lower())
        raw_stances = c.get("stances") if isinstance(c.get("stances"), dict) else {}
        stances = {}
        for key, json_key in ISSUE_JSON_KEYS.items():
            v = raw_stances.get(json_key, 5)
            if not isinstance(v, int) or isinstance(v, bool) or not 1 <= v <= 10:
                raise ValueError(f"caucus {cname}: {json_key} must be a whole number from 1 to 10")
            stances[key] = v
        caucuses.append({"name": cname, "stances": stances})
    caucus_names = {c["name"] for c in caucuses}

    def caucus_of(entry):
        v = entry.get("caucus") if isinstance(entry, dict) else None
        return v if isinstance(v, str) and v in caucus_names else ""

    senators = []
    for x in raw_year.get("senators") or []:
        if isinstance(x, dict) and x.get("party") in ("R", "D"):
            nm = x.get("name")
            senators.append({"name": nm.strip() if isinstance(nm, str) else "", "party": x["party"],
                             "caucus": caucus_of(x)})
    seats = {}
    for st, items in (raw_year.get("seats") or {}).items():
        if st not in state_names or st == "Washington DC" or not isinstance(items, list):
            continue
        built = []
        for item in items[:2]:
            seat = {}
            for p, fallback in (("R", "Republican candidate"), ("D", "Democratic candidate")):
                c = item.get(p) if isinstance(item, dict) else None
                c = c if isinstance(c, dict) else {}
                adv = c.get("advantage", 5)
                if not isinstance(adv, int) or isinstance(adv, bool) or not 1 <= adv <= SENATE_ADVANTAGE_MAX:
                    raise ValueError(f"{st}: advantage must be a whole number from 1 to {SENATE_ADVANTAGE_MAX}")
                name = c.get("name")
                name = name.strip() if isinstance(name, str) else ""
                seat[p] = {"name": name or fallback, "advantage": adv, "caucus": caucus_of(c)}
            built.append(seat)
        if built:
            seats[st] = built
    return {"holdover": holdover, "seats": seats, "caucuses": caucuses, "senators": senators} if seats else None


def read_house(raw_year, state_names):
    """Optional House election data. Each state stores a list of members; each member is a seat object with a party, name, caucus and advantage."""
    if not isinstance(raw_year, dict):
        return None
    caucuses, seen = [], set()
    for c in raw_year.get("caucuses") or []:
        if not isinstance(c, dict):
            continue
        name = c.get("name")
        name = name.strip() if isinstance(name, str) else ""
        if not name or name.lower() == LOYALISTS.lower() or name.lower() in seen:
            raise ValueError(f"house caucus name {name!r} is empty, used twice or reserved")
        seen.add(name.lower())
        raw_stances = c.get("stances") if isinstance(c.get("stances"), dict) else {}
        stances = {}
        for key, json_key in ISSUE_JSON_KEYS.items():
            v = raw_stances.get(json_key, 5)
            if not isinstance(v, int) or isinstance(v, bool) or not 1 <= v <= 10:
                raise ValueError(f"house caucus {name}: {json_key} must be a whole number from 1 to 10")
            stances[key] = v
        caucuses.append({"name": name, "stances": stances})
    caucus_names = {c["name"] for c in caucuses}

    def caucus_of(entry):
        v = entry.get("caucus") if isinstance(entry, dict) else None
        return v if isinstance(v, str) and v in caucus_names else ""

    members = []
    for x in raw_year.get("members") or []:
        if not isinstance(x, dict):
            continue
        party = x.get("party")
        if party not in ("R", "D"):
            continue
        nm = x.get("name")
        adv = x.get("advantage", 5)
        if not isinstance(adv, int) or isinstance(adv, bool) or not 1 <= adv <= HOUSE_ADVANTAGE_MAX:
            raise ValueError(f"house member advantage must be a whole number from 1 to {HOUSE_ADVANTAGE_MAX}")
        members.append({
            "name": nm.strip() if isinstance(nm, str) else "",
            "party": party,
            "advantage": adv,
            "caucus": caucus_of(x),
        })

    seats = {}
    for st, items in (raw_year.get("seats") or {}).items():
        if st not in state_names or not isinstance(items, list):
            continue
        built = []
        for item in items:
            if not isinstance(item, dict):
                continue
            party = item.get("party")
            if party not in ("R", "D"):
                continue
            adv = item.get("advantage", 5)
            if not isinstance(adv, int) or isinstance(adv, bool) or not 1 <= adv <= HOUSE_ADVANTAGE_MAX:
                raise ValueError(f"{st}: house member advantage must be a whole number from 1 to {HOUSE_ADVANTAGE_MAX}")
            nm = item.get("name")
            built.append({
                "name": nm.strip() if isinstance(nm, str) else "",
                "party": party,
                "advantage": adv,
                "caucus": caucus_of(item),
            })
        if built:
            seats[st] = built
    return {"seats": seats, "caucuses": caucuses, "members": members} if seats else None


def load_scenarios():
    """Return ({scenario name: {state: tuple}}, {scenario name: issue texts}, {scenario name: senate data}, {scenario name: house data})."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scenarios.json")
    if not os.path.exists(path):
        raise SystemExit("scenarios.json was not found in the game folder. Put it next to election_game.py.")
    try:
        with open(path, encoding="utf-8") as f:
            whole = json.load(f)
        raw = whole["scenarios"]
        raw_texts = whole.get("issue_text", {})
        if not isinstance(raw_texts, dict):
            raw_texts = {}
        out, texts, senates, houses = {}, {}, {}, {}
        raw_senate = whole.get("senate", {})
        raw_house = whole.get("house", {})
        if not isinstance(raw_senate, dict):
            raw_senate = {}
        if not isinstance(raw_house, dict):
            raw_house = {}
        for name, states in raw.items():
            out[name] = {
                st: (v["immigration"], v["trade"], v["partisanship"], v["abortion"],
                    v["electoral_college"], v["foreign_policy"], v.get("gun_policy", DEFAULT_GUN))
                for st, v in states.items()
            }
            texts[name] = read_issue_text(raw_texts.get(name))
            try:
                senate = read_senate(raw_senate.get(name), out[name])
            except Exception as error:
                print(f"Senate data of the {name} election was ignored ({error}).")
                senate = None
            if senate:
                senates[name] = senate
            try:
                house = read_house(raw_house.get(name), out[name])
            except Exception as error:
                print(f"House data of the {name} election was ignored ({error}).")
                house = None
            if house:
                houses[name] = house
    except Exception as error:
        raise SystemExit(f"Could not read scenarios.json ({error}).")
    if not out:
        raise SystemExit("scenarios.json has no elections in it.")
    return out, texts, senates, houses


def choose_scenario(scenarios):
    names = list(scenarios)
    if len(names) == 1:
        return names[0]
    print("\nAvailable elections: " + ", ".join(names))
    while True:
        pick = input("Which election do you want to play? ").strip()
        if pick in scenarios:
            return pick
        print("  Please type one of the names above exactly.")


# ---------------------------------------------------------------------------
# TUNING SECTION - change these numbers to rebalance the game
# ---------------------------------------------------------------------------

WEIGHTS = {
    "immigration": 1.0,
    "trade": 1.0,
    "partisanship": 1.25,
    "abortion": 1.0,
    "foreign": 1.0,
    "gun": 1.0,
}

POPULARITY_POINTS = 1.0
HOME_STATE_POINTS = 5
CAMPAIGN_STOPS = 3
CAMPAIGN_POINTS = 1
VP_STATE_POINTS = 1

SENATE_TOP_TICKET_DIVISOR = 6
SENATE_DIVIDED_DIVISOR = 3
SENATE_ADVANTAGE_MAX = 50
HOUSE_TOP_TICKET_DIVISOR = 6
HOUSE_DIVIDED_DIVISOR = 3
HOUSE_ADVANTAGE_MAX = 50

CAUCUS_MAX_DISAGREEMENT = 20
CAUCUS_MOVE_PER_TURN = 1
LOYALISTS = "Party loyalists"

SPOILER_TIERS = [
    (6, 20),
    (12, 14),
    (24, 8),
    (36, 3),
]

ISSUES = ["trade", "immigration", "partisanship", "abortion", "foreign", "gun"]

DEFAULT_ISSUE_TEXT = {
    "trade": ("Trade", "free market", "protectionist"),
    "immigration": ("Immigration", "open borders", "strict control"),
    "partisanship": ("Partisanship", "very Republican", "very Democratic"),
    "abortion": ("Abortion", "pro-life", "pro-choice"),
    "foreign": ("Foreign policy", "dovish", "hawkish"),
    "gun": ("Gun policy", "pro-gun", "strict gun control"),
}
ISSUE_JSON_KEYS = {"trade": "trade", "immigration": "immigration", "partisanship": "partisanship",
                   "abortion": "abortion", "foreign": "foreign_policy", "gun": "gun_policy"}
ISSUE_TEXT = dict(DEFAULT_ISSUE_TEXT)


def issue_prompt(key):
    name, low, high = ISSUE_TEXT[key]
    return f"{name} (1 = {low}, 10 = {high})"

TAGS = {"Republican": "[R]", "Democrat": "[D]", "Third Party": "[3]", "Fourth Party": "[4]"}


def ask_number(prompt, low, high):
    while True:
        text = input(f"{prompt} [{low}-{high}]: ").strip()
        if text.isdigit() and low <= int(text) <= high:
            return int(text)
        print(f"  Please enter a whole number from {low} to {high}.")


def ask_yes_no(prompt):
    while True:
        text = input(f"{prompt} (y/n): ").strip().lower()
        if text in ("y", "yes"):
            return True
        if text in ("n", "no"):
            return False
        print("  Please type y or n.")


def ask_stances(party, partisan_low, partisan_high, partisan_text, with_popularity=True):
    answers = {
        "trade": ask_number(issue_prompt("trade"), 1, 10),
        "immigration": ask_number(issue_prompt("immigration"), 1, 10),
        "partisanship": ask_number(partisan_text, partisan_low, partisan_high),
        "abortion": ask_number(issue_prompt("abortion"), 1, 10),
        "foreign": ask_number(issue_prompt("foreign"), 1, 10),
        "gun": ask_number(issue_prompt("gun"), 1, 10),
    }
    if with_popularity:
        answers["popularity"] = ask_number("Personal popularity (1 = unpopular, 10 = very popular)", 1, 10)
    return answers


STATE_ALIASES = {"dc": "Washington DC", "d.c.": "Washington DC",
                 "washington d.c.": "Washington DC", "washington, dc": "Washington DC",
                 "ma": "Massachusetts", "pa": "Pennsylvania", "ct": "Connecticut",
                 "nc": "North Carolina", "sc": "South Carolina", "de": "Delaware",
                 "nh": "New Hampshire"}


def ask_state(prompt):
    lookup = {name.lower(): name for name in STATES}
    lookup.update({k: v for k, v in STATE_ALIASES.items() if v in STATES})
    while True:
        text = " ".join(input(f"{prompt}: ").split()).lower()
        if text in lookup:
            return lookup[text]
        print("  That is not a state in this election. Type a state name, for example Ohio.")


def finish_candidate(c, use_vp):
    print(f"\nCampaign: choose {CAMPAIGN_STOPS} stops. You may pick the same state "
          f"more than once; each stop adds +{CAMPAIGN_POINTS} there.")
    c["campaign"] = [ask_state(f"  Campaign stop {i} of {CAMPAIGN_STOPS}")
                     for i in range(1, CAMPAIGN_STOPS + 1)]

    if use_vp:
        while True:
            c["vp"] = input("\nType your vice president's name: ").strip()
            if c["vp"]:
                break
            print("  Every candidate must choose a vice president.")
        c["vp_state"] = ask_state("Vice president's home state")
    else:
        c["vp"], c["vp_state"] = "", None

    stops = {}
    for st in c["campaign"]:
        stops[st] = stops.get(st, 0) + 1
    line = (f"\n  {c['name']}: home state {c['home_state']} (+{HOME_STATE_POINTS}), campaign: "
            + ", ".join(f"{st} x{n}" for st, n in stops.items()))
    if c["vp_state"]:
        line += f", VP {c['vp']} from {c['vp_state']} (+{VP_STATE_POINTS})"
    print(line + ".")
    if c["multiplier"] < 1.0:
        print(f"  All of these bonuses are scaled by the strength factor {c['multiplier']:.1f}.")


def ask_main_candidate(number, party, use_vp):
    print(f"\n=== Candidate {number} ({party}) ===")
    name = input("Name: ").strip() or f"Candidate {number}"
    home = ask_state("Home state")
    if party == "Republican":
        text, low, high = f"{ISSUE_TEXT['partisanship'][0]} (1 = extreme Republican, 5 = moderate)", 1, 5
    else:
        text, low, high = f"{ISSUE_TEXT['partisanship'][0]} (6 = moderate, 10 = extreme Democrat)", 6, 10
    candidate = ask_stances(party, low, high, text)
    candidate.update({"name": name, "party": party, "multiplier": 1.0, "penalty": 0.0,
                      "home_state": home})
    finish_candidate(candidate, use_vp)
    return candidate


def ask_minor_candidate(label, use_vp):
    print(f"\n=== {label} Candidate ===")
    name = input("Name: ").strip() or label
    home = ask_state("Home state")
    strength = ask_number("Strength (1 = very weak, 5 = as strong as the main candidates)", 1, 5)
    text = f"{ISSUE_TEXT['partisanship'][0]} (1 = very Republican, 9 = very Democratic)"
    candidate = ask_stances(label, 1, 9, text)
    candidate.update({
        "name": name,
        "party": label,
        "strength": strength,
        "multiplier": strength / 5,
        "penalty": 0.0,
        "home_state": home,
    })
    finish_candidate(candidate, use_vp)
    return candidate


def ask_party(label, party):
    print(f"\n=== {label} Party platform (Senate elections) ===")
    name = ISSUE_TEXT["partisanship"][0]
    if party == "Republican":
        text, low, high = f"{name} (1 = extreme Republican, 5 = moderate)", 1, 5
    else:
        text, low, high = f"{name} (6 = moderate, 10 = extreme Democrat)", 6, 10
    platform = ask_stances(party, low, high, text, with_popularity=False)
    platform.update({"party": party, "name": f"{label} Party"})
    return platform


def ideology_distance(a, b):
    return sum(abs(a[issue] - b[issue]) for issue in ISSUES)


def spoiler_penalty(distance):
    for max_distance, penalty in SPOILER_TIERS:
        if distance <= max_distance:
            return penalty
    return 0


def apply_third_party_effect(c1, c2, c3):
    d1 = ideology_distance(c3, c1)
    d2 = ideology_distance(c3, c2)
    factor = c3["multiplier"]

    print(f"\n=== {c3['party'].upper()} ANALYSIS ===")
    print(f"Ideology distance to {c1['name']} (R): {d1}")
    print(f"Ideology distance to {c2['name']} (D): {d2}")

    if d1 < d2:
        victims = [(c1, d1, 1.0)]
    elif d2 < d1:
        victims = [(c2, d2, 1.0)]
    else:
        victims = [(c1, d1, 0.5), (c2, d2, 0.5)]

    for victim, dist, share in victims:
        base = spoiler_penalty(dist)
        added = base * factor * share
        victim["penalty"] += added
        print(f"{c3['name']} is closer to {victim['name']}.")
        print(f"  Base penalty: {base} points per state, "
              f"strength factor: {factor:.1f}, "
              f"final penalty: -{added:.1f} points per state for {victim['name']}.")
        if victim["penalty"] != added:
            print(f"  {victim['name']}'s total spoiler penalty is now -{victim['penalty']:.1f} per state.")
    if all(spoiler_penalty(d) == 0 for _, d, _ in victims):
        print(f"{c3['name']} is too different from both to hurt anyone.")


def state_bonus(c, state_name):
    pts = 0.0
    if c.get("home_state") == state_name:
        pts += HOME_STATE_POINTS
    pts += CAMPAIGN_POINTS * c.get("campaign", []).count(state_name)
    if c.get("vp_state") == state_name:
        pts += VP_STATE_POINTS
    return pts


def ticket_label(c):
    return f"{c['name']}/{c['vp']}" if c.get("vp") else c["name"]


def ticket_text(c):
    return f"The {ticket_label(c)} ticket" if c.get("vp") else c["name"]


def issue_score(candidate, state):
    imm, trade, part, abort, _ev, foreign = state[:6]
    gun = state[6] if len(state) > 6 else DEFAULT_GUN
    total = 0.0
    total += WEIGHTS["immigration"] * (9 - abs(imm - candidate["immigration"]))
    total += WEIGHTS["trade"] * (9 - abs(trade - candidate["trade"]))
    total += WEIGHTS["partisanship"] * (9 - abs(part - candidate["partisanship"]))
    total += WEIGHTS["abortion"] * (9 - abs(abort - candidate["abortion"]))
    total += WEIGHTS["foreign"] * (9 - abs(foreign - candidate["foreign"]))
    total += WEIGHTS["gun"] * (9 - abs(gun - candidate["gun"]))
    return total


def score(candidate, state, state_name):
    total = issue_score(candidate, state)
    total += POPULARITY_POINTS * candidate["popularity"]
    total += state_bonus(candidate, state_name)
    return total * candidate["multiplier"] - candidate["penalty"]


def vote_shares(scores):
    positive = [max(s, 0.0) for s in scores]
    total = sum(positive)
    if total <= 0:
        return [100.0 / len(scores)] * len(scores)
    return [100.0 * p / total for p in positive]


def round_to_100(values, digits=1):
    unit = 10 ** digits
    scaled = [v * unit for v in values]
    floors = [int(x) for x in scaled]
    missing = round(100 * unit) - sum(floors)
    order = sorted(range(len(values)), key=lambda i: scaled[i] - floors[i], reverse=True)
    for i in order[:max(missing, 0)]:
        floors[i] += 1
    return [f / unit for f in floors]


def join_names(names):
    if len(names) <= 2:
        return " and ".join(names)
    return ", ".join(names[:-1]) + " and " + names[-1]


def run_election(candidates, caucus_decides=False):
    votes = [0] * len(candidates)
    popular = [0.0] * len(candidates)
    margins = []
    state_results = []
    tied_states = []

    print("\n=== ELECTION RESULTS BY STATE ===")
    for state_name, data in STATES.items():
        ev = data[4]
        scores = [score(c, data, state_name) for c in candidates]
        best = max(scores)
        leaders = [i for i, s in enumerate(scores) if best - s < 1e-9]
        is_tie = len(leaders) > 1
        winner = random.choice(leaders)

        shares = vote_shares(scores)
        ordered = sorted(shares, reverse=True)
        gap = 0.0 if is_tie else ordered[0] - ordered[1]
        for i, share in enumerate(shares):
            popular[i] += ev * share

        votes[winner] += ev
        c = candidates[winner]
        note = ""
        if is_tie:
            names = join_names([candidates[i]["name"] for i in leaders])
            note = f" (TIE between {names}: coin flip, each had an equal chance)"
            tied_states.append((state_name, names))
        print(f"{TAGS[c['party']]} {state_name:<16} {c['name']} wins ({ev} EV){note}")
        margins.append((gap, state_name, c["name"]))
        state_results.append({
            "state": state_name,
            "code": STATE_CODES.get(state_name),
            "ev": ev,
            "winner": winner,
            "margin": round(gap, 1),
            "shares": round_to_100(shares),
            "scores": [round(x, 1) for x in scores],
            "tie": is_tie,
            "tied": leaders if is_tie else [],
        })

    if tied_states:
        print(f"\n=== TIED STATES ({len(tied_states)}) ===")
        print("When candidates have exactly the same score in a state, the game flips a fair coin:")
        print("every tied candidate has an equal chance (50/50 with two).")
        for state_name, names in tied_states:
            winner_index = next(r["winner"] for r in state_results if r["state"] == state_name)
            print(f"{state_name}: {names} -> {candidates[winner_index]['name']} won the coin flip")

    margins.sort()
    print("\n=== THE 3 CLOSEST STATES ===")
    for margin, state_name, winner_name in margins[:3]:
        print(f"{state_name}: margin {margin:.1f} percentage points, winner {winner_name}")

    total_ev = sum(d[4] for d in STATES.values())
    needed = total_ev // 2 + 1
    popular_pct = round_to_100([100.0 * p / sum(popular) for p in popular])

    print("\n=== FINAL RESULTS ===")
    for c, v in zip(candidates, votes):
        print(f"{TAGS[c['party']]} {ticket_label(c)}: {v} electoral votes")
    print(f"({needed} needed to win)")

    top = max(votes)
    top_candidates = [c for c, v in zip(candidates, votes) if v == top]
    print("\n=== POPULAR VOTE ===")
    print("(each state counts its electoral votes x the candidate's share of that state)")
    for c, pct, pts in zip(candidates, popular_pct, popular):
        print(f"{TAGS[c['party']]} {ticket_label(c)}: {pct:.1f}%  ({pts:,.0f} points)")

    best_pop = max(popular)
    pop_leaders = [i for i, p in enumerate(popular) if best_pop - p < 1e-9]
    popular_note = ""
    if len(pop_leaders) == 1 and len(top_candidates) == 1:
        pop_name = candidates[pop_leaders[0]]["name"]
        if candidates[pop_leaders[0]] is top_candidates[0]:
            popular_note = f"{pop_name} won the popular vote and also has the most electoral votes."
        else:
            popular_note = (f"{pop_name} won the popular vote, but "
                            f"{top_candidates[0]['name']} won more electoral votes.")
    if popular_note:
        print(popular_note)

    deadlock = len(top_candidates) > 1 or top < needed
    if deadlock and caucus_decides:
        why = (f"The top candidates are tied on {top} electoral votes." if len(top_candidates) > 1
               else f"No candidate reached {needed} electoral votes.")
        print(f"\n{why}")
        print("The election is deadlocked: the Senate caucuses will decide it (see below).")
        verdict = f"{why} The Senate caucuses decide the election."
    elif len(top_candidates) > 1:
        print("\nIt's a tie! No clear winner.")
        verdict = "It's a tie! No clear winner."
    elif top >= needed:
        print(f"\n*** {ticket_text(top_candidates[0])} wins the election! ***")
        verdict = f"{ticket_text(top_candidates[0])} wins the election!"
    else:
        print(f"\nNo candidate reached {needed} electoral votes.")
        print("In real life the House of Representatives would decide.")
        print(f"In this game, {ticket_text(top_candidates[0])} (most electoral votes) wins the House vote.")
        verdict = (f"No candidate reached {needed} electoral votes. In this game, "
                   f"{ticket_text(top_candidates[0])} (most electoral votes) wins the House vote.")

    return {
        "candidates": [{"name": c["name"], "party": c["party"], "ticket": ticket_label(c),
                        "votes": v, "popular_pct": pct, "popular_points": round(pts, 1)}
                       for c, v, pct, pts in zip(candidates, votes, popular_pct, popular)],
        "states": state_results,
        "total_ev": total_ev,
        "needed": needed,
        "verdict": verdict,
        "popular_note": popular_note,
        "deadlock": deadlock,
    }


PARTY_NAME = {"R": "Republican", "D": "Democratic"}
PARTY_PLURAL = {"R": "Republicans", "D": "Democrats"}


def senate_control(final, candidates, pres_winner):
    needed = (final["R"] + final["D"]) // 2 + 1
    if final["R"] >= needed:
        return "R", False
    if final["D"] >= needed:
        return "D", False
    if final["R"] == final["D"] and pres_winner is not None:
        party = candidates[pres_winner]["party"]
        if party in ("Republican", "Democrat"):
            return ("R" if party == "Republican" else "D"), True
    return None, False


def run_senate(senate, candidates, platforms, pres_winner):
    c_rep, c_dem = candidates[0], candidates[1]
    platform = {"R": platforms[0], "D": platforms[1]}
    pres = {"R": c_rep, "D": c_dem}

    gap = c_rep["popularity"] - c_dem["popularity"]
    divided = {"R": 0.0, "D": 0.0}
    if gap > 0:
        divided["D"] = gap / SENATE_DIVIDED_DIVISOR
    elif gap < 0:
        divided["R"] = -gap / SENATE_DIVIDED_DIVISOR

    races, won = [], {"R": 0, "D": 0}
    for state_name, data in STATES.items():
        seats = senate["seats"].get(state_name)
        if not seats:
            continue
        base = {p: issue_score(platform[p], data) for p in "RD"}
        top = {p: score(pres[p], data, state_name) / SENATE_TOP_TICKET_DIVISOR for p in "RD"}
        for number, seat in enumerate(seats, start=1):
            raw, entries = [], []
            for p in "RD":
                total = base[p] + seat[p]["advantage"] + top[p] + divided[p]
                raw.append(total)
                entries.append({"party": p, "name": seat[p]["name"], "advantage": seat[p]["advantage"],
                                "caucus": seat[p]["caucus"],
                                "party_score": round(base[p], 1), "top_ticket": round(top[p], 1),
                                "divided": round(divided[p], 1), "score": round(total, 1)})
            best = max(raw)
            leaders = [i for i, x in enumerate(raw) if best - x < 1e-9]
            is_tie = len(leaders) > 1
            winner = random.choice(leaders)
            shares = vote_shares(raw)
            races.append({"state": state_name, "code": STATE_CODES.get(state_name), "seat": number,
                          "seats_in_state": len(seats), "candidates": entries, "winner": winner,
                          "margin": 0.0 if is_tie else round(abs(shares[0] - shares[1]), 1),
                          "shares": round_to_100(shares), "tie": is_tie})
            won["RD"[winner]] += 1

    final = {p: senate["holdover"][p] + won[p] for p in "RD"}
    total_seats = final["R"] + final["D"]
    needed = total_seats // 2 + 1
    control, tie_break = senate_control(final, candidates, pres_winner)

    return {"races": races, "holdover": dict(senate["holdover"]), "won": won, "final": final,
            "total_seats": total_seats, "needed": needed, "control": control, "tie_break": tie_break,
            "popularity_gap": gap, "divided": {p: round(divided[p], 1) for p in "RD"},
            "top_ticket_divisor": SENATE_TOP_TICKET_DIVISOR, "divided_divisor": SENATE_DIVIDED_DIVISOR}


def build_new_senate(senate, senate_result):
    people = []
    for p in "RD":
        n = senate["holdover"][p]
        listed = [x for x in senate["senators"] if x["party"] == p]
        if len(listed) > n:
            print(f"Note: {len(listed)} {PARTY_PLURAL[p]} are listed as not up for election, but only {n} are. "
                  f"The last {len(listed) - n} listed are ignored.")
        for x in listed[:n]:
            people.append({"name": x["name"], "party": p, "caucus": x["caucus"], "origin": "not up"})
        for _ in range(n - len(listed[:n])):
            people.append({"name": "", "party": p, "caucus": "", "origin": "not up"})
    for r in senate_result["races"]:
        w = r["candidates"][r["winner"]]
        people.append({"name": w["name"], "party": w["party"], "caucus": w.get("caucus", ""), "origin": "won"})
    return people


def caucus_table(senate, roster):
    rows = []
    for cname in [c["name"] for c in senate["caucuses"]] + [""]:
        row = {"name": cname or LOYALISTS, "loyalists": cname == ""}
        for p in "RD":
            members = [m for m in roster if m["caucus"] == cname and m["party"] == p]
            row[p] = {"not_up": sum(1 for m in members if m["origin"] == "not up"),
                      "won": sum(1 for m in members if m["origin"] == "won")}
        rows.append(row)
    return rows


def disagreement(a, b):
    return sum(WEIGHTS[k] * abs(a[k] - b[k]) for k in ISSUES)


def run_caucus_vote(senate, roster, candidates, result):
    order = sorted(range(len(candidates)),
                   key=lambda i: (-result["candidates"][i]["votes"], -result["candidates"][i]["popular_points"], i))
    eligible = order[:2]
    total = len(roster)
    majority = total // 2 + 1

    def describe(members):
        named = [{"name": m["name"], "party": m["party"]} for m in members if m["name"]]
        unnamed = {p: sum(1 for m in members if not m["name"] and m["party"] == p) for p in "RD"}
        return named, unnamed

    groups = []
    for c in senate["caucuses"]:
        members = [m for m in roster if m["caucus"] == c["name"]]
        if not members:
            continue
        dis = [disagreement(c["stances"], candidates[i]) for i in eligible]
        best = min(dis)
        closest = [k for k, d in enumerate(dis) if abs(d - best) < 1e-9]
        pick = random.choice(closest)
        over = best - CAUCUS_MAX_DISAGREEMENT
        turn = 1 if over <= 1e-9 else max(1, math.ceil(over / CAUCUS_MOVE_PER_TURN - 1e-9))
        named, unnamed = describe(members)
        groups.append({"name": c["name"], "loyalists": False, "size": len(members), "named": named,
                       "unnamed": unnamed, "disagreement": [round(d, 2) for d in dis],
                       "candidate": eligible[pick], "turn": turn, "over": round(max(over, 0.0), 2),
                       "tie_pick": len(closest) > 1})
    for p, party in (("R", "Republican"), ("D", "Democrat")):
        members = [m for m in roster if m["caucus"] == "" and m["party"] == p]
        if not members:
            continue
        match = [i for i in eligible if candidates[i]["party"] == party]
        named, unnamed = describe(members)
        groups.append({"name": f"{LOYALISTS} ({PARTY_NAME[p]})", "loyalists": True, "size": len(members),
                       "named": named, "unnamed": unnamed, "disagreement": None,
                       "candidate": match[0] if match else None, "turn": 1 if match else None,
                       "over": 0.0, "tie_pick": False})

    totals = {i: 0 for i in eligible}
    turns, winner, how, stop = [], None, None, 0
    last = max([g["turn"] for g in groups if g["turn"]] or [0])
    for t in range(1, last + 1):
        joined = [g for g in groups if g["turn"] == t]
        for g in joined:
            totals[g["candidate"]] += g["size"]
        turns.append({"turn": t, "totals": [totals[i] for i in eligible],
                      "abstaining": total - sum(totals.values()),
                      "joined": [{"name": g["name"], "size": g["size"], "candidate": g["candidate"]} for g in joined]})
        stop = t
        lead = max(totals.values())
        if lead >= majority:
            winner, how = [i for i in eligible if totals[i] == lead][0], "majority"
            break
    if winner is None:
        lead = max(totals.values())
        leaders = [i for i in eligible if totals[i] == lead]
        winner = random.choice(leaders)
        how = "coin flip" if len(leaders) > 1 else "most votes"
    for g in groups:
        g["counted"] = bool(g["turn"]) and g["turn"] <= (stop or 0)

    w = candidates[winner]
    if how == "majority":
        summary = f"{w['name']} won in turn {stop} with {totals[winner]} of {total} senators (majority: {majority})."
    elif how == "most votes":
        summary = (f"Nobody reached the majority ({majority} of {total}) even after the last caucus voted, so "
                   f"{w['name']} won with the most votes ({totals[winner]}).")
    else:
        summary = (f"Nobody reached the majority ({majority} of {total}) and the top candidates are tied on "
                   f"{totals[winner]} votes, so {w['name']} won a coin flip.")
    return {"candidates": [{"index": i, "name": candidates[i]["name"], "party": candidates[i]["party"],
                            "ev": result["candidates"][i]["votes"]} for i in eligible],
            "total": total, "majority": majority, "limit": CAUCUS_MAX_DISAGREEMENT, "move": CAUCUS_MOVE_PER_TURN,
            "groups": groups, "turns": turns, "winner": winner, "how": how, "stop": stop,
            "final": [totals[i] for i in eligible], "summary": summary}


def run_house(house, candidates, result):
    """A first-pass House contingent vote: each state delegation picks the strongest top-three candidate; if no majority, it abstains."""
    if not house or not house.get("seats"):
        return None
    tops = sorted(range(len(candidates)),
                  key=lambda i: (result["candidates"][i]["votes"], result["candidates"][i]["popular_points"]),
                  reverse=True)[:3]
    support = {i: 0 for i in range(len(candidates))}
    state_pick = []
    for state_name, seats in house["seats"].items():
        if not seats:
            continue
        scores = {i: 0.0 for i in range(len(candidates))}
        for i in tops:
            cand = candidates[i]
            # party-friendly base: the relevant main party platform gets the seat's party signal.
            for seat in seats:
                if seat["party"] == "R" and cand["party"] == "Republican":
                    party_score = issue_score(cand, STATES[state_name])
                elif seat["party"] == "D" and cand["party"] == "Democrat":
                    party_score = issue_score(cand, STATES[state_name])
                else:
                    party_score = -999
                score_total = party_score + seat["advantage"]
                scores[i] += max(score_total, 0)
        total = len(seats)
        best = max(scores.values())
        leaders = [i for i, v in scores.items() if abs(v - best) < 1e-9]
        if len(leaders) == 1 and best > 0:
            winner = leaders[0]
            if best > total / 2:
                support[winner] += 1
                state_pick.append({"state": state_name, "winner": winner, "support": best})
            else:
                state_pick.append({"state": state_name, "winner": None, "support": best})
        else:
            state_pick.append({"state": state_name, "winner": None, "support": best})

    target = 26
    winners = sorted(range(len(candidates)), key=lambda i: support[i], reverse=True)
    winner = winners[0] if support[winners[0]] >= target else None
    final = None if winner is None else candidates[winner]
    summary = f"House support: {support[winner]} states support {final['name']}" if winner is not None else "No candidate reached the 26-state threshold"
    return {"candidates": [{"index": i, "name": candidates[i]["name"], "party": candidates[i]["party"], "states": support[i]} for i in range(len(candidates))],
            "support": support, "states": state_pick, "winner": winner, "target": target, "summary": summary}


def print_house(vote, candidates):
    if not vote:
        return
    print("\n=== HOUSE OF REPRESENTATIVES CONTINGENT VOTE ===")
    for c in vote["candidates"]:
        print(f"{c['name']} ({c['party']}): {c['states']} states support them")
    if vote["winner"] is None:
        print("No candidate reached 26 states; the House remains deadlocked.")
    else:
        print(f"{candidates[vote['winner']]['name']} wins the House vote with {vote['support'][vote['winner']]} state delegations.")


# ---------------------------------------------------------------------------
# Results map
# ---------------------------------------------------------------------------

MAP_PLACEHOLDER = "/*RESULTS_JSON*/null"


def show_map(result, year):
    folder = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(folder, "map_template.html")
    out_path = os.path.join(folder, "election_map.html")
    try:
        with open(template_path, encoding="utf-8") as f:
            template = f.read()
        if MAP_PLACEHOLDER not in template:
            print(f"\nMap not shown: map_template.html has no {MAP_PLACEHOLDER} marker.")
            return
        unmapped = [r["state"] for r in result["states"] if not r["code"]]
        if unmapped:
            print("\nNote: no map code for " + ", ".join(unmapped)
                  + " (add it to STATE_CODES). It is listed in the table but not coloured.")
        data = dict(result, year=str(year))
        payload = json.dumps(data).replace("<", "\\u003c")
        page = template.replace(MAP_PLACEHOLDER, payload)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(page)
        print(f"\nMap saved as {out_path}")
        webbrowser.open(Path(out_path).as_uri())
    except FileNotFoundError:
        print("\nMap not shown: map_template.html was not found in the game folder.")
    except Exception as error:
        print(f"\nMap not shown ({error}).")


def main():
    global STATES, ISSUE_TEXT
    print("ELECTION GAME - simulate an election based on political stances")
    scenarios, issue_texts, senates, houses = load_scenarios()
    while True:
        year = choose_scenario(scenarios)
        STATES = scenarios[year]
        ISSUE_TEXT = issue_texts[year]
        print(f"\n>>> Playing the {year} election ({len(STATES)} states)")
        use_vp = ask_yes_no("\nUse vice presidents? (if yes, every candidate must choose one)")
        use_senate = year in senates and ask_yes_no("\nAlso hold the Senate elections of this year?")
        use_house = year in houses and ask_yes_no("\nAlso hold the House elections of this year?")
        c1 = ask_main_candidate(1, "Republican", use_vp)
        c2 = ask_main_candidate(2, "Democrat", use_vp)
        candidates = [c1, c2]

        if ask_yes_no("\nAdd a third-party candidate?"):
            c3 = ask_minor_candidate("Third Party", use_vp)
            apply_third_party_effect(c1, c2, c3)
            candidates.append(c3)
            if ask_yes_no("\nAdd a fourth candidate?"):
                c4 = ask_minor_candidate("Fourth Party", use_vp)
                apply_third_party_effect(c1, c2, c4)
                candidates.append(c4)

        platforms = None
        if use_senate:
            platforms = [ask_party("Republican", "Republican"), ask_party("Democratic", "Democrat")]

        use_caucus = use_senate and bool(senates[year]["caucuses"])
        result = run_election(candidates, caucus_decides=use_caucus)

        if use_senate:
            votes = [c["votes"] for c in result["candidates"]]
            leaders = [i for i, v in enumerate(votes) if v == max(votes)]
            caucus_decides = use_caucus and result["deadlock"]
            pres_winner = None if caucus_decides else (leaders[0] if len(leaders) == 1 else None)
            senate_result = run_senate(senates[year], candidates, platforms, pres_winner)
            roster = build_new_senate(senates[year], senate_result)
            vote = None
            if caucus_decides:
                vote = run_caucus_vote(senates[year], roster, candidates, result)
                pres_winner = vote["winner"]
                senate_result["control"], senate_result["tie_break"] = senate_control(
                    senate_result["final"], candidates, pres_winner)
                result["verdict"] = f"{ticket_text(candidates[pres_winner])} wins the election in the Senate caucus vote!"
            result["senate"] = senate_result
            if sensates := senates[year]:
                pass
            if senates[year]["caucuses"]:
                senate_result["caucus_table"] = caucus_table(senates[year], roster)
            if vote:
                result["caucus_vote"] = vote

        if use_house:
            house_vote = run_house(houses[year], candidates, result)
            result["house"] = house_vote
            print_house(house_vote, candidates)

        show_map(result, year)

        if not ask_yes_no("\nPlay again?"):
            print("Thanks for playing!")
            break


if __name__ == "__main__":
    main()
    input("\nPress Enter to close...")
