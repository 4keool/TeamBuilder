import os
import time
import numpy as np
import shutil
import logging
from fastapi import FastAPI, UploadFile, Form, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from deap import base, creator, tools, algorithms
from load import load_data, load_prev_json
from save import save_results, json_to_png, save_update_team
from util import ensure_directory_exists
from genetic_algorithm import init_individual, custom_mutate, evaluate

class TaskState:
    def __init__(self):
        self.cancelled = False
        self.progress = 0.0
        self.remaining_time = 0
        self.result_path = None

app = FastAPI()
tasks = {}

creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
creator.create("Individual", list, fitness=creator.FitnessMin)

# 로그 설정
logging.basicConfig(
    filename='api.log',  # 로그를 저장할 파일명
    level=logging.DEBUG,  # 로그 레벨 설정 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format='%(asctime)s %(levelname)s:%(message)s'  # 로그 포맷 설정
)

def log_task_event(task_id: str, message: str, level: str = "debug"):
    """
    로깅 유틸리티 함수

    INPUT:
    - task_id (str): 요청하는 uuid의 값
    - message (str): 로그 메세지
    - level (str): 로그의 레벨을 나타냄

    OUTPUT:
    - 
    """
    log_message = f"Task {task_id} - {message}"
    if level == "debug":
        logging.debug(log_message)
    elif level == "error":
        logging.error(log_message)

def execute_genetic(task_id: str, num_teams, repeat, data_path):
    """
    실제 유전 알고리즘을 실행시키는 함수

    INPUT:
    - task_id (str): 요청하는 uuid의 값
    - num_teams : 팀의 수
    - repeat : 반복 횟수
    - data_path : players.json 파일의 위치

    OUTPUT:
    - result.json : 자세한 결과를 담은 json 파일
    - result.png : 공유를 위해 간략하게 시각화한 이미지 파일
    """

    task = tasks[task_id]
    
    try:
        logging.debug("Task {task_id} started")
        start_time = time.time()
        logging.debug("Loading data...")
        fixed_assignments, players = load_data(data_path)
        logging.debug("Setting up toolbox...")
        toolbox = setup_toolbox(num_teams, fixed_assignments, players)

        logging.debug("Creating population...")
        population, hof, stats = initialize_population(toolbox)

        for gen in range(repeat):
            if task.cancelled:
                logging.debug("Task {task_id} was cancelled.")
                break
            logging.debug(f"Generation {gen+1}...")

            process_generation(task_id, task, toolbox, population, hof, gen, repeat, start_time)
    except Exception as e:
        logging.error(f"Task {task_id} failed: {e}")
        task.result_path = None
    finally:
        finalize_task(task_id, task, hof, num_teams, players, repeat, data_path, start_time)

def setup_toolbox(num_teams, fixed_assignments, players):
    """
    유전 알고리즘을 실행하기 위한 Toolbox 설정

    INPUT:
    - num_teams : 팀의 수
    - fixed_assignments : 
    - players : 

    OUTPUT:
    - toolbox
    """

    toolbox = base.Toolbox()
    toolbox.register("individual", init_individual, num_teams, fixed_assignments, players)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    toolbox.register("mutate", custom_mutate, indpb=0.2, fixed_assignments=fixed_assignments, players=players, num_teams=num_teams)
    toolbox.register("evaluate", evaluate, num_teams=num_teams, players=players)
    toolbox.register("mate", tools.cxTwoPoint)
    toolbox.register("select", tools.selTournament, tournsize=3)
    return toolbox

def initialize_population(toolbox):
    """
    초기 Population 설정

    INPUT:
    - toolbox

    OUTPUT:
    - population
    - hof
    - stats
    """

    population = toolbox.population(n=300)
    hof = tools.HallOfFame(1)
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("avg", np.mean)
    stats.register("min", min)
    return population, hof, stats

def process_generation(task_id, task, toolbox, population, hof, gen, repeat, start_time):
    """
    세대별 작업 처리

    INPUT:
    - task_id (str): 요청하는 uuid의 값
    - task
    - toolbox
    - population
    - hof
    - gen
    - repeat
    - start_time

    OUTPUT:
    - population
    - hof
    """

    gen_start_time = time.time()

    population = algorithms.varAnd(population, toolbox, cxpb=0.5, mutpb=0.2)
    fits = toolbox.map(toolbox.evaluate, population)
    for fit, ind in zip(fits, population):
        ind.fitness.values = fit
    population = toolbox.select(population, len(population))
    hof.update(population)

    update_progress(task_id, task, gen, repeat, start_time, gen_start_time)

def update_progress(task_id, task, gen, repeat, start_time, gen_start_time):
    """
    작업 진행률 및 남은 시간 업데이트

    INPUT:
    - task_id (str): 요청하는 uuid의 값
    - task
    - gen
    - repeat
    - start_time
    - gen_start_time

    OUTPUT:
    - task.progress
    - task.remaining_time
    """

    task.progress = (gen + 1) / repeat * 100

    elapsed_time = time.time() - start_time
    gen_time = time.time() - gen_start_time
    remaining_time = gen_time * (repeat - gen - 1)
    task.remaining_time = int(remaining_time)

    log_task_event(task_id, f"Progress: {task.progress:.2f}%, Remaining Time: {task.remaining_time} seconds")

