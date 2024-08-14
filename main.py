import sys
import time
import numpy
from deap import base, creator, tools, algorithms
from load import load_data
from save import save_results, json_to_png
from genetic_algorithm import init_individual, custom_mutate, evaluate
from util import parse_args, ensure_directory_exists

# 최소화 적합도 생성
creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
# 개체 인스턴스 생성
creator.create("Individual", list, fitness=creator.FitnessMin)

def main():
    """
    유전자 알고리즘을 실행하여 팀을 배정하는 메인 함수.
    프로그램이 시작되면 명령줄 인수를 파싱하고, 데이터 로드, 개체 초기화,
    유전자 알고리즘을 실행하며, 중간 및 최종 결과를 저장합니다.

    INPUT:
    - 없음 (명령줄 인수로부터 값을 가져옵니다)

    OUTPUT:
    - 없음 (결과는 파일로 저장되거나 화면에 출력됩니다)
    """
    args = parse_args()  # 명령줄 인수 분석

    if args.num_teams <= 0:
        print("num_teams cannot be empty.")  # 팀 수 유효성 확인
        sys.exit(1)

    num_teams = args.num_teams
    repeat = args.repeat
    data_path = args.data_path

    # 데이터 로드 및 디렉토리 확인
    ensure_directory_exists(data_path)
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
    start_time = time.time()  # 시작 시간 기록
    population = toolbox.population(n=300)  # 초기 개체 집단 생성
    hof = tools.HallOfFame(1)  # 가장 우수한 개체를 저장할 구조
    stats = tools.Statistics(lambda ind: ind.fitness.values)  # 통계 정보 생성
    stats.register("avg", numpy.mean)  # 평균 적합도 등록
    stats.register("min", min)  # 최소 적합도 등록

    printunit = 100  # 중간 결과를 출력할 주기
    measured_generations = 0  # 측정된 세대 수
    measured_time = 0  # 측정된 시간
    estimation_started = False  # 시간 예측 시작 여부
    total_estimated_time = None  # 전체 예상 소요 시간

    try:
        for gen in range(repeat):
            gen_start_time = time.time()  # 세대 시작 시간
            population = algorithms.varAnd(population, toolbox, cxpb=0.5, mutpb=0.2)  # 교차 및 변이 적용
            fits = toolbox.map(toolbox.evaluate, population)  # 적합도 평가
            for fit, ind in zip(fits, population):
                ind.fitness.values = fit
            population = toolbox.select(population, len(population))  # 선택 연산 수행
            hof.update(population)  # 가장 우수한 개체 업데이트

            gen_end_time = time.time()  # 세대 종료 시간
            gen_duration = gen_end_time - gen_start_time  # 세대 수행 시간 계산

            # 시간 예측을 위한 초기 1~2초 측정
            if not estimation_started:
                measured_generations += 1
                measured_time += gen_duration
                if measured_time >= 1.0:  # 1초 이상 측정되면 예상 시간 계산 시작
                    avg_time_per_gen = measured_time / measured_generations
                    total_estimated_time = avg_time_per_gen * repeat  # 전체 예상 소요 시간 계산
                    estimation_started = True

            if gen % printunit == 0:  # 중간 결과 출력 시점
                record = stats.compile(population)
                print(f"Gen: {gen+printunit}/{repeat}, Stats: {record}")
                
                if estimation_started:
                    elapsed_time = time.time() - start_time  # 현재까지 경과 시간 계산
                    completion_percentage = (elapsed_time / total_estimated_time) * 100  # 진행 상황 퍼센트 계산
                    print(f"Progress: {completion_percentage:.2f}% completed. "
                          f"Elapsed Time: {elapsed_time:.2f} sec, "
                          f"Estimated Total Time: {total_estimated_time:.2f} sec")

    except KeyboardInterrupt:
        print("\nAlgorithm interrupted. Saving current best result...")  # 알고리즘 중단 시 메시지 출력
    finally:
        end_time = time.time()  # 종료 시간 기록
        elapsed_time = end_time - start_time  # 전체 경과 시간 계산
        result_path = save_results(hof[0], num_teams, players, repeat, data_path, elapsed_time)  # 결과 저장
        json_to_png(result_path)  # 결과를 이미지로 변환 및 저장
        print(f"Results saved successfully. Elapsed Time: {elapsed_time:.2f} sec.")  # 최종 결과와 경과 시간 출력

if __name__ == "__main__":
    main()
