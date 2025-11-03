#!/bin/bash

# 設定嚴格模式，遇到錯誤立即停止執行
set -e

# 顯示當前目錄文件（用於調試）
echo -e "\n=== 當前目錄文件列表 ==="
ls -latr

# 服務配置
SERVICE_NAME='cmb-caller-frontend'
REGION="asia-east1"
PROJECT_ID='callme-op-419108'   # Trial
#PROJECT_ID='callme-398802'    # Release
IMAGE_NAME="gcr.io/${PROJECT_ID}/cmb-caller-frontend:latest"

# 記錄開始時間
echo -e "\n=== 部署開始 ==="
start_time=$(date +%s)
date

# 準備Dockerfile
echo -e "\n=== 準備Dockerfile ==="
cp -a Dockerfile.trial Dockerfile
file -i cmb-caller-frontend_trial.py requirements.txt Dockerfile

# 設置Pub/Sub（僅在首次部署時需要）
echo -e "\n=== 設置Pub/Sub ==="
if ! gcloud pubsub topics describe cross-instance-comms --project="$PROJECT_ID" 2>/dev/null; then
    gcloud pubsub topics create cross-instance-comms --project="$PROJECT_ID"
fi

if ! gcloud pubsub subscriptions describe version-sub --project="$PROJECT_ID" 2>/dev/null; then
    gcloud pubsub subscriptions create version-sub \
        --topic=cross-instance-comms \
        --project="$PROJECT_ID"
fi

# 構建並推送Docker映像
echo -e "\n=== 構建Docker映像 ==="
gcloud builds submit --tag "$IMAGE_NAME" --project="$PROJECT_ID"

# 部署服務
echo -e "\n=== 部署Cloud Run服務 ==="
date

DEPLOY_TIMESTAMP=$(date +%s)

# gcloud beta run deploy "$SERVICE_NAME" \
  # --source . \
  # --region "$REGION" \
  # --project "$PROJECT_ID" \
  # --memory 2Gi \
  # --cpu 1 \
  # --execution-environment gen2 \
  # --timeout=600 \
  # --service-min-instances=0 \
  # --concurrency=1000 \
  # --max-instances=1 \
  # --set-env-vars DEPLOY_TIMESTAMP=$DEPLOY_TIMESTAMP
  


# gcloud run deploy "$SERVICE_NAME" \
gcloud beta run deploy "$SERVICE_NAME" \
  --image="$IMAGE_NAME" \
  --region="$REGION" \
  --project="$PROJECT_ID" \
  --platform=managed \
  --allow-unauthenticated \
  --memory=2Gi \
  --cpu=1 \
  --execution-environment=gen2 \
  --timeout=600 \
  --service-min-instances=1 \
  --concurrency=1000 \
  --max-instances=1 \
  --set-env-vars="DEPLOY_TIMESTAMP=$DEPLOY_TIMESTAMP,GOOGLE_CLOUD_PROJECT=$PROJECT_ID" \
  --port=8080

# 恢復原始Dockerfile
echo -e "\n=== 恢復Dockerfile ==="
cp -a Dockerfile.live Dockerfile

# 獲取並切換流量到最新版本
# echo -e "\n=== 流量切換 ==="
# LATEST_REVISION=$(gcloud run revisions list \
  # --service="$SERVICE_NAME" \
  # --region="$REGION" \
  # --project="$PROJECT_ID" \
  # --sort-by="~creationTimestamp" \
  # --limit=1 \
  # --format="value(metadata.name)")

# echo "最新修訂版本為：$LATEST_REVISION"

# gcloud run services update-traffic "$SERVICE_NAME" \
  # --to-revisions="$LATEST_REVISION=100" \
  # --region="$REGION" \
  # --project="$PROJECT_ID"

# 計算並顯示執行時間
end_time=$(date +%s)
execution_time=$((end_time - start_time))

echo -e "\n=== 部署完成 ==="
date
echo "總執行時間: $execution_time 秒"

# 顯示服務URL
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
  --region="$REGION" \
  --project="$PROJECT_ID" \
  --format="value(status.url)")

echo -e "\n服務已部署，可通過以下URL訪問："
echo "$SERVICE_URL"