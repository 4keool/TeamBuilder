import json

def load_data(file_path):
    """
    주어진 경로에서 JSON 데이터를 로드하고 고정된 선수와 일반 선수 리스트를 반환하는 함수.

    INPUT:
    - file_path (str): 데이터를 로드할 파일의 경로

    OUTPUT:
    - fixed_assignments (dict): 고정된 선수의 팀 배정 정보
    - players (list): 일반 선수 리스트
    """
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

def load_prev_json(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)