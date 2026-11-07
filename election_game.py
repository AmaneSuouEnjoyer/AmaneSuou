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

# How much each factor matters. Partisanship is weighted heavily because
# party loyalty is the biggest driver of how a state votes.
# Change these numbers to tune the game.
WEIGHTS = {
    "immigration": 1.0,
    "trade": 1.0,
    "partisanship": 3.0,
    "abortion": 1.0,
    "foreign": 1.0,
}


def ask_number(prompt, low, high):
    """Keep asking until the player types a whole number between low and high."""
    while True:
        text = input(f"{prompt} [{low}-{high}]: ").strip()
        if text.isdigit() and low <= int(text) <= high:
            return int(text)
        print(f"  Please enter a whole number from {low} to {high}.")


def ask_candidate(number, party):
    print(f"\n=== Candidate {number} ({party}) ===")
    name = input("Name: ").strip() or f"Candidate {number}"
    if party == "Republican":
        p_prompt, p_low, p_high = "Partisanship (1 = extreme Republican, 5 = moderate)", 1, 5
    else:
        p_prompt, p_low, p_high = "Partisanship (6 = moderate, 10 = extreme Democrat)", 6, 10
    return {
        "name": name,
        "party": party,
        "trade": ask_number("Trade (1 = free market, 10 = protectionist)", 1, 10),
        "immigration": ask_number("Immigration (1 = open borders, 10 = strict control)", 1, 10),
        "partisanship": ask_number(p_prompt, p_low, p_high),
        "abortion": ask_number("Abortion (1 = pro-life, 10 = pro-choice)", 1, 10),
        "foreign": ask_number("Foreign policy (1 = dovish, 10 = hawkish)", 1, 10),
    }


def score(candidate, state):
    """Higher score = the state likes this candidate more.
    Each factor gives 0-9 points depending on how close the candidate is."""
    imm, trade, part, abort, _ev, foreign = state
    total = 0.0
    total += WEIGHTS["immigration"] * (9 - abs(imm - candidate["immigration"]))
    total += WEIGHTS["trade"] * (9 - abs(trade - candidate["trade"]))
    total += WEIGHTS["partisanship"] * (9 - abs(part - candidate["partisanship"]))
    total += WEIGHTS["abortion"] * (9 - abs(abort - candidate["abortion"]))
    total += WEIGHTS["foreign"] * (9 - abs(foreign - candidate["foreign"]))
    return total


def run_election(c1, c2):
    votes = {c1["name"]: 0, c2["name"]: 0}
    margins = []

    print("\n=== ELECTION RESULTS BY STATE ===")
    for state_name, data in STATES.items():
        ev = data[4]
        s1, s2 = score(c1, data), score(c2, data)
        margin = abs(s1 - s2)

        if s1 > s2:
            winner = c1
            note = ""
        elif s2 > s1:
            winner = c2
            note = ""
        else:
            winner = random.choice([c1, c2])
            note = " (tie, decided randomly)"

        votes[winner["name"]] += ev
        tag = "[R]" if winner["party"] == "Republican" else "[D]"
        print(f"{tag} {state_name:<16} {winner['name']} wins ({ev} EV){note}")
        margins.append((margin, state_name, winner["name"]))

    margins.sort()
    print("\n=== THE 3 CLOSEST STATES ===")
    for margin, state_name, winner_name in margins[:3]:
        print(f"{state_name}: margin {margin:.1f}, winner {winner_name}")

    print("\n=== FINAL RESULTS ===")
    print(f"{c1['name']} (R): {votes[c1['name']]} electoral votes")
    print(f"{c2['name']} (D): {votes[c2['name']]} electoral votes")

    if votes[c1["name"]] > votes[c2["name"]]:
        print(f"\n*** {c1['name']} wins the election! ***")
    elif votes[c2["name"]] > votes[c1["name"]]:
        print(f"\n*** {c2['name']} wins the election! ***")
    else:
        print("\nIt's a tie! No clear winner.")


def main():
    print("ELECTION GAME - simulate an election based on political stances")
    while True:
        c1 = ask_candidate(1, "Republican")
        c2 = ask_candidate(2, "Democrat")
        run_election(c1, c2)
        again = input("\nPlay again? (y/n): ").strip().lower()
        if again != "y":
            print("Thanks for playing!")
            break


if __name__ == "__main__":
    main()
