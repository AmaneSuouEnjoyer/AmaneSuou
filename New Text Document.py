# Define states and their attributes
# States with their positions on issues: trade, immigration, partisanship, and abortion
states = {
    "Texas": {"immigration": 8, "trade": 2, "partisanship": 3, "abortion": 4, "electoral_college": 40, "foreign_policy": 8},
    "California": {"immigration": 3, "trade": 4, "partisanship": 9, "abortion": 8, "electoral_college": 54, "foreign_policy": 2},
    "New York": {"immigration": 3, "trade": 5, "partisanship": 9, "abortion": 8, "electoral_college": 28, "foreign_policy": 3},
    "New Jersey": {"immigration": 4, "trade": 6, "partisanship": 7, "abortion": 7, "electoral_college": 14, "foreign_policy": 3},
    "Illinois": {"immigration": 4, "trade": 7, "partisanship": 8, "abortion": 8, "electoral_college": 19, "foreign_policy": 2},
    "Pennsylvania": {"immigration": 6, "trade": 8, "partisanship": 6, "abortion": 6, "electoral_college": 19, "foreign_policy": 4},
    "Ohio": {"immigration": 8, "trade": 8, "partisanship": 5, "abortion": 4, "electoral_college": 17, "foreign_policy": 5},
    "Wisconsin": {"immigration": 6, "trade": 8, "partisanship": 7, "abortion": 7, "electoral_college": 10, "foreign_policy": 4},
    "Michigan": {"immigration": 6, "trade": 8, "partisanship": 7, "abortion": 7, "electoral_college": 15, "foreign_policy": 3},
    "Minnesota": {"immigration": 4, "trade": 8, "partisanship": 8, "abortion": 7, "electoral_college": 10, "foreign_policy": 2},
    "Missouri": {"immigration": 8, "trade": 7, "partisanship": 3, "abortion": 4, "electoral_college": 10, "foreign_policy": 8},
    "Kentucky": {"immigration": 9, "trade": 7, "partisanship": 2, "abortion": 3, "electoral_college": 8, "foreign_policy": 7},
    "West Virginia": {"immigration": 9, "trade": 9, "partisanship": 3, "abortion": 2, "electoral_college": 4, "foreign_policy": 6},
    "Oklahoma": {"immigration": 9, "trade": 3, "partisanship": 2, "abortion": 2, "electoral_college": 7, "foreign_policy": 8},
    "Tennessee": {"immigration": 9, "trade": 3, "partisanship": 3, "abortion": 2, "electoral_college": 11, "foreign_policy": 8},
    "Indiana": {"immigration": 8, "trade": 5, "partisanship": 3, "abortion": 4, "electoral_college": 11, "foreign_policy": 7},
    "Arkansas": {"immigration": 8, "trade": 3, "partisanship": 3, "abortion": 2, "electoral_college": 6, "foreign_policy": 7},
    "Mississippi": {"immigration": 9, "trade": 3, "partisanship": 2, "abortion": 2, "electoral_college": 6, "foreign_policy": 7},
    "Alabama": {"immigration": 9, "trade": 4, "partisanship": 2, "abortion": 2, "electoral_college": 9, "foreign_policy": 7},
    "Louisiana": {"immigration": 8, "trade": 3, "partisanship": 3, "abortion": 2, "electoral_college": 8, "foreign_policy": 7},
    "South Carolina": {"immigration": 8, "trade": 3, "partisanship": 3, "abortion": 3, "electoral_college": 9, "foreign_policy": 7},
    "Georgia": {"immigration": 6, "trade": 3, "partisanship": 4, "abortion": 4, "electoral_college": 16, "foreign_policy": 6},
    "Florida": {"immigration": 6, "trade": 4, "partisanship": 5, "abortion": 4, "electoral_college": 30, "foreign_policy": 6},
    "North Carolina": {"immigration": 7, "trade": 3, "partisanship": 4, "abortion": 4, "electoral_college": 16, "foreign_policy": 7},
    "Virginia": {"immigration": 4, "trade": 3, "partisanship": 6, "abortion": 7, "electoral_college": 13, "foreign_policy": 6},
    "South Dakota": {"immigration": 7, "trade": 2, "partisanship": 2, "abortion": 5, "electoral_college": 3, "foreign_policy": 6},
    "North Dakota": {"immigration": 7, "trade": 2, "partisanship": 2, "abortion": 5, "electoral_college": 3, "foreign_policy": 6},
    "Kansas": {"immigration": 7, "trade": 2, "partisanship": 2, "abortion": 5, "electoral_college": 6, "foreign_policy": 6},
    "Nebraska": {"immigration": 7, "trade": 2, "partisanship": 2, "abortion": 5, "electoral_college": 5, "foreign_policy": 6},
    "Wyoming": {"immigration": 7, "trade": 3, "partisanship": 1, "abortion": 2, "electoral_college": 3, "foreign_policy": 7},
    "Idaho": {"immigration": 6, "trade": 4, "partisanship": 1, "abortion": 2, "electoral_college": 4, "foreign_policy": 7},
    "Montana": {"immigration": 6, "trade": 4, "partisanship": 2, "abortion": 3, "electoral_college": 4, "foreign_policy": 6},
    "Utah": {"immigration": 5, "trade": 2, "partisanship": 1, "abortion": 3, "electoral_college": 6, "foreign_policy": 7},
    "Arizona": {"immigration": 6, "trade": 2, "partisanship": 3, "abortion": 5, "electoral_college": 11, "foreign_policy": 6},
    "Colorado": {"immigration": 3, "trade": 2, "partisanship": 7, "abortion": 8, "electoral_college": 10, "foreign_policy": 3},
    "New Mexico": {"immigration": 3, "trade": 3, "partisanship": 7, "abortion": 7, "electoral_college": 5, "foreign_policy": 3},
    "Nevada": {"immigration": 6, "trade": 4, "partisanship": 6, "abortion": 8, "electoral_college": 6, "foreign_policy": 4},
    "Washington": {"immigration": 3, "trade": 3, "partisanship": 8, "abortion": 9, "electoral_college": 12, "foreign_policy": 2},
    "Alaska": {"immigration": 6, "trade": 4, "partisanship": 2, "abortion": 4, "electoral_college": 3, "foreign_policy": 5},
    "Hawaii": {"immigration": 2, "trade": 3, "partisanship": 8, "abortion": 8, "electoral_college": 4, "foreign_policy": 2},
    "Oregon": {"immigration": 3, "trade": 3, "partisanship": 7, "abortion": 9, "electoral_college": 8, "foreign_policy": 2},
    "Washington DC": {"immigration": 1, "trade": 2, "partisanship": 10, "abortion": 10, "electoral_college": 3, "foreign_policy": 1},
    "Massachusetts": {"trade": 3, "immigration": 1, "partisanship": 10, "electoral_college": 11, "abortion": 9, "foreign_policy": 1},
    "Rhode Island": {"trade": 2, "immigration": 2, "partisanship": 9, "electoral_college": 4, "abortion": 9, "foreign_policy": 2},
    "Connecticut": {"trade": 2, "immigration": 2, "partisanship": 9, "electoral_college": 7, "abortion": 9, "foreign_policy": 2},
    "Maryland": {"trade": 3, "immigration": 2, "partisanship": 8, "electoral_college": 10, "abortion": 9, "foreign_policy": 2},
    "Delaware": {"trade": 3, "immigration": 2, "partisanship": 9, "electoral_college": 3, "abortion": 9, "foreign_policy": 2},
    "Vermont": {"trade": 4, "immigration": 2, "partisanship": 8, "electoral_college": 3, 'abortion': 10, "foreign_policy": 1},
    "New Hampshire": {"trade": 2, "immigration": 4, "partisanship": 5, "electoral_college": 4, "abortion": 7, "foreign_policy": 3},
    "Maine": {"trade": 2, "immigration": 3, "partisanship": 7, "electoral_college": 4, 'abortion': 8, "foreign_policy": 3},
    "Iowa": {"trade": 8, "immigration": 6, "partisanship": 4, "abortion": 6, "electoral_college": 6, "foreign_policy": 4},
}

