import os
import json
import argparse

def ensure_directory_exists(directory):
    """
    주어진 디렉토리가 존재하는지 확인하고, 없으면 생성하는 함수.
    
    INPUT:
    - directory (str): 생성할 디렉토리 경로
    
    OUTPUT:
    - 없음
    """
    if not os.path.exists(directory):
        os.makedirs(directory)

def parse_args():
    """
    명령줄 인수를 파싱하는 함수.
    
    INPUT:
    - 없음
    
    OUTPUT:
    - argparse.Namespace: 명령줄 인수로부터 파싱된 값들을 반환합니다.
    """
    parser = argparse.ArgumentParser(description="Team assignment using genetic algorithms.")
    parser.add_argument("--num_teams", type=int, required=True, help="Number of teams to distribute players among.")
    parser.add_argument("--repeat", type=int, default=1000, help="Number of generations for the genetic algorithm.")
    parser.add_argument("--data_path", type=str, default="players.json", help="Path to the players data file.")
    return parser.parse_args()
