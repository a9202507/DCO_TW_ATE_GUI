#!/bin/bash

# Docker 鏡像測試腳本
# 用法: ./test-docker.sh [tag]

set -e

# 默認使用 latest 標籤
TAG=${1:-latest}
IMAGE_NAME="docker.io/a9202507/dco-tw-ate-server:$TAG"

echo "🔍 測試 Docker 鏡像: $IMAGE_NAME"
echo "================================="

# 檢查鏡像是否存在
echo "📦 檢查鏡像..."
if ! docker manifest inspect $IMAGE_NAME > /dev/null 2>&1; then
    echo "❌ 鏡像不存在: $IMAGE_NAME"
    echo "請檢查 GitHub Actions 是否成功運行"
    exit 1
fi

echo "✅ 鏡像存在"

# 拉取鏡像
echo "⬇️ 拉取鏡像..."
docker pull $IMAGE_NAME

# 檢查鏡像信息
echo "ℹ️ 鏡像信息:"
docker inspect $IMAGE_NAME --format='Created: {{.Created}}
Size: {{.Size}} bytes
Architecture: {{.Architecture}}
OS: {{.Os}}'

# 測試運行
echo "🚀 測試運行容器..."
CONTAINER_ID=$(docker run -d -p 8000:8000 --name test-ate-server $IMAGE_NAME)

# 等待服務器啟動
echo "⏳ 等待服務器啟動..."
sleep 5

# 測試健康檢查
echo "🏥 測試健康檢查..."
if curl -f http://localhost:8000 > /dev/null 2>&1; then
    echo "✅ 服務器運行正常"
else
    echo "❌ 服務器未響應"
    docker logs $CONTAINER_ID
    docker stop $CONTAINER_ID
    docker rm $CONTAINER_ID
    exit 1
fi

# 清理測試容器
echo "🧹 清理測試容器..."
docker stop $CONTAINER_ID
docker rm $CONTAINER_ID

echo "🎉 所有測試通過！"
echo "鏡像 $IMAGE_NAME 可以正常使用"