import random


def get_valid_input(prompt, min_value, max_value):
    while True:
        try:
            value = int(input(prompt))
            if value < min_value or value > max_value:
                print(f"Please enter a number between {min_value} and {max_value}.")
            else:
                return value
        except ValueError:
            print("Invalid input. Please enter a valid number.")


def run_game():
    print("Welcome to the Election Game!")

    # Candidate 1 (Republican)
    candidate1_name = input("Enter the name of Candidate 1 (Republican): ")
    print("\nNow, please select your positions on the following issues for Candidate 1.")

    candidate1_trade = get_valid_input("What is your stance on trade? (1-10) 1 is free market, 10 is protectionist: ",
                                       1, 10)
    candidate1_immigration = get_valid_input(
        "What is your stance on immigration? (1-10) 1 is open borders, 10 is strict immigration control: ", 1, 10)
    candidate1_partisanship = get_valid_input(
        "What is your partisanship stance? (1-5) 1 is extreme Republican, 5 is moderate: ", 1, 5)
    candidate1_abortion = get_valid_input("What is your stance on abortion? (1-10) 1 is pro-life, 10 is pro-choice: ",
                                          1, 10)
    candidate1_foreign_policy = get_valid_input(
        "What is your stance on foreign policy? (1-10) 1 is the most dovish, 10 is the most hawkish: ", 1, 10)

    # Candidate 2 (Democrat)
    candidate2_name = input("Enter the name of Candidate 2 (Democrat): ")
    print("\nNow, please select your positions on the following issues for Candidate 2.")

    candidate2_trade = get_valid_input("What is your stance on trade? (1-10) 1 is free market, 10 is protectionist: ",
                                       1, 10)
    candidate2_immigration = get_valid_input(
        "What is your stance on immigration? (1-10) 1 is open borders, 10 is strict immigration control: ", 1, 10)
    candidate2_partisanship = get_valid_input(
        "What is your partisanship stance? (6-10) 6 is moderate Democrat, 10 is extreme Democrat: ", 6, 10)
    candidate2_abortion = get_valid_input("What is your stance on abortion? (1-10) 1 is pro-life, 10 is pro-choice: ",
                                          1, 10)
    candidate2_foreign_policy = get_valid_input(
        "What is your stance on foreign policy? (1-10) 1 is the most dovish, 10 is the most hawkish: ", 1, 10)

    def get_home_state(candidate_name):
        while True:
            home_state = input(f"Enter the home state of {candidate_name}: ").strip()
            if home_state in states:
                return home_state
            print("Invalid state name. Please enter a valid state name from the list.")

    candidate1_home_state = get_home_state(candidate1_name)
    candidate2_home_state = get_home_state(candidate2_name)

    def calculate_closer_position(state, candidate1, candidate2):
        score1 = 0
        score2 = 0
        issues = ["trade", "immigration", "partisanship", "abortion", "foreign_policy"]
        for issue in issues:
            score1 += abs(state[issue] - candidate1[issue])
            score2 += abs(state[issue] - candidate2[issue])
        return score1, score2

    candidate1_votes = 0
    candidate2_votes = 0
    tied_states = []  # Will store the names of states with ties
    state_margins = []  # Stores the margin of victory and the winner for each state

    for state_name, state_data in states.items():
        score1, score2 = calculate_closer_position(state_data,
                                                   {"trade": candidate1_trade, "immigration": candidate1_immigration,
                                                    "partisanship": candidate1_partisanship,
                                                    "abortion": candidate1_abortion,
                                                    "foreign_policy": candidate1_foreign_policy},
                                                   {"trade": candidate2_trade, "immigration": candidate2_immigration,
                                                    "partisanship": candidate2_partisanship,
                                                    "abortion": candidate2_abortion,
                                                    "foreign_policy": candidate2_foreign_policy})
        if state_name == candidate1_home_state:
            score1 -= 4
        if state_name == candidate2_home_state:
            score2 -= 4

        margin = abs(score1 - score2)  # Calculate margin

        # Determine winner based on scores
        if score1 < score2:
            state_winner = candidate1_name
            candidate1_votes += state_data["electoral_college"]
        elif score1 > score2:
            state_winner = candidate2_name
            candidate2_votes += state_data["electoral_college"]
        else:  # If it's a tie, apply random winner for electoral votes
            state_winner = random.choice([candidate1_name, candidate2_name])
            tied_states.append({
                "state": state_name,
                "winner": state_winner,
                "electoral_votes": state_data["electoral_college"]
            })
            print(f"{state_name} is tied, no electoral votes awarded, winner chosen: {state_winner}.")

        # Append to the state_margins list based on the winner and margin
        state_margins.append({
            "state": state_name,
            "margin": margin,
            "winner": state_winner
        })

        print(f"{state_name} is won by {state_winner} with {state_data['electoral_college']} electoral votes!")

    # Add tied state results to the final vote tally for the closest states
    for tied_state in tied_states:
        winner = tied_state["winner"]  # Use the same winner as for the electoral tie resolution
        if winner == candidate1_name:
            candidate1_votes += tied_state["electoral_votes"]
            print(
                f"{candidate1_name} wins {tied_state['state']} with {tied_state['electoral_votes']} electoral votes (randomly assigned).")
        else:
            candidate2_votes += tied_state["electoral_votes"]
            print(
                f"{candidate2_name} wins {tied_state['state']} with {tied_state['electoral_votes']} electoral votes (randomly assigned).")

    print("\nElection Results:")
    print(f"{candidate1_name} has {candidate1_votes} electoral votes.")
    print(f"{candidate2_name} has {candidate2_votes} electoral votes.")

    if candidate1_votes > candidate2_votes:
        print(f"{candidate1_name} wins the election!")
    elif candidate2_votes > candidate1_votes:
        print(f"{candidate2_name} wins the election!")
    else:
        print("The election is a tie!")

    # Sort the state_margins by margin
    state_margins.sort(key=lambda x: x["margin"])

    # Get the 3 closest states
    closest_states = state_margins[:3]

    print("\nThe 3 Closest States:")
    for state in closest_states:
        print(f"State: {state['state']} | Margin: {state['margin']} | Winner: {state['winner']}")


while True:
    run_game()
    input("\nPress any key to restart the game...")