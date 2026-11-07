import random

# State data: (immigration, trade, partisanship, abortion, electoral_votes, foreign_policy)
# immigration:  1 = open borders,  10 = strict control
# trade:        1 = free market,   10 = protectionist
# partisanship: 1 = very Republican, 10 = very Democratic
# abortion:     1 = pro-life,      10 = pro-choice
# foreign:      1 = dovish,        10 = hawkish
STATES = {
    "Texas": (8, 2, 3, 4, 40, 8),
    "California": (3, 4, 9, 8, 54, 2),
    "New York": (3, 5, 9, 8, 28, 3),
    "New Jersey": (4, 6, 7, 7, 14, 3),
    "Illinois": (4, 7, 8, 8, 19, 2),
    "Pennsylvania": (6, 8, 6, 6, 19, 4),
    "Ohio": (8, 8, 5, 4, 17, 5),
    "Wisconsin": (6, 8, 7, 7, 10, 4),
    "Michigan": (6, 8, 7, 7, 15, 3),
    "Minnesota": (4, 8, 8, 7, 10, 2),
    "Missouri": (8, 7, 3, 4, 10, 8),
    "Kentucky": (9, 7, 2, 3, 8, 7),
    "West Virginia": (9, 9, 3, 2, 4, 6),
    "Oklahoma": (9, 3, 2, 2, 7, 8),
    "Tennessee": (9, 3, 3, 2, 11, 8),
    "Indiana": (8, 5, 3, 4, 11, 7),
    "Arkansas": (8, 3, 3, 2, 6, 7),
    "Mississippi": (9, 3, 2, 2, 6, 7),
    "Alabama": (9, 4, 2, 2, 9, 7),
    "Louisiana": (8, 3, 3, 2, 8, 7),
    "South Carolina": (8, 3, 3, 3, 9, 7),
    "Georgia": (6, 3, 4, 4, 16, 6),
    "Florida": (6, 4, 5, 4, 30, 6),
    "North Carolina": (7, 3, 4, 4, 16, 7),
    "Virginia": (4, 3, 6, 7, 13, 6),
    "South Dakota": (7, 2, 2, 5, 3, 6),
    "North Dakota": (7, 2, 2, 5, 3, 6),
    "Kansas": (6, 2, 2, 5, 6, 6),
    "Nebraska": (6, 2, 2, 5, 5, 6),
    "Wyoming": (7, 3, 1, 2, 3, 7),
    "Idaho": (7, 3, 1, 2, 4, 7),
    "Montana": (6, 4, 2, 3, 4, 6),
    "Utah": (5, 2, 1, 3, 6, 8),
    "Arizona": (6, 2, 3, 5, 11, 6),
    "Colorado": (3, 2, 7, 8, 10, 3),
    "New Mexico": (3, 3, 7, 7, 5, 3),
    "Nevada": (6, 4, 6, 8, 6, 4),
    "Washington": (3, 3, 8, 9, 12, 2),
    "Alaska": (6, 4, 2, 4, 3, 5),
    "Hawaii": (2, 3, 8, 8, 4, 2),
    "Oregon": (3, 3, 7, 9, 8, 2),
    "Washington DC": (1, 2, 10, 10, 3, 1),
    "Massachusetts": (1, 3, 10, 9, 11, 1),
    "Rhode Island": (2, 2, 9, 9, 4, 2),
    "Connecticut": (2, 2, 9, 9, 7, 2),
    "Maryland": (2, 3, 8, 9, 10, 2),
    "Delaware": (2, 3, 9, 9, 3, 2),
    "Vermont": (2, 4, 8, 10, 3, 1),
    "New Hampshire": (4, 2, 5, 7, 4, 3),
    "Maine": (3, 2, 7, 8, 4, 3),
    "Iowa": (6, 8, 4, 6, 6, 4),
}

