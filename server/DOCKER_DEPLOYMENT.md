# GitHub Actions Docker 自動化部署

## 概述
當您推送代碼到 GitHub 時，GitHub Actions 會自動：
1. 獲取 Git commit hash 作為 Docker 鏡像版本號
2. 構建 Docker 鏡像
3. 推送到 Docker Hub

## 設置步驟

### 1. 創建 Docker Hub Access Token

1. 前往 [Docker Hub](https://hub.docker.com/)
2. 登入您的帳號
3. 點擊右上角頭像 → Account Settings
4. 選擇 "Security" 標籤
5. 點擊 "New Access Token"
6. 輸入 Token 名稱（例如：`github-actions`）
7. 選擇權限（建議選擇 "Read, Write, Delete"）
8. 點擊 "Generate"
9. **複製生成的 Token**（只會顯示一次）

### 2. 添加 GitHub Secrets

1. 前往您的 GitHub 倉庫
2. 點擊 "Settings" 標籤
3. 在左側選單中點擊 "Secrets and variables" → "Actions"
4. 點擊 "New repository secret"
5. 添加以下兩個 secrets：

#### Secret 1: DOCKERHUB_USERNAME
- **Name**: `DOCKERHUB_USERNAME`
- **Value**: 您的 Docker Hub 用戶名（例如：`a9202507`）

#### Secret 2: DOCKERHUB_TOKEN
- **Name**: `DOCKERHUB_TOKEN`
- **Value**: 剛剛生成的 Access Token

### 3. 推送代碼觸發自動化

推送代碼到 `master` 或 `main` 分支時會自動觸發：

```bash
git add .
git commit -m "Add Docker automation"
git push origin master
```

## 鏡像標籤說明

推送後會生成以下標籤的鏡像：

- `latest` - 最新版本（只有推送到默認分支時）
- `master` 或 `main` - 分支名稱
- `master-<commit-hash>` - 分支 + 短 commit hash
- `<full-commit-hash>` - 完整的 commit hash

## 使用示例

```bash
# 拉取最新版本
docker pull docker.io/a9202507/dco-tw-ate-server:latest

# 拉取特定 commit 版本
docker pull docker.io/a9202507/dco-tw-ate-server:abc1234

# 運行容器
docker run -d -p 8000:8000 docker.io/a9202507/dco-tw-ate-server:latest
```

## 故障排除

### 常見問題

1. **"unauthorized: authentication required"**
   - 檢查 `DOCKERHUB_USERNAME` 和 `DOCKERHUB_TOKEN` 是否正確設置

2. **"repository does not exist"**
   - 確保 Docker Hub 上存在對應的倉庫
   - 檢查用戶名拼寫是否正確

3. **Workflow 不觸發**
   - 確保推送的是 `master` 或 `main` 分支
   - 檢查 `server/` 目錄下的文件是否有變更

### 查看 Workflow 日誌

1. 前往 GitHub 倉庫的 "Actions" 標籤
2. 點擊最新的 workflow 運行
3. 查看詳細日誌

## 安全注意事項

- Access Token 只會在生成時顯示一次，請妥善保存
- 定期輪換 Access Token
- 不要將 Token 提交到代碼倉庫中
- 限制 Token 的權限範圍

## 進階配置

如果需要自定義 workflow，可以修改 `.github/workflows/docker-build.yml` 文件：

- 更改觸發條件
- 添加測試步驟
- 修改鏡像標籤策略
- 添加多架構支持