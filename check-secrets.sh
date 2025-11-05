#!/bin/bash

# GitHub Secrets 檢查腳本
# 用法: ./check-secrets.sh

echo "🔍 檢查 GitHub Secrets 設置..."
echo "================================="

# 檢查是否在正確的目錄
if [ ! -f ".github/workflows/docker-build.yml" ]; then
    echo "❌ 錯誤：請在專案根目錄運行此腳本"
    exit 1
fi

echo "✅ 找到 GitHub Actions workflow 文件"

# 檢查 workflow 文件中的 secrets 引用
echo ""
echo "📋 Workflow 中引用的 secrets："
grep -n "secrets\." .github/workflows/docker-build.yml

echo ""
echo "📝 請確認以下 secrets 已正確設置："
echo ""
echo "1. DOCKERHUB_USERNAME"
echo "   - 值應該是：a9202507"
echo ""
echo "2. DOCKERHUB_TOKEN"
echo "   - 值應該是您的 Docker Hub Access Token"
echo "   - 長度應該是 64 個字符"
echo ""

echo "🔗 GitHub Secrets 設置位置："
echo "https://github.com/a9202507/DCO_TW_ATE_GUI/settings/secrets/actions"
echo ""

echo "💡 常見問題："
echo "1. 確保 secret 名稱完全匹配（區分大小寫）"
echo "2. 確保 secret 值不包含多餘的空格"
echo "3. 確保您有倉庫的管理權限"
echo ""

echo "🧪 測試方法："
echo "1. 推送一個小變更到 master 分支"
echo "2. 前往 Actions 標籤查看 workflow 運行狀態"
echo "3. 如果還是失敗，請檢查 Actions 的詳細日誌"