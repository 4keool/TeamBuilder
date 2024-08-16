import os
import json

def save_results(best_individual, num_teams, players, repeat, data_path, elapsed_time):
    """
    최적의 팀 배정 결과를 JSON 파일로 저장하는 함수.

    INPUT:
    - best_individual (list): 최적의 팀 배정 정보를 담은 개체
    - num_teams (int): 팀의 수
    - players (list): 일반 선수 리스트
    - repeat (int): 유전자 알고리즘의 반복 횟수
    - data_path (str): 데이터 파일 경로
    - elapsed_time (float): 알고리즘 수행 시간

    OUTPUT:
    - filename (str): 결과 JSON 파일의 경로
    """
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
    
    print(f"Save Json : {filename}")

    return filename

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from PIL import Image
def json_to_png(json_path):
    """
    JSON 파일을 읽어 팀 배정 결과를 시각화하여 PNG 파일로 저장하는 함수.

    INPUT:
    - json_path (str): JSON 파일 경로

    OUTPUT:
    - png_image_path (str): 생성된 PNG 이미지 파일의 경로
    """
    # JSON 파일을 읽어와 데이터를 로드합니다.
    with open(json_path, 'r', encoding='utf-8') as file:
        data = json.load(file)

    # 모든 팀의 이름을 추출합니다.
    teams = list(data['results'].keys())

    # 팀 이름과 총점, 멤버, 점수를 저장할 리스트 초기화
    team_names = []
    total_scores = []
    member_lists = []
    score_lists = []

    # 각 팀에 대해 데이터를 추출하여 리스트에 저장합니다.
    for team in teams:
        team_names.append(team)
        total_scores.append(data['results'][team]["Total Score"])
        member_lists.append(list(data['results'][team]["Members"].keys()))
        score_lists.append(list(data['results'][team]["Members"].values()))

    # 가장 많은 멤버를 가진 팀의 멤버 수를 구합니다.
    max_members = max(len(members) for members in member_lists)

    # 멤버 수가 적은 팀의 리스트에 빈 문자열을 추가하여 길이를 맞춥니다.
    for i in range(len(member_lists)):
        while len(member_lists[i]) < max_members:
            member_lists[i].append('')
            score_lists[i].append('')

    # 컬럼을 생성하고, 팀 이름과 총점을 헤더로 사용하여 DataFrame을 구성합니다.
    columns = []
    data_dict = {}

    for i in range(len(teams)):
        columns.append(f"{team_names[i]}")
        columns.append(f"{total_scores[i]}")
        data_dict[columns[-2]] = member_lists[i]
        data_dict[columns[-1]] = score_lists[i]

    df = pd.DataFrame(data_dict)

    # 한글을 지원하는 폰트를 불러옵니다.
    font_path = '/usr/share/fonts/truetype/nanum/NanumGothic.ttf'
    if not os.path.exists(font_path):
        print("Error: 폰트를 불러올 수 없습니다. 시스템에 'NanumGothic' 폰트가 설치되지 않았을 수 있습니다.")
        print("설치하려면 터미널에 다음 명령어를 실행하세요: sudo apt-get install fonts-nanum")
        return  # 폰트가 없으면 작업을 중지합니다.

    fontprop = fm.FontProperties(fname=font_path)

    # Excel 스타일의 표를 이미지로 생성합니다.
    fig, ax = plt.subplots(figsize=(10, len(df) * 0.5))  # 이미지 크기를 데이터에 맞춰 동적으로 설정합니다.
    ax.axis('tight')  # 그래프의 축을 타이트하게 조정합니다.
    ax.axis('off')  # 그래프의 축을 숨깁니다.
    the_table = ax.table(cellText=df.values, colLabels=df.columns, cellLoc='center', loc='center')

    # 테이블의 모든 셀에 폰트를 적용합니다.
    the_table.auto_set_font_size(False)
    the_table.set_fontsize(12)

    # team_names와 total_scores의 컬럼에 대해 폰트 크기를 키우고 굵게 설정하며 셀의 높이를 조정합니다.
    bold_fontprop = fontprop.copy()
    bold_fontprop.set_weight('bold')
    bold_fontprop.set_size(14)  # 폰트 크기를 14로 설정

    for col_idx in range(0, len(columns), 2):  # team_names와 total_scores의 인덱스는 짝수입니다.
        the_table[0, col_idx].set_text_props(fontproperties=bold_fontprop)
        the_table[0, col_idx + 1].set_text_props(fontproperties=bold_fontprop)

        # 셀의 높이를 조정하여 겹치지 않도록 합니다.
        the_table[0, col_idx].set_height(the_table[0, col_idx].get_height() * 1.5)
        the_table[0, col_idx + 1].set_height(the_table[0, col_idx + 1].get_height() * 1.5)

    # 나머지 셀에는 기본 폰트를 적용합니다.
    for key, cell in the_table.get_celld().items():
        if key[0] > 0:  # 첫 번째 행은 건너뜁니다.
            cell.set_text_props(fontproperties=fontprop)

    # 이미지를 PNG 파일로 저장합니다.
    png_image_path = json_path.replace('.json', '.png')
    plt.savefig(png_image_path, bbox_inches='tight', dpi=300)

    print(f"Save Png : {png_image_path}")

    # 생성된 PNG 파일의 경로를 반환합니다.
    return png_image_path

def save_update_team(filepath, data):
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

    return filename