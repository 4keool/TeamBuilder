import random
from deap import creator

def init_individual(num_teams, fixed_assignments, players):
    """
    초기 개체(유전자)를 생성하는 함수.
    고정된 선수들은 지정된 팀에 할당되고, 나머지 선수들은 임의로 할당됩니다.

    INPUT:
    - num_teams (int): 팀의 수
    - fixed_assignments (dict): 고정된 선수의 팀 배정 정보
    - players (list): 일반 선수 리스트

    OUTPUT:
    - individual (creator.Individual): 초기화된 개체
    """
    individual = [random.randint(0, num_teams - 1) for _ in range(len(players))]
    for i, player in enumerate(players):
        if player['name'] in fixed_assignments:
            individual[i] = fixed_assignments[player['name']]
    return creator.Individual(individual)

def custom_mutate(individual, indpb, fixed_assignments, players, num_teams):
    """
    개체(유전자)에 변이를 적용하는 함수.
    고정된 선수들은 변이하지 않도록 처리됩니다.

    INPUT:
    - individual (list): 변이를 적용할 개체
    - indpb (float): 변이 확률
    - fixed_assignments (dict): 고정된 선수의 팀 배정 정보
    - players (list): 일반 선수 리스트
    - num_teams (int): 팀의 수

    OUTPUT:
    - individual (list): 변이가 적용된 개체
    """
    fixed_indices = [i for i, p in enumerate(players) if p['name'] in fixed_assignments.keys()]
    for i in range(len(individual)):
        if i not in fixed_indices and random.random() < indpb:
            individual[i] = random.randint(0, num_teams - 1)
    return individual,

def evaluate(individual, num_teams, players):
    """
    개체(팀 배정)의 적합도를 평가하는 함수.
    팀의 인원 수와 평균 점수, 최고 점수의 균형을 평가합니다.

    INPUT:
    - individual (list): 팀 배정 정보가 담긴 개체
    - num_teams (int): 팀의 수
    - players (list): 일반 선수 리스트

    OUTPUT:
    - fitness (tuple): 평가된 적합도 값 (값이 작을수록 적합함)
    """
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
