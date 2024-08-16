import time
import threading
import logging
from fastapi import FastAPI, UploadFile, Form, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from typing import Optional
import shutil
from deap import base, creator, tools, algorithms
import numpy as np
from load import load_data
from save import save_results, json_to_png
from genetic_algorithm import init_individual, custom_mutate, evaluate
from util import ensure_directory_exists

# 로그 설정
logging.basicConfig(
    filename='genetic_algorithm.log',  # 로그를 저장할 파일명
    level=logging.DEBUG,  # 로그 레벨 설정 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format='%(asctime)s %(levelname)s:%(message)s'  # 로그 포맷 설정
)

app = FastAPI()

# 모든 작업 상태를 저장할 딕셔너리 (UUID를 키로 사용)
tasks = {}

class TaskState:
    def __init__(self):
        self.cancelled = False
        self.progress = 0.0
        self.remaining_time = 0
        self.result_path = None

creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
creator.create("Individual", list, fitness=creator.FitnessMin)

def genetic_algorithm_task(task_id: str, num_teams, repeat, data_path):
    task = tasks[task_id]
    
    try:
        logging.debug("Task {task_id} started")
        start_time = time.time()
        logging.debug("Loading data...")
        fixed_assignments, players = load_data(data_path)
        logging.debug("Setting up toolbox...")
        toolbox = base.Toolbox()
        toolbox.register("individual", init_individual, num_teams, fixed_assignments, players)
        toolbox.register("population", tools.initRepeat, list, toolbox.individual)
        toolbox.register("mutate", custom_mutate, indpb=0.2, fixed_assignments=fixed_assignments, players=players, num_teams=num_teams)
        toolbox.register("evaluate", evaluate, num_teams=num_teams, players=players)
        toolbox.register("mate", tools.cxTwoPoint)
        toolbox.register("select", tools.selTournament, tournsize=3)

        logging.debug("Creating population...")
        population = toolbox.population(n=300)
        hof = tools.HallOfFame(1)
        stats = tools.Statistics(lambda ind: ind.fitness.values)
        stats.register("avg", np.mean)
        stats.register("min", min)

        for gen in range(repeat):
            if task.cancelled:
                logging.debug("Task {task_id} was cancelled.")
                break
            logging.debug(f"Generation {gen+1}...")

            gen_start_time = time.time()

            population = algorithms.varAnd(population, toolbox, cxpb=0.5, mutpb=0.2)
            fits = toolbox.map(toolbox.evaluate, population)
            for fit, ind in zip(fits, population):
                ind.fitness.values = fit
            population = toolbox.select(population, len(population))
            hof.update(population)

            # 진행률 및 남은 시간 업데이트
            elapsed_time = time.time() - start_time
            progress = (gen + 1) / repeat * 100
            task.progress = progress
            
            gen_time = time.time() - gen_start_time
            remaining_time = gen_time * (repeat - gen - 1)
            task.remaining_time = int(remaining_time)

        total_processing_time = time.time() - start_time
        logging.debug("Task {task_id} Saving results...")
        result_path = save_results(hof[0], num_teams, players, repeat, data_path, total_processing_time)
        logging.debug(f"Results saved to {result_path}")

        png_path = json_to_png(result_path)
        task.result_path = png_path
        logging.debug(f"PNG saved to {png_path}")
    except Exception as e:
        logging.error(f"Task {task_id} failed: {e}")
        task.result_path = None
    finally:
        task.progress = 100.0
        task.remaining_time = 0


@app.post("/start-task/")
async def start_task(
    background_tasks: BackgroundTasks,
    uuid: str = Form(...),
    file: UploadFile = Form(...),
    num_teams: int = Form(...),
    repeat: int = Form(...),
):
    
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

    # 새로운 작업 상태를 생성하고 UUID에 매핑
    task_state = TaskState()
    tasks[uuid] = task_state

    background_tasks.add_task(genetic_algorithm_task, uuid, num_teams, repeat, data_path)

    return {"message": "Task started", "uuid": uuid}

@app.get("/progress/")
async def get_progress(uuid: str = Form(...)):
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
        return {"status": "Task in progress", "progress": task.progress}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)