# ---------------------------------------------------------------------------
# TUNING SECTION - change these numbers to rebalance the game
# ---------------------------------------------------------------------------

# How much each issue matters (1.0 = every issue counts the same).
WEIGHTS = {
    "immigration": 1.0,
    "trade": 1.0,
    "partisanship": 1.0,
    "abortion": 1.0,
    "foreign": 1.0,
}

# Points a candidate gets in EVERY state per popularity step (popularity 3 = 3 points).
POPULARITY_POINTS = 1.0

# Third-party "spoiler" damage. If the third-party candidate's ideology is
# close to a main candidate's, that main candidate loses points in EVERY state.
# Ideology distance = sum of the differences on the 5 issues (max 45).
# Each entry is (max distance, penalty). The closer, the bigger the penalty.
# Anything farther than the last tier causes no damage.
SPOILER_TIERS = [
    (5, 8),     # almost identical ideology
    (10, 6),
    (20, 3),
    (30, 1),
]

ISSUES = ["trade", "immigration", "partisanship", "abortion", "foreign"]

TAGS = {"Republican": "[R]", "Democrat": "[D]", "Third Party": "[3]"}


# ---------------------------------------------------------------------------
# Input helpers
# ---------------------------------------------------------------------------

def ask_number(prompt, low, high):
    """Keep asking until the player types a whole number between low and high."""
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


def ask_stances(party, partisan_low, partisan_high, partisan_text):
    """Ask the questions every candidate gets. Returns a stats dictionary."""
    return {
        "trade": ask_number("Trade (1 = free market, 10 = protectionist)", 1, 10),
        "immigration": ask_number("Immigration (1 = open borders, 10 = strict control)", 1, 10),
        "partisanship": ask_number(partisan_text, partisan_low, partisan_high),
        "abortion": ask_number("Abortion (1 = pro-life, 10 = pro-choice)", 1, 10),
        "foreign": ask_number("Foreign policy (1 = dovish, 10 = hawkish)", 1, 10),
        "popularity": ask_number("Personal popularity (1 = unpopular, 5 = very popular)", 1, 5),
    }


def ask_main_candidate(number, party):
    print(f"\n=== Candidate {number} ({party}) ===")
    name = input("Name: ").strip() or f"Candidate {number}"
    if party == "Republican":
        text, low, high = "Partisanship (1 = extreme Republican, 5 = moderate)", 1, 5
    else:
        text, low, high = "Partisanship (6 = moderate, 10 = extreme Democrat)", 6, 10
    candidate = ask_stances(party, low, high, text)
    candidate.update({"name": name, "party": party, "multiplier": 1.0, "penalty": 0.0})
    return candidate


def ask_third_party():
    print("\n=== Third-Party Candidate ===")
    name = input("Name: ").strip() or "Third Party"
    strength = ask_number("Strength (1 = very weak, 5 = as strong as the main candidates)", 1, 5)
    text = "Partisanship (1 = very Republican, 9 = very Democratic)"
    candidate = ask_stances("Third Party", 1, 9, text)
    candidate.update({
        "name": name,
        "party": "Third Party",
        "strength": strength,
        "multiplier": strength / 5,   # 5 -> 1.0, 1 -> 0.2
        "penalty": 0.0,
    })
    return candidate


# ---------------------------------------------------------------------------
# Third-party spoiler effect
# ---------------------------------------------------------------------------

def ideology_distance(a, b):
    """Total issue difference between two candidates (popularity does not count)."""
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

    print("\n=== THIRD-PARTY ANALYSIS ===")
    print(f"Ideology distance to {c1['name']} (R): {d1}")
    print(f"Ideology distance to {c2['name']} (D): {d2}")

    if d1 < d2:
        victims = [(c1, d1, 1.0)]
    elif d2 < d1:
        victims = [(c2, d2, 1.0)]
    else:
        # Exactly equally close: the damage is split between both.
        victims = [(c1, d1, 0.5), (c2, d2, 0.5)]

    for victim, dist, share in victims:
        base = spoiler_penalty(dist)
        victim["penalty"] = base * factor * share
        print(f"{c3['name']} is closer to {victim['name']}.")
        print(f"  Base penalty: {base} points per state, "
              f"strength factor: {factor:.1f}, "
              f"final penalty: -{victim['penalty']:.1f} points per state for {victim['name']}.")
    if all(spoiler_penalty(d) == 0 for _, d, _ in victims):
        print("The third party is too different from both to hurt anyone.")


