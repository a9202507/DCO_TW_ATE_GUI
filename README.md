# ATE Control System GUI

This project provides a web-based Graphical User Interface (GUI) for controlling various Automated Test Equipment (ATE) instruments.

![ATE GUI](readme_image/ate_gui.png)

## 核心功能 (Features)

- **遠端控制**: 透過網頁介面遠端操作多種 GPIB 儀器。
- **多儀器面板**: 為四種主要儀器類型提供獨立的控制面板，並以虛擬化儀器層來支援不同廠牌的同功能儀器：
  - **⚡ Power Supply**: 開啟/關閉輸出電源、設定輸出電壓，設定輸出電流，並即時回報目前儀器狀態(輸出中/輸出電壓/輸出電流)
  - **🔋 Electronic Load**: 開啟/關閉負載、設定輸出電流值，並即時回報目前儀器狀態(負載中/輸出電流)
  - **📈 DAQ**: 讀取指定通道的數據，並設定該通道讀取的單位(電壓/阻抭/溫度)，且允許使用者增加監控的通道。
  - **📉 Oscilloscope**: 執行/停止、設定觸發、儲存波形並投放到 UI 上，
  -
- **儀器自動偵測**: 自動掃描並列出所有已連接的 GPIB 儀器，將可以儀器清單更新回到各儀器面板，方便使用者在該面板下拉選單中選擇儀器。

- **多客戶端支援**: 伺服器可以同時處理來自多個客戶端的連線請求。
- **現代化 UI**: 採用響應式的深色主題介面，在不同裝置上都有良好的體驗。

## 系統架構 (System Architecture)

本系統採用 Client-Server 架構：

1.  **伺服器 (Server - `server/app_server.py`)**

    - 使用 **FastAPI** 建立的 Python 後端。
    - 提供前端網頁介面 (HTML/CSS/JS)。
    - 負責接收來自網頁的控制指令，並將其轉發給對應的客戶端。

2.  **客戶端 (Client - `client/app_client.py`)**
    - 一個在本地端運行的 Python 程式。
    - 直接與硬體儀器溝通，執行從伺服器收到的指令。
    - 負責儀器掃描和實際的硬體操作。

## 如何使用 (How to Run)

請確保您的環境中已安裝 `uv` 套件管理器。

1.  **啟動伺服器 (Start the Server)**

    - 在專案的 `server` 目錄下，執行以下指令來安裝依賴套件並啟動伺服器：
      ```shell
      # cd server
      uv run app_server.py
      ```
    - 伺服器將運行在 `http://localhost:8000`。

2.  **啟動客戶端 (Start the Client)**

    - 在專案的 `client` 目錄下，執行以下指令來安裝依賴套件並啟動客戶端：
      ```shell
      # cd client
      uv run app_client.py
      ```
    - 客戶端啟動後，會等待來自伺服器的指令。

3.  **開啟網頁介面**
    - 在瀏覽器中開啟 `http://localhost:8000`。
    - 您將看到儀器控制面板。
    - 點擊 **「偵測所有儀器」** 按鈕，下方會出現偵測到的儀器列表。
    - 點擊儀器項目旁的 **「複製位址」** 按鈕，然後將位址貼到對應儀器面板的「儀器位址」輸入框中。
    - 現在您可以開始使用面板上的按鈕來控制您的儀器。

# 前端架構 (Frontend Architecture)

為了提高程式碼的可維護性和模組化程度，前端介面採用元件化的方式建構。每個儀器的控制面板都是一個獨立的 HTML 檔案，由主頁面動態載入。

**檔案結構:**

主要的 UI 檔案位於 `server/` 目錄中，其結構如下：

```
server/
├── static/
│   ├── components/         # 儀器面板元件
│   │   ├── _panel_power_supply.html
│   │   ├── _panel_eload.html
│   │   ├── _panel_daq.html
│   │   └── _panel_scope.html
│   ├── js/
│   │   ├── app.js          # 主應用程式邏輯
│   │   └── loader.js       # 負責動態載入元件的腳本
│   └── css/
│       └── styles.css      # 主要樣式表
└── templates/
    └── index.html          # 主應用程式外殼 (Main application shell)
```

**運作方式:**

1.  瀏覽器載入 `index.html`，這是一個只包含基本佈局和容器的「外殼」頁面。
2.  `loader.js` 腳本會執行，它會自動從 `/static/components/` 路徑抓取所有 `_panel_*.html` 元件。
3.  腳本將這些元件的內容注入到 `index.html` 的主網格佈局中，從而動態生成完整的控制介面。

## 未來開發 (Future Development)

本 `README.md` 文件將作為專案需求的唯一真實來源 (single source of truth)。未來的任何功能修改或新增需求，都請先更新此文件，我將會根據此文件的內容來進行後續的開發。
