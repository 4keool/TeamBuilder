import os
import json
import random
import argparse
from deap import creator

# 명령줄 인수 처리 함수
def parse_args():
    parser = argparse.ArgumentParser(description="Team assignment using genetic algorithms.")
    parser.add_argument("--num_teams", type=int, required=True, help="Number of teams to distribute players among.")
    parser.add_argument("--repeat", type=int, default=1000, help="Number of generations for the genetic algorithm.")
    parser.add_argument("--data_path", type=str, default="players.json", help="Path to the players data file.")
    return parser.parse_args()

# 데이터 로드 함수
def load_data(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
        # max 값이 None인 경우 0으로 설정
        for player in data['players']:
            if player.get('max') is None:
                player['max'] = 0
        return data['fixed_assignments'], data['players']
    except FileNotFoundError:
        raise FileNotFoundError("Data file not found.")
    except json.JSONDecodeError:
        raise json.JSONDecodeError("Error decoding JSON.")

# 고정 선수를 고려한 초기 개체 생성 함수
def init_individual(num_teams, fixed_assignments, players):
    individual = [random.randint(0, num_teams - 1) for _ in range(len(players))]
    for i, player in enumerate(players):
        if player['name'] in fixed_assignments:
            individual[i] = fixed_assignments[player['name']]
    return creator.Individual(individual)

# 변이 함수: 고정된 선수는 변이하지 않음
def custom_mutate(individual, indpb, fixed_assignments, players, num_teams):
    fixed_indices = [i for i, p in enumerate(players) if p['name'] in fixed_assignments.keys()]
    for i in range(len(individual)):
        if i not in fixed_indices and random.random() < indpb:
            individual[i] = random.randint(0, num_teams - 1)
    return individual,

# 적합도 평가: 팀의 인원 수 및 점수의 균형 평가
def evaluate(individual, num_teams, players):
    team_counts = [0] * num_teams
    team_avg_scores = [0] * num_teams
    team_max_scores = [0] * num_teams
    
    for player, team in zip(players, individual):
        team_counts[team] += 1
        team_avg_scores[team] += player['avg']
        team_max_scores[team] += player['max']
    
    if min(team_counts) < len(players) // num_teams:
        return (1000,)
    
    team_avg_score_balance = max(team_avg_scores) - min(team_avg_scores)
    team_max_score_balance = max(team_max_scores) - min(team_max_scores)
    
    avg_score_variance = sum((score - sum(team_avg_scores) / num_teams) ** 2 for score in team_avg_scores) / num_teams
    max_score_variance = sum((score - sum(team_max_scores) / num_teams) ** 2 for score in team_max_scores) / num_teams
    
    return (team_avg_score_balance + team_max_score_balance + avg_score_variance + max_score_variance * 0.7,)

# 결과 데이터를 JSON 파일에 저장하는 함수
def save_results(best_individual, num_teams, players, repeat, data_path, elapsed_time):
    teams = [[] for _ in range(num_teams)]
    for player, team_number in zip(players, best_individual):
        teams[team_number].append(player)
    
    for team in teams:
        team.sort(key=lambda x: x['avg'], reverse=True)
    
    result_data = {
        'parameters': {
            'num_teams': num_teams,
            'repeat': repeat,
            'data_path': data_path,
            'run_time': round(elapsed_time, 2)
        },
        'results': {
            f"Team {i+1}": {
                "Total Score": round(sum(p['avg'] for p in team), 1),
                "Members": {p["name"]: round(p["avg"], 1) for p in team}
            } for i, team in enumerate(teams)
        }
    }
    
    dirname = os.path.dirname(data_path)
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    filename = os.path.join(dirname, "result.json")
    index = 1
    while os.path.exists(filename):
        filename = os.path.join(dirname, f"result{index}.json")
        index += 1
    
    with open(filename, "w", encoding='utf-8') as f:
        json.dump(result_data, f, ensure_ascii=False, indent=4)
    
    return filename