# ---------------------------------------------------------------------------
# Scoring and election
# ---------------------------------------------------------------------------

def score(candidate, state):
    """Higher score = the state likes this candidate more."""
    imm, trade, part, abort, _ev, foreign = state
    total = 0.0
    total += WEIGHTS["immigration"] * (9 - abs(imm - candidate["immigration"]))
    total += WEIGHTS["trade"] * (9 - abs(trade - candidate["trade"]))
    total += WEIGHTS["partisanship"] * (9 - abs(part - candidate["partisanship"]))
    total += WEIGHTS["abortion"] * (9 - abs(abort - candidate["abortion"]))
    total += WEIGHTS["foreign"] * (9 - abs(foreign - candidate["foreign"]))
    total += POPULARITY_POINTS * candidate["popularity"]
    # Third-party strength scales the whole score; spoiler damage is subtracted.
    return total * candidate["multiplier"] - candidate["penalty"]


def run_election(candidates):
    votes = [0] * len(candidates)
    margins = []

    print("\n=== ELECTION RESULTS BY STATE ===")
    for state_name, data in STATES.items():
        ev = data[4]
        scores = [score(c, data) for c in candidates]
        best = max(scores)
        leaders = [i for i, s in enumerate(scores) if s == best]
        note = ""
        if len(leaders) > 1:
            note = " (tie, decided randomly)"
        winner = random.choice(leaders)

        ordered = sorted(scores, reverse=True)
        margin = ordered[0] - ordered[1]

        votes[winner] += ev
        c = candidates[winner]
        print(f"{TAGS[c['party']]} {state_name:<16} {c['name']} wins ({ev} EV){note}")
        margins.append((margin, state_name, c["name"]))

    margins.sort()
    print("\n=== THE 3 CLOSEST STATES ===")
    for margin, state_name, winner_name in margins[:3]:
        print(f"{state_name}: margin {margin:.1f}, winner {winner_name}")

    total_ev = sum(d[4] for d in STATES.values())
    needed = total_ev // 2 + 1

    print("\n=== FINAL RESULTS ===")
    for c, v in zip(candidates, votes):
        print(f"{TAGS[c['party']]} {c['name']}: {v} electoral votes")
    print(f"({needed} needed to win)")

    top = max(votes)
    top_candidates = [c for c, v in zip(candidates, votes) if v == top]

    if len(top_candidates) > 1:
        print("\nIt's a tie! No clear winner.")
    elif top >= needed:
        print(f"\n*** {top_candidates[0]['name']} wins the election! ***")
    else:
        print(f"\nNo candidate reached {needed} electoral votes.")
        print("In real life the House of Representatives would decide.")
        print(f"In this game, {top_candidates[0]['name']} (most electoral votes) wins the House vote.")


def main():
    print("ELECTION GAME - simulate an election based on political stances")
    while True:
        c1 = ask_main_candidate(1, "Republican")
        c2 = ask_main_candidate(2, "Democrat")
        candidates = [c1, c2]

        if ask_yes_no("\nAdd a third-party candidate?"):
            c3 = ask_third_party()
            apply_third_party_effect(c1, c2, c3)
            candidates.append(c3)

        run_election(candidates)

        if not ask_yes_no("\nPlay again?"):
            print("Thanks for playing!")
            break


if __name__ == "__main__":
    main()
    input("\nPress Enter to close...")
