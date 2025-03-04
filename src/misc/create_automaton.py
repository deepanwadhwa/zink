import csv
import ahocorasick
import pickle

# File path to the CSV file (adjust as needed)
input_file = "codes.csv"

# Read the CSV file and extract the description column (assumed at index 3)
descriptions = []
with open(input_file, newline='', encoding="utf-8") as f:
    reader = csv.reader(f)
    for row in reader:
        # Check that the row has at least 4 columns
        if len(row) >= 4:
            # Strip to remove any surrounding whitespace/quotes
            descriptions.append(row[3].strip())

print("Extracted Descriptions:")
for d in descriptions:
    print(d)

# Build the Aho–Corasick automaton with the description strings as patterns
automaton = ahocorasick.Automaton()
for desc in descriptions:
    automaton.add_word(desc, desc)
automaton.make_automaton()

# Dump the automaton to a pickle file
with open("medical_conditions_automaton.pkl", "wb") as out_file:
    pickle.dump(automaton, out_file)

print("Automaton built and saved to 'automaton.pkl'")
