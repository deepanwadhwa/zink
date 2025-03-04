import pickle

# Load the saved Aho–Corasick automaton from pickle
with open("medical_conditions_automaton.pkl", "rb") as f:
    automaton = pickle.load(f)

def longest_match(text):
    longest = ""
    # Iterate over all matches in the text using the loaded automaton
    for end_index, word in automaton.iter(text):
        if len(word) > len(longest):
            longest = word
    return longest
