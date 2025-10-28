# ATE 儀器控制系統 GUI

本專案提供了一個基於 Web 的圖形化使用者介面 (GUI)，用於控制各種自動化測試設備 (ATE) 儀器。

![ATE GUI](readme_image/ate_gui.png)

## 核心功能 (Features)

- **🔗 遠端控制**: 透過現代化網頁介面遠端操作多種 GPIB 儀器
- **🎛️ 多儀器支援**: 目前支援四種主要儀器類型，每種都有獨立的控制面板：

  - **⚡ 電源供應器 (Power Supply)**: Chroma 62012P
    - 開啟/關閉輸出電源
    - 設定輸出電壓和電流
    - 即時顯示輸出狀態、電壓、電流
  - **🔋 電子負載 (Electronic Load)**: Chroma 63206A
    - 開啟/關閉負載
    - 設定負載電流
    - 即時顯示負載狀態和電流
  - **� 數據採集器 (DAQ)**: HP 34970A
    - 多通道數據讀取
    - 支持電壓、電阻、溫度等多種單位
    - 動態添加監控通道
  - **📉 示波器 (Oscilloscope)**: 框架已建立，等待具體儀器實現

- **🔍 智慧儀器偵測**: 自動掃描所有連接的 GPIB 儀器，智能識別儀器類型並更新到對應控制面板
- **🌐 多客戶端支援**: 服務器可同時處理多個客戶端的連接請求
- **📱 現代化 UI**: 採用響應式深色主題設計，在桌面和移動設備上均有良好體驗
- **🔄 實時狀態監控**: 即時檢查客戶端連接狀態，確保系統運作正常
- **🏢 企業級架構**: 採用工廠模式和抽象層設計，易於擴展支援更多儀器品牌

## 系統架構 (System Architecture)

本系統採用 **客戶端-服務器 (Client-Server)** 分離架構設計：

### 1. 服務器端 (Server - `server/app_server.py`)

- **技術棧**: FastAPI + Uvicorn
- **功能**:
  - 提供現代化 Web UI 界面
  - 處理來自瀏覽器的控制請求
  - 將指令轉發給對應的客戶端
  - 實時檢查客戶端連接狀態
  - 支持多客戶端同時連接

### 2. 客戶端 (Client - `client/app_client.py`)

- **技術棧**: FastAPI + PyVISA + 工廠模式
- **功能**:
  - 直接與 GPIB 硬體儀器通信
  - 執行服務器轉發的控制指令
  - 自動掃描和識別連接的儀器
  - 實現儀器抽象層，支持多品牌儀器

### 3. 儀器抽象層 (Instrument Abstraction Layer)

- **設計模式**: 工廠模式 + 抽象基類
- **優勢**:
  - 統一的儀器控制介面
  - 易於添加新儀器支援
  - 隔離硬體差異

## 專案結構 (Project Structure)

```
DCO_TW_ATE_GUI/
├── server/                    # 服務器端代碼
│   ├── app_server.py         # FastAPI 服務器主程式
│   ├── main.py               # 服務器啟動腳本
│   ├── templates/
│   │   └── index.html        # 主頁面模板
│   └── static/
│       ├── css/
│       │   └── styles.css    # UI 樣式表
│       ├── js/
│       │   ├── app.js        # 前端邏輯
│       │   └── loader.js     # 元件載入器
│       ├── components/       # UI 元件
│       │   ├── _panel_power_supply.html
│       │   ├── _panel_eload.html
│       │   ├── _panel_daq.html
│       │   └── _panel_scope.html
│       └── image/
│           └── logo.png      # 系統 Logo
├── client/                    # 客戶端代碼
│   ├── app_client.py          # FastAPI 客戶端主程式
│   └── instruments/           # 儀器實現
│       ├── power_supply_chroma_62012p.py
│       ├── eload_chroma_63206a.py
│       ├── daq_hp_34970a.py
│       ├── *_factory.py       # 工廠類
│       └── *_interface.py     # 抽象介面
├── openspec/                  # OpenSpec 規範文件
├── AGENTS.md                  # AI 助手開發記錄
└── README.md                  # 本文件
```