def finalize_task(task_id, task, hof, num_teams, players, repeat, data_path, start_time):
    """
    작업 종료 후 처리
    
    INPUT:
    - task_id (str): 요청하는 uuid의 값
    - task
    - hof
    - num_teams
    - players
    - repeat
    - data_path
    - start_time

    OUTPUT:
    - total_processing_time
    - task.result_path
    - task.progress
    - task.remaining_time
    """
    total_processing_time = time.time() - start_time
    result_path = save_results(hof[0], num_teams, players, repeat, data_path, total_processing_time)
    task.result_path = json_to_png(result_path)
    
    log_task_event(task_id, f"Results saved to {task.result_path}")
    
    task.progress = 100.0
    task.remaining_time = 0

def swap_members(data, swap_info):
    """
    팀 멤버들의 자리를 옮긴다.
    
    INPUT:
    - data: 원본 데이터가 들어있다.
    - swap_info: swap 해야하는 정보가 들어있다.

    OUTPUT:
    - update_data: 저장할 json 데이터가 들어있다.
    """
    swap_pairs = [pair.split(',') for pair in swap_info.split('|')]
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

@app.post("/start-task/")
async def start_task(
    background_tasks: BackgroundTasks,
    uuid: str = Form(...),
    file: UploadFile = Form(...),
    num_teams: int = Form(...),
    repeat: int = Form(...),
):
    """
    작업을 시작하는 부분
    
    uuid: 클라이언트가 제공한 고유 식별자 (UUID)
    file: 계삭하려는 players.json 파일이 담겨있음
    num_teams: 팀의 수
    repeat: 반복 횟수
    """
    if uuid in tasks and tasks[uuid].progress < 100:
        return JSONResponse({"message": "Another task is already running. Please wait until it finishes or cancel it first."}, status_code=400)

    data_path = f"data/{uuid}/{file.filename}"
    ensure_directory_exists(f"data/{uuid}")
    try:
        with open(data_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logging.error(f"Failed to save file: {e}")
        return JSONResponse({"message:": "Failed to save file."}, status_code=500)

    tasks[uuid] = TaskState()
    background_tasks.add_task(execute_genetic, uuid, num_teams, repeat, data_path)

    return {"message": "Task started", "uuid": uuid}

@app.get("/progress/")
async def get_progress(uuid: str = Form(...)):
    """
    작업 진행사항을 확인하는 부분
    
    uuid: 클라이언트가 제공한 고유 식별자 (UUID)
    """
    task = tasks.get(uuid)

    if not task:
        return {"error": "Invalid UUID or task not found"}
    
    return {"progress": task.progress, "remaining time": task.remaining_time}

@app.post("/cancel-task/")
async def cancel_task(uuid: str = Form(...)):
    """
    작업을 취소하는 엔드포인트.
    
    uuid: 클라이언트가 제공한 고유 식별자 (UUID)
    """
    task = tasks.get(uuid)
    
    if not task:
        return {"error": "Invalid UUID or task not found"}
    
    task.cancelled = True
    return {"message": f"Task {uuid} cancelled."}

@app.get("/result/")
async def get_result(uuid: str = Form(...)):
    """
    작업 결과와 진행 상황을 가져오는 엔드포인트.
    
    uuid: 클라이언트가 제공한 고유 식별자 (UUID)
    """
    task = tasks.get(uuid)
    
    if not task:
        return {"error": "Invalid UUID or task not found"}
    
    if task.result_path:
        # 결과가 준비되었으면 파일 경로와 함께 응답
        return FileResponse(task.result_path, media_type='image/png', filename="result.png")
    else:
        # 진행 상황을 반환
        return {"status": "Task in progress", "progress": task.progress, "remaining time": task.remaining_time}

@app.get("/init-file/")
async def get_initial_file():
    """
    초기 파일을 제공하는 API 엔드포인트.
    
    Returns:
    FileResponse: 초기 파일을 포함한 응답
    """
    file_path = "players.backup"  # 초기 파일 경로를 지정합니다.
    return FileResponse(file_path, media_type='application/json', filename="players_.json")

@app.post("/swap/")
async def swap_teams(uuid: str = Form(...),
    swap_info: str = Form(...)):
    """
    결과값을 수정하기 위한 APIA 엔드포인트.

    uuid: 클라이언트가 제공한 고유 식별자 (UUID)
    swapinfo: 어떤 값들은 변경할지에 대한 정보
    """
    task = tasks.get(uuid)
    if not task:
        return {"error": "Invalid UUID or task not found"}

    if task.result_path != None:
        prev_png_path = task.result_path
        prev_json_path = os.path.splitext(prev_png_path)[0] + ".json"

        data = load_prev_json(prev_json_path)

        if 'parameters' not in data:
            data['parameters'] = {}
        data['parameters']['original_data'] = prev_json_path
        data['parameters']['swap_info'] = swap_info

        task.progress = 0
        task.remaining_time = 9999

        update_data = swap_members(data, swap_info)
        new_json_path = save_update_team(prev_json_path, update_data)
        task.result_path = json_to_png(new_json_path)

        task.progress = 100
        task.remaining_time = 0
        return {"update team data"}

    else:
        log_task_event(uuid, f"else")
        return {"status": "Task in progress", "progress": task.progress, "remaining time": task.remaining_time}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)