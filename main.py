import sys
import time
import json
import numpy
from deap import base, creator, tools, algorithms
from func import load_data, init_individual, custom_mutate, evaluate, save_results, parse_args

# 최소화 적합도 생성
creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
# 개체 인스턴스 생성
creator.create("Individual", list, fitness=creator.FitnessMin)

def main():
    args = parse_args()  # 인자 분석

    if args.num_teams <= 0:
        print("num_teams cannot be empty.")  # 팀 수 유효성 확인
        sys.exit(1)

    num_teams = args.num_teams
    repeat = args.repeat
    data_path = args.data_path

    # 데이터 로드 및 툴박스 설정
    try:
        fixed_assignments, players = load_data(data_path)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading data: {str(e)}")
        sys.exit(1)
        
    toolbox = base.Toolbox()
    toolbox.register("individual", init_individual, num_teams, fixed_assignments, players)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    toolbox.register("mutate", custom_mutate, indpb=0.2, fixed_assignments=fixed_assignments, players=players, num_teams=num_teams)
    toolbox.register("evaluate", evaluate, num_teams=num_teams, players=players)
    toolbox.register("mate", tools.cxTwoPoint)
    toolbox.register("select", tools.selTournament, tournsize=3)

    # 유전 알고리즘 실행
    start_time = time.time()
    population = toolbox.population(n=300)
    hof = tools.HallOfFame(1)
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("avg", numpy.mean)
    stats.register("min", min)

    printunit = 100
    for gen in range(repeat):
        population = algorithms.varAnd(population, toolbox, cxpb=0.5, mutpb=0.2)
        fits = toolbox.map(toolbox.evaluate, population)
        for fit, ind in zip(fits, population):
            ind.fitness.values = fit
        population = toolbox.select(population, len(population))
        hof.update(population)
        if gen % printunit == 0:
            record = stats.compile(population)
            print(f"Gen: {gen+printunit}/{repeat}, Stats: {record}")

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Elapsed Time: {elapsed_time:.2f} seconds")
    result_path = save_results(hof[0], num_teams, players, repeat, data_path, elapsed_time)

if __name__ == "__main__":
    main()
