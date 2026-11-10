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
            out[key] = (pick("label", name), low, high)
        else:
            out[key] = (pick("label", name), pick("low", low), pick("high", high))
    return out


def read_senate(raw_year, state_names):
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
    """Optional House election data.
    Data format:
      {
        "seats": {
          "California": [
            {"party":"R","name":"A","caucus":"", "advantage":5},
            {"party":"D","name":"B","caucus":"", "advantage":5}
          ]
        }
      }
    We use the same structure for the editor and JSON.
    """
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
    return {"seats": seats, "caucuses": caucuses} if seats else None


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


# Different house logic: state vote share decides the seat split between the two main parties.
def normalize_two_party_voice(state_result):
    rep = 0.0
    dem = 0.0
    if state_result and "shares" in state_result:
        shares = state_result["shares"]
        for idx, cand in enumerate(state_result.get("candidates", [])):
            if cand.get("party") == "Republican":
                rep += float(cand.get("share", 0.0))
            elif cand.get("party") == "Democrat":
                dem += float(cand.get("share", 0.0))
    if rep + dem <= 0:
        return 50.0, 50.0
    return rep / (rep + dem) * 100.0, dem / (rep + dem) * 100.0


def largest_remainder(total, rep_pct, dem_pct):
    rep = round(total * rep_pct / 100.0)
    dem = total - rep
    # If the rounded totals don't add up due to floating-point error, adjust using the remainder.
    while rep + dem != total:
        if rep + dem < total:
            rep += 1
        else:
            rep -= 1
    return rep, dem


def run_house(house, candidates, result):
    if not house or not house.get("seats"):
        return None

    by_state = {}
    total_rep = 0
    total_dem = 0

    # map result state -> share for each candidate; use the two-party share for the main parties
    for state_name, seats in house["seats"].items():
        if not seats:
            continue
        state_result = next((s for s in result["states"] if s["state"] == state_name), None)
        if state_result is None:
            rep_pct = 50.0
            dem_pct = 50.0
        else:
            rep_pct = 0.0
            dem_pct = 0.0
            for index, cand in enumerate(result["candidates"]):
                name = cand["name"]
                party = cand["party"]
                # share is in percent for each candidate in state_result.sharing, but the result object doesn't currently attach those candidate shares by party.
                # We choose the party's share by checking the candidate's party and the winner margin from the state result.
                if party == "Republican":
                    rep_pct = state_result.get("shares", [50.0, 50.0])[index] if index < len(state_result.get("shares", [50.0, 50.0])) else 50.0
                elif party == "Democrat":
                    dem_pct = state_result.get("shares", [50.0, 50.0])[index] if index < len(state_result.get("shares", [50.0, 50.0])) else 50.0
            if rep_pct + dem_pct <= 0:
                rep_pct = 50.0
                dem_pct = 50.0
            else:
                rep_pct = rep_pct / (rep_pct + dem_pct) * 100.0
                dem_pct = dem_pct / (rep_pct + dem_pct) * 100.0 if rep_pct + dem_pct > 0 else 50.0

        total = len(seats)
        rep_count, dem_count = largest_remainder(total, rep_pct, dem_pct)
        rep_queue = [m for m in seats if m["party"] == "R"]
        dem_queue = [m for m in seats if m["party"] == "D"]

        rep_elected = rep_queue[:rep_count]
        dem_elected = dem_queue[:dem_count]

        state_party = "R" if rep_count > dem_count else "D" if dem_count > rep_count else "T"
        by_state[state_name] = {
            "state": state_name,
            "R": rep_count,
            "D": dem_count,
            "party_winner": state_party,
            "rep_elected": rep_elected,
            "dem_elected": dem_elected,
        }
        total_rep += rep_count
        total_dem += dem_count

    support = {i: 0 for i in range(len(candidates))}
    for state_name, state_data in by_state.items():
        if state_data["party_winner"] == "R":
            for idx, cand in enumerate(candidates):
                if cand["party"] == "Republican":
                    support[idx] += 1
        elif state_data["party_winner"] == "D":
            for idx, cand in enumerate(candidates):
                if cand["party"] == "Democrat":
                    support[idx] += 1
        elif state_data["party_winner"] == "T":
            # a tie state stays as a state with no house delegation winner; it is not counted
            pass

    winner_index = None
    for idx, support_count in sorted(support.items(), key=lambda kv: kv[1], reverse=True):
        if support_count >= 26:
            winner_index = idx
            break

    return {
        "composition": {"R": total_rep, "D": total_dem},
        "states": by_state,
        "support": support,
        "winner": winner_index,
        "target": 26,
        "summary": "House support: %s state delegations for %s" % (support[winner_index], candidates[winner_index]["name"]) if winner_index is not None else "No candidate reached 26 state delegations.",
    }


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
    total_ev = sum(d[4] for d in STATES.values())
    needed = total_ev // 2 + 1
    popular_pct = round_to_100([100.0 * p / sum(popular) for p in popular])
    top = max(votes)
    top_candidates = [c for c, v in zip(candidates, votes) if v == top]
    deadlock = len(top_candidates) > 1 or top < needed
    return {
        "candidates": [{"name": c["name"], "party": c["party"], "ticket": c["name"],
                        "votes": v, "popular_pct": pct, "popular_points": round(pts, 1), "share": round(100.0 * v / total_ev, 1)}
                       for c, v, pct, pts in zip(candidates, votes, popular_pct, popular)],
        "states": state_results,
        "total_ev": total_ev,
        "needed": needed,
        "deadlock": deadlock,
    }


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


