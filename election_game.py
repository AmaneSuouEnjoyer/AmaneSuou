import streamlit as st
import random

# Define states and their attributes
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
    "Kansas": {"immigration": 6, "trade": 2, "partisanship": 2, "abortion": 5, "electoral_college": 6, "foreign_policy": 6},
    "Nebraska": {"immigration": 6, "trade": 2, "partisanship": 2, "abortion": 5, "electoral_college": 5, "foreign_policy": 6},
    "Wyoming": {"immigration": 7, "trade": 3, "partisanship": 1, "abortion": 2, "electoral_college": 3, "foreign_policy": 7},
    "Idaho": {"immigration": 7, "trade": 3, "partisanship": 1, "abortion": 2, "electoral_college": 4, "foreign_policy": 7},
    "Montana": {"immigration": 6, "trade": 4, "partisanship": 2, "abortion": 3, "electoral_college": 4, "foreign_policy": 6},
    "Utah": {"immigration": 5, "trade": 2, "partisanship": 1, "abortion": 3, "electoral_college": 6, "foreign_policy": 8},
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

# Function for validated user input
def get_valid_input(prompt, min_value, max_value, key):
    return st.slider(prompt, min_value, max_value, key=key)

# Main game function
def run_game():
    st.title("Election Game")
    st.markdown("Simulate an election based on your political stances!")

    st.header("Candidate 1 (Republican)")
    candidate1_name = st.text_input("Enter the name of Candidate 1 (Republican):", key="cand1_name")

    candidate1_trade = get_valid_input("Stance on trade? (1: free market, 10: protectionist)", 1, 10, "cand1_trade")
    candidate1_immigration = get_valid_input("Stance on immigration? (1: open borders, 10: strict control)", 1, 10, "cand1_immigration")
    candidate1_partisanship = get_valid_input("Partisanship? (1: extreme Republican, 5: moderate)", 1, 5, "cand1_partisanship")
    candidate1_abortion = get_valid_input("Stance on abortion? (1: pro-life, 10: pro-choice)", 1, 10, "cand1_abortion")
    candidate1_foreign_policy = get_valid_input("Foreign policy? (1: dovish, 10: hawkish)", 1, 10, "cand1_foreign")

    st.header("Candidate 2 (Democrat)")
    candidate2_name = st.text_input("Enter the name of Candidate 2 (Democrat):", key="cand2_name")

    candidate2_trade = get_valid_input("Stance on trade? (1: free market, 10: protectionist)", 1, 10, "cand2_trade")
    candidate2_immigration = get_valid_input("Stance on immigration? (1: open borders, 10: strict control)", 1, 10, "cand2_immigration")
    candidate2_partisanship = get_valid_input("Partisanship? (10: extreme Democrat, 6: moderate)", 6, 10, "cand2_partisanship")
    candidate2_abortion = get_valid_input("Stance on abortion? (1: pro-life, 10: pro-choice)", 1, 10, "cand2_abortion")
    candidate2_foreign_policy = get_valid_input("Foreign policy? (1: dovish, 10: hawkish)", 1, 10, "cand2_foreign")

    if st.button("Run Simulation"):
        candidate1_votes = 0
        candidate2_votes = 0
        state_margins = []

        st.subheader("Election Results by State")
        for state, attributes in states.items():
            score1 = 0
            score2 = 0

            score1 += 10 - abs(attributes["trade"] - candidate1_trade)
            score1 += 10 - abs(attributes["immigration"] - candidate1_immigration)
            score1 += 5 - abs(attributes["partisanship"] - candidate1_partisanship)
            score1 += 10 - abs(attributes["abortion"] - candidate1_abortion)
            score1 += 10 - abs(attributes["foreign_policy"] - candidate1_foreign_policy)

            score2 += 10 - abs(attributes["trade"] - candidate2_trade)
            score2 += 10 - abs(attributes["immigration"] - candidate2_immigration)
            score2 += 5 - abs(attributes["partisanship"] - candidate2_partisanship)
            score2 += 10 - abs(attributes["abortion"] - candidate2_abortion)
            score2 += 10 - abs(attributes["foreign_policy"] - candidate2_foreign_policy)

            margin = abs(score1 - score2)
            if score1 > score2:
                candidate1_votes += attributes["electoral_college"]
                st.write(f"✅ {state}: {candidate1_name} wins ({attributes['electoral_college']} votes)")
                state_margins.append({"state": state, "margin": margin, "winner": candidate1_name})
            elif score2 > score1:
                candidate2_votes += attributes["electoral_college"]
                st.write(f"🔵 {state}: {candidate2_name} wins ({attributes['electoral_college']} votes)")
                state_margins.append({"state": state, "margin": margin, "winner": candidate2_name})
            else:
                winner = random.choice([1, 2])
                if winner == 1:
                    candidate1_votes += attributes["electoral_college"]
                    st.write(f"🤝 {state}: Tie, random winner is {candidate1_name} ({attributes['electoral_college']} votes)")
                    state_margins.append({"state": state, "margin": margin, "winner": candidate1_name})
                else:
                    candidate2_votes += attributes["electoral_college"]
                    st.write(f"🤝 {state}: Tie, random winner is {candidate2_name} ({attributes['electoral_college']} votes)")
                    state_margins.append({"state": state, "margin": margin, "winner": candidate2_name})

        # Sort the state_margins by margin
        state_margins.sort(key=lambda x: x["margin"])

        # Get the 3 closest states
        closest_states = state_margins[:3]

        st.subheader("The 3 Closest States")
        for state in closest_states:
            st.write(f"State: {state['state']} | Margin: {state['margin']} | Winner: {state['winner']}")

        st.header("Final Results")
        st.write(f"🟥 {candidate1_name}: {candidate1_votes} Electoral Votes")
        st.write(f"🟦 {candidate2_name}: {candidate2_votes} Electoral Votes")

        if candidate1_votes > candidate2_votes:
            st.success(f"🎉 {candidate1_name} wins the election!")
        elif candidate2_votes > candidate1_votes:
            st.success(f"🎉 {candidate2_name} wins the election!")
        else:
            st.warning("It's a tie! No clear winner.")

# Run the game
run_game()