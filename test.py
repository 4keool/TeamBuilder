import json
import sys
from main import main  # Make sure that the main.py and func.py are in a state where they can be imported like this

# Mock data to simulate command line arguments and input data
sys.argv = ["main.py", "--num_teams", "4", "--repeat", "100", "--data_path", "data.json"]

# Mock input file creation (data.json)
data = {
    "fixed_assignments": [],
    "players": [{"name": "Player1", "avg": 50, "max": 75}, {"name": "Player2", "avg": 55, "max": 80}]
}
with open("data.json", 'w') as f:
    json.dump(data, f)

# Running the main function to see output
if __name__ == "__main__":
    main()
