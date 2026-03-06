
#!/bin/bash

# 使用方式: bash deploy.sh trial | live | live_ok
set +e

RAW_MODE="$1"
# 先將 MODE 轉成小寫
MODE=$(echo "$RAW_MODE" | tr '[:upper:]' '[:lower:]')

if [ -z "$MODE" ]; then
  echo "請指定模式：trial、live 或 live_ok"
  return 1 2>/dev/null || exit 1
fi

# 僅接受 trial / live / live_ok
if [ "$MODE" != "trial" ] && [ "$MODE" != "live" ] && [ "$MODE" != "live_ok" ]; then
  echo "請指定模式：trial、live 或 live_ok"
  return 1 2>/dev/null || exit 1  # 若是被 source，return；否則 exit
fi

echo -e "當前部署模式：\033[1m$MODE\033[0m"

# LIVE 與 LIVE_OK 模式都需要確認提示
if [ "$MODE" == "live" ] || [ "$MODE" == "live_ok" ]; then
  echo -e "\n\033[1;31m警告：您正在部署到 LIVE 生產環境！\033[0m"
  echo -e "\033[1;33m請確認以下事項：\033[0m"
  echo "1. 代碼已通過測試"
  echo "2. 已備份重要數據"
  echo "3. 已通知相關人員"
  echo -e "\n\033[1;33m按任意鍵繼續部署，或按 Ctrl+C 取消...\033[0m"
  read -n 1 -s -r
  echo -e "\n\033[1;32m繼續部署 LIVE 環境...\033[0m\n"
fi

# =========================
# 設定環境參數
# =========================
if [ "$MODE" == "trial" ]; then
  PROJECT_ID='callme-op-419108'
  PY_FILE='cmb-caller-frontend_trial.py'
  TIMEOUT=300
  MIN_INSTANCES=0
else
  # live 與 live_ok 都是生產專案，但 PY 檔名略有差異
  PROJECT_ID='callme-398802'
  TIMEOUT=3600
  MIN_INSTANCES=1

  if [ "$MODE" == "live" ]; then
    PY_FILE='cmb-caller-frontend.py'
  else
    # live_ok：優先使用 _ok.py，若不存在則使用 _OK.py
    if [ -f "cmb-caller-frontend_ok.py" ]; then
      PY_FILE='cmb-caller-frontend_ok.py'
    elif [ -f "cmb-caller-frontend_OK.py" ]; then
      PY_FILE='cmb-caller-frontend_OK.py'
    else
      echo "找不到 cmb-caller-frontend_ok.py 或 cmb-caller-frontend_OK.py，請確認檔案存在。"
      return 1 2>/dev/null || exit 1
    fi
  fi
fi

SERVICE_NAME='cmb-caller-frontend'
REGION="asia-east1"

# 根據 Artifact Registry 的正確格式定義 IMAGE_NAME
IMAGE_NAME="${REGION}-docker.pkg.dev/${PROJECT_ID}/cloud-run-source-deploy/${SERVICE_NAME}:latest"

# 設定嚴格模式：任何命令失敗立即退出（如需可開啟）
# set -e

echo -e "\n=== 當前目錄文件列表 ==="
ls -latr || true  # 非關鍵命令，失敗時不退出

echo -e "\n=== 部署開始 ==="
start_time=$(date +%s)
date || true  # 非關鍵命令，失敗時不退出

echo -e "\n=== 準備Dockerfile ==="
# live_ok 優先 Dockerfile.live_ok，不存在則回退 Dockerfile.live
DOCKER_MODE="$MODE"
if [ "$MODE" == "live_ok" ]; then
  if [ -f "Dockerfile.live_ok" ]; then
    DOCKER_MODE="live_ok"
  elif [ -f "Dockerfile.live" ]; then
    echo "提示：未找到 Dockerfile.live_ok，改用 Dockerfile.live"
    DOCKER_MODE="live"
  else
    echo "找不到 Dockerfile.live_ok 或 Dockerfile.live，請確認檔案存在。"
    return 1 2>/dev/null || exit 1
  fi
fi

# 一般模式檔案檢查
if [ ! -f "Dockerfile.$DOCKER_MODE" ]; then
  echo "找不到 Dockerfile.$DOCKER_MODE，請確認檔案存在。"
  return 1 2>/dev/null || exit 1
fi

cp -a "Dockerfile.$DOCKER_MODE" Dockerfile
file -i "$PY_FILE" requirements.txt Dockerfile || true  # 非關鍵命令，失敗時不退出

echo -e "\n=== 設置Pub/Sub ==="
# 檢查並創建 Pub/Sub topic
if ! gcloud pubsub topics describe cross-instance-comms --project="$PROJECT_ID" 2>/dev/null; then
  gcloud pubsub topics create cross-instance-comms --project="$PROJECT_ID" || true  # 容忍創建失敗
  echo "Pub/Sub topic 'cross-instance-comms' 已創建。"
else
  echo "Pub/Sub topic 'cross-instance-comms' 已存在。"
fi

# 檢查並創建 Pub/Sub subscription
if ! gcloud pubsub subscriptions describe version-sub --project="$PROJECT_ID" 2>/dev/null; then
  gcloud pubsub subscriptions create version-sub \
    --topic=cross-instance-comms \
    --project="$PROJECT_ID" || true  # 容忍創建失敗
  echo "Pub/Sub subscription 'version-sub' 已創建。"
else
  echo "Pub/Sub subscription 'version-sub' 已存在。"
fi

echo -e "\n=== 構建Docker映像 ==="
gcloud builds submit . --tag "$IMAGE_NAME" --project="$PROJECT_ID"

echo -e "\n=== 部署Cloud Run服務 ==="
DEPLOY_TIMESTAMP=$(date +%s)

gcloud beta run deploy "$SERVICE_NAME" \
  --image="$IMAGE_NAME" \
  --region="$REGION" \
  --project="$PROJECT_ID" \
  --platform=managed \
  --allow-unauthenticated \
  --memory=2Gi \
  --cpu=1 \
  --execution-environment=gen2 \
  --timeout=$TIMEOUT \
  --service-min-instances=$MIN_INSTANCES \
  --max-instances=10 \
  --concurrency=1000 \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=$PROJECT_ID" \
  --port=8080

end_time=$(date +%s)
execution_time=$((end_time - start_time))

echo -e "\n=== 部署完成 ==="
date || true  # 非關鍵命令，失敗時不退出
echo "總執行時間: $execution_time 秒"

SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
  --region="$REGION" \
  --project="$PROJECT_ID" \
  --format="value(status.url)") || true  # 容忍查詢失敗

echo -e "\n服務已部署，可通過以下URL訪問："
echo "$SERVICE_URL"

echo -e "\n\n之後要嘗試修改加速"
