# 베이스 이미지로 Python 3.9을 사용합니다.
FROM python:3.9

# 작업 디렉토리를 설정합니다.
WORKDIR /app

# 필요한 패키지 목록을 복사합니다.
COPY requirements.txt .

# 필요한 패키지를 설치합니다.
RUN pip install --no-cache-dir -r requirements.txt

# sudo와 fonts-nanum을 설치합니다.
RUN apt update && \
    apt install -y sudo && \
    sudo apt-get install -y fonts-nanum && \
    apt install -y vim

# 애플리케이션 파일들을 복사합니다.
COPY . .

# uvicorn을 통해 FastAPI 애플리케이션을 실행합니다.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
