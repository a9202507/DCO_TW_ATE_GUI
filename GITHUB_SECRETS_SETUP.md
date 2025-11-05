# GitHub Secrets 設置指南 20251105

## 📍 找到 Secrets 設置位置

### 步驟 1: 進入倉庫 Settings

1. 打開您的 GitHub 倉庫頁面
2. 點擊右上角的 **"Settings"** 標籤

### 步驟 2: 找到 Secrets 選項

1. 在左側選單中向下滾動
2. 找到 **"Secrets and variables"** 部分
3. 點擊 **"Actions"**

### 步驟 3: 添加新的 Secret

1. 點擊綠色的 **"New repository secret"** 按鈕

---

## 🔐 添加 Docker Hub 憑證

### Secret 1: DOCKERHUB_USERNAME

```
Name: DOCKERHUB_USERNAME
Value: a9202507
```

### Secret 2: DOCKERHUB_TOKEN

```
Name: DOCKERHUB_TOKEN
Value: [您的 Docker Hub Access Token]
```

---

## 📸 視覺化步驟

```
GitHub 倉庫頁面
├── Settings (右上角)
│   ├── Secrets and variables (左側選單)
│   │   ├── Actions
│   │   │   ├── New repository secret (綠色按鈕)
│   │   │   │   ├── Name: DOCKERHUB_USERNAME
│   │   │   │   └── Value: a9202507
│   │   │   └── New repository secret (再按一次)
│   │   │       ├── Name: DOCKERHUB_TOKEN
│   │   │       └── Value: [您的 token]
```

---

## ✅ 驗證設置

添加完 secrets 後：

1. **推送測試代碼**：

   ```bash
   git add .
   git commit -m "Test Docker automation"
   git push origin master
   ```

2. **檢查 Actions**：

   - 前往倉庫的 "Actions" 標籤
   - 查看是否有新的 workflow 運行
   - 如果成功，會看到 Docker 鏡像被推送

3. **檢查 Docker Hub**：
   - 前往您的 Docker Hub 倉庫
   - 查看是否有新的鏡像標籤

---

## 🆘 如果找不到選項

如果您在倉庫中沒有看到 "Settings"：

1. **檢查權限**：確保您是倉庫的 Owner 或 Admin
2. **檢查組織**：如果是組織倉庫，可能需要組織管理員權限
3. **聯繫管理員**：請倉庫管理員幫您添加 secrets

---

## 🔍 常見問題

**Q: 為什麼沒有 "Secrets and variables" 選項？**
A: 確保您有倉庫的寫入權限，或者聯繫倉庫管理員。

**Q: 添加了 secrets 但 workflow 還是失敗？**
A: 檢查 secret 名稱是否正確（區分大小寫）。

**Q: Token 忘記了怎麼辦？**
A: 可以重新生成新的 Access Token 替換舊的。