## 環境需求 (Requirements)

- **Python**: 3.12+
- **套件管理器**: uv
- **儀器介面**: GPIB (透過 NI VISA 或類似驅動)
- **作業系統**: Windows/Linux/macOS

## 安裝與使用 (Installation & Usage)

### 環境準備

```bash
# 安裝 uv 套件管理器 (如果尚未安裝)
# 請參考 https://github.com/astral-sh/uv
```

### 啟動系統

#### 步驟 1: 啟動服務器

```bash
cd server
uv run app_server.py
```

服務器將運行在 `http://localhost:8000`

#### 步驟 2: 啟動客戶端

```bash
cd client
uv run app_client.py
```

客戶端將連接服務器並開始監聽控制指令

#### 步驟 3: 開啟 Web 界面

- 在瀏覽器中訪問 `http://localhost:8000`
- 確認連接狀態顯示 "已連線"
- 點擊 **"🔍 偵測所有儀器"** 按鈕
- 在儀器列表中選擇要控制的儀器
- 開始使用各儀器面板進行控制

## 儀器控制詳解 (Instrument Control Details)

### 電源供應器 (Chroma 62012P)

- **連接地址**: GPIB0::6::INSTR
- **支援功能**:
  - 電源開關控制
  - 電壓設定 (0-100V)
  - 電流設定 (0-50A)
  - 實時狀態監控

### 電子負載 (Chroma 63206A)

- **連接地址**: GPIB0::7::INSTR
- **支援功能**:
  - 負載開關控制
  - 電流設定 (CC 模式)
  - 實時狀態監控

### 數據採集器 (HP 34970A)

- **連接地址**: GPIB0::10::INSTR
- **支援功能**:
  - 多通道數據讀取
  - 單位選擇 (V/Ω/°C)
  - 動態通道管理

## 前端架構 (Frontend Architecture)

採用 **元件化設計**，提高程式碼可維護性和重用性：

- **主頁面** (`index.html`): 應用外殼，包含基本佈局
- **動態載入**: `loader.js` 自動載入各儀器面板元件
- **響應式設計**: 自適應不同屏幕尺寸
- **深色主題**: 現代化 UI 設計

## 開發與擴展 (Development & Extension)

### 添加新儀器支援

1. 在 `client/instruments/` 建立新的儀器類
2. 實現對應的抽象介面
3. 更新工廠類註冊新儀器
4. 在前端添加對應的控制面板

### API 介面

- **GET** `/api/my-status`: 獲取客戶端狀態
- **POST** `/api/detect`: 偵測可用儀器
- **POST** `/api/control`: 發送控制指令
- **GET** `/api/status`: 獲取儀器狀態

## 故障排除 (Troubleshooting)

### 常見問題

1. **連接狀態顯示 "連線錯誤"**

   - 確認客戶端程序 (`app_client.py`) 已啟動
   - 檢查防火牆設定 (允許 8001 端口)
   - 確認網路連接正常

2. **儀器偵測失敗**

   - 確認 GPIB 驅動已正確安裝
   - 檢查儀器電源和連接線
   - 確認儀器地址設定正確

3. **控制指令無回應**
   - 檢查儀器是否被其他程序占用
   - 確認儀器處於遠端控制模式
   - 查看客戶端日誌輸出

## 版本歷史 (Version History)

- **v2.0.0**: 重構架構，添加多儀器支援，實現工廠模式
- **v1.0.0**: 初始版本，基本儀器控制功能

## 授權與貢獻 (License & Contributing)

本專案採用 MIT 授權。歡迎提交 Issue 和 Pull Request 來改進系統功能。

---

**注意**: 本 README.md 文件作為專案需求的唯一真實來源。任何功能修改或新增需求，請先更新此文件。
