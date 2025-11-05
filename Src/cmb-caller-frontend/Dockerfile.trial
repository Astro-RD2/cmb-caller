# 使用 Python 官方映像
FROM python:3.9-slim

# 設定無緩衝環境
ENV PYTHONUNBUFFERED=1

ENV TZ=Asia/Taipei
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 設置工作目錄
WORKDIR /app

# 複製程式碼到容器中
#COPY . .
COPY cmb-caller-frontend_trial.py .
COPY requirements.txt .

# 安裝 pip 最新版本
#RUN pip install --upgrade pip

# 安裝 requirements.txt 中的所有依賴
RUN pip install --no-cache-dir -r requirements.txt

# 設置環境變數
ENV PORT 8080
# 暴露端口
EXPOSE $PORT

# 運行伺服器
CMD ["python", "cmb-caller-frontend_trial.py"]


