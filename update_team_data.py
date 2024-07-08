import json
import argparse
import os

def load_json(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(filepath, data):
    dirname = os.path.dirname(filepath)
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    
    filename = os.path.join(dirname, "result.json")
    index = 1
    while os.path.exists(filename):
        filename = os.path.join(dirname, f"result{index}.json")
        index += 1
    
    with open(filename, "w", encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def swap_members(data, swap_info):
    swap_pairs = [pair.split(',') for pair in swap_info.split(';')]
    swap_dict = {item.strip(): None for pair in swap_pairs for item in pair}
    
    team_data = data['results']
    
    for team_name, team_info in team_data.items():
        members = team_info['Members']
        for member in members:
            if member in swap_dict:
                swap_dict[member] = (team_name, member, members[member])
    
    for member1, member2 in swap_pairs:
        member1, member2 = member1.strip(), member2.strip()
        team1, name1, score1 = swap_dict[member1]
        team2, name2, score2 = swap_dict[member2]
        
        # Swap members and their scores
        data['results'][team1]['Members'].pop(name1)
        data['results'][team2]['Members'].pop(name2)
        
        data['results'][team1]['Members'][member2] = score2
        data['results'][team2]['Members'][member1] = score1
        
        data['results'][team1]['Total Score'] += score2 - score1
        data['results'][team2]['Total Score'] += score1 - score2
    
    for team_name, team_info in team_data.items():
        sorted_members = dict(sorted(team_info['Members'].items(), key=lambda item: item[1], reverse=True))
        data['results'][team_name]['Members'] = sorted_members
    
    return data

def main():
    parser = argparse.ArgumentParser(description='Swap team members and update scores in a JSON file.')
    parser.add_argument('--filepath', type=str, required=True, help='The path to the result JSON file')
    parser.add_argument('--swap_info', type=str, required=True, help='The swap information in the format "member1,member2; member3,member4; ..."')
    
    args = parser.parse_args()
    
    data = load_json(args.filepath)
    
    # Add swap_info to parameters
    if 'parameters' not in data:
        data['parameters'] = {}
    data['parameters']['original_data'] = args.filepath
    data['parameters']['swap_info'] = args.swap_info
    
    updated_data = swap_members(data, args.swap_info)
    
    save_json(args.filepath, updated_data)

if __name__ == '__main__':
    main()