def ask_state(prompt):
    lookup = {name.lower(): name for name in STATES}
    lookup.update({k: v for k, v in STATE_ALIASES.items() if v in STATES})
    while True:
        text = " ".join(input(f"{prompt}: ").split()).lower()
        if text in lookup:
            return lookup[text]
        print("  That is not a state in this election. Type a state name, for example Ohio.")


STATE_ALIASES = {"dc": "Washington DC", "d.c.": "Washington DC", "washington d.c.": "Washington DC",
                 "washington, dc": "Washington DC", "ma": "Massachusetts", "pa": "Pennsylvania", "ct": "Connecticut",
                 "nc": "North Carolina", "sc": "South Carolina", "de": "Delaware", "nh": "New Hampshire"}


def state_bonus(c, state_name):
    pts = 0.0
    if c.get("home_state") == state_name:
        pts += HOME_STATE_POINTS
    pts += CAMPAIGN_POINTS * c.get("campaign", []).count(state_name)
    if c.get("vp_state") == state_name:
        pts += VP_STATE_POINTS
    return pts


HOME_STATE_POINTS = 5
CAMPAIGN_STOPS = 3
CAMPAIGN_POINTS = 1
VP_STATE_POINTS = 1

# Used by the map template
def build_house_result(house, result):
    # This is a conservative House model: seat share follows the state R/D vote share exactly and is applied to the House delegation in that state.
    # This matches the rule: the percentage of the vote won equals the percentage of the seats won.
    if not house or not house.get("seats"):
        return None
    house_result = {"composition": {"R": 0, "D": 0}, "states": {}, "winner": None, "target": 26}
    for state_name, seats in house["seats"].items():
        if not seats:
            continue
        state_data = next((s for s in result["states"] if s["state"] == state_name), None)
        if state_data is None:
            rep_pct = 50.0
            dem_pct = 50.0
        else:
            # Use the two-party vote split from the state result.
            shares = state_data.get("shares", [50.0, 50.0])
            rep_share = shares[0] if len(shares) > 0 else 50.0
            dem_share = shares[1] if len(shares) > 1 else 50.0
            if rep_share + dem_share <= 0:
                rep_pct = 50.0
                dem_pct = 50.0
            else:
                rep_pct = rep_share / (rep_share + dem_share) * 100.0
                dem_pct = dem_share / (rep_share + dem_share) * 100.0
        total_seats = len(seats)
        rep_seats = round(total_seats * rep_pct / 100.0)
        if rep_seats + round(total_seats * dem_pct / 100.0) != total_seats:
            rep_seats = total_seats - round(total_seats * dem_pct / 100.0)
        dem_seats = total_seats - rep_seats
        rep_queue = [m for m in seats if m["party"] == "R"]
        dem_queue = [m for m in seats if m["party"] == "D"]
        elected = {"R": rep_queue[:rep_seats], "D": dem_queue[:dem_seats]}
        if rep_seats > dem_seats:
            party_winner = "R"
        elif dem_seats > rep_seats:
            party_winner = "D"
        else:
            party_winner = "T"
        house_result["states"][state_name] = {"R": rep_seats, "D": dem_seats, "winner": party_winner}
        house_result["composition"]["R"] += rep_seats
        house_result["composition"]["D"] += dem_seats

    # House chooses a president from the top three candidates by the number of state delegations behind them.
    house_support = {i: 0 for i in range(len(result["candidates"]))}
    for state_name, state_data in house_result["states"].items():
        if state_data["winner"] == "R":
            for idx, cand in enumerate(result["candidates"]):
                if cand["party"] == "Republican":
                    house_support[idx] += 1
        elif state_data["winner"] == "D":
            for idx, cand in enumerate(result["candidates"]):
                if cand["party"] == "Democrat":
                    house_support[idx] += 1

    winner_index = max(house_support, key=house_support.get) if house_support else None
    if winner_index is not None and house_support[winner_index] >= 26:
        house_result["winner"] = winner_index
        house_result["summary"] = f"{result['candidates'][winner_index]['name']} wins the House vote with {house_support[winner_index]} state delegations."
    else:
        house_result["winner"] = None
        house_result["summary"] = "No candidate reached 26 state delegations."
    house_result["support"] = house_support
    return house_result


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
            candidates.append(c3)
            if ask_yes_no("\nAdd a fourth candidate?"):
                c4 = ask_minor_candidate("Fourth Party", use_vp)
                candidates.append(c4)

        result = run_election(candidates)
        if use_house:
            house_result = build_house_result(houses[year], result)
            result["house"] = house_result
            if house_result:
                print("\n=== HOUSE OF REPRESENTATIVES ===")
                print(f"Republicans: {house_result['composition']['R']} seats | Democrats: {house_result['composition']['D']} seats")
                print(house_result["summary"])

        show_map(result, year)
        if not ask_yes_no("\nPlay again?"):
            print("Thanks for playing!")
            break


if __name__ == "__main__":
    main()
    input("\nPress Enter to close...")
