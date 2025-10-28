let clientInfo = {};
let isDetecting = false;
const instrumentTypes = ["power-supply", "eload", "daq", "scope"];
const pollingIntervals = {};
let daqChannelCount = 1;

// --- STATUS & DISPLAY FUNCTIONS ---

function showStatus(panelId, message, type) {
  const statusDiv = document.getElementById(`status-${panelId}`);
  if (statusDiv) {
    statusDiv.innerHTML = `<div class="status ${type}">${message}</div>`;
    if (type === "success" || type === "info") {
      setTimeout(() => {
        if (statusDiv.innerHTML.includes(message)) statusDiv.innerHTML = "";
      }, 5000);
    }
  }
}

function showGlobalStatus(message, type) {
  const statusDiv = document.getElementById("global-status");
  if (statusDiv) {
    statusDiv.innerHTML = `<div class="status ${type}">${message}</div>`;
    if (type === "success" || type === "info") {
      setTimeout(() => {
        if (statusDiv.innerHTML.includes(message)) statusDiv.innerHTML = "";
      }, 5000);
    }
  }
}

function updateStatusDisplay(instrumentType, data) {
  const displayDiv = document.getElementById(
    `status-display-${instrumentType}`
  );
  if (!displayDiv) return;

  let html = "";
  if (instrumentType === "power-supply") {
    html = `
            <div class="status-item"><span class="status-label">State</span><span class="status-value">${
              data.output || "N/A"
            }</span></div>
            <div class="status-item"><span class="status-label">Voltage</span><span class="status-value">${
              data.voltage || "0.00"
            } V</span></div>
            <div class="status-item"><span class="status-label">Current</span><span class="status-value">${
              data.current || "0.00"
            } A</span></div>
        `;
  } else if (instrumentType === "eload") {
    html = `
            <div class="status-item"><span class="status-label">State</span><span class="status-value">${
              data.output || "N/A"
            }</span></div>
            <div class="status-item"><span class="status-label">Current</span><span class="status-value">${
              data.current || "0.00"
            } A</span></div>
        `;
  }
  displayDiv.innerHTML = html;
}

// --- CORE API FUNCTIONS ---

async function checkClientStatus() {
  try {
    const response = await fetch("/api/my-status");
    clientInfo = await response.json();
    document.getElementById("clientIP").textContent = clientInfo.ip || "未知";
    document.getElementById("sessionID").textContent =
      clientInfo.session_id || "未知";
    document.getElementById("connectionStatus").textContent =
      clientInfo.status === "connected" ? "已連線" : "連線錯誤";
    document.getElementById("instrumentCount").textContent =
      clientInfo.instruments?.length || 0;
  } catch (error) {
    document.getElementById("connectionStatus").textContent = "連線錯誤";
  }
}

async function detectInstruments() {
  if (isDetecting) return;
  isDetecting = true;
  const detectBtn = document.querySelector(".btn-detection");
  detectBtn.disabled = true;
  showGlobalStatus("正在掃描您的 GPIB 儀器...", "info");

  try {
    const response = await fetch("/api/detect", { method: "POST" });
    const result = await response.json();
    if (response.ok && result.success) {
      displayInstruments(result.instruments);
      showGlobalStatus(
        `✅ 成功偵測到 ${result.instruments.length} 個儀器`,
        "success"
      );
      await checkClientStatus();
    } else {
      showGlobalStatus(`❌ 偵測失敗: ${result.detail || "未知錯誤"}`, "error");
    }
  } catch (error) {
    showGlobalStatus(`❌ 偵測時發生網路錯誤`, "error");
  } finally {
    isDetecting = false;
    detectBtn.disabled = false;
  }
}

async function controlInstrument(instrumentType, action) {
    console.log(`controlInstrument called with: ${instrumentType}, ${action}`);
    const addressSelect = document.getElementById(`address-${instrumentType}`);  const address = addressSelect.value;

  if (!address) {
    showStatus(instrumentType, "❌ 請先選擇一個儀器位址", "error");
    return;
  }

  const payload = { instrument_type: instrumentType, address, action };

  // --- Payload assembly for specific actions ---
  const valueActions = {
    set_voltage: "value-power-supply-voltage",
    set_current: "value-power-supply-current", // For Power Supply
  };
  if (action === "set_current" && instrumentType === "eload") {
    valueActions.set_current = "value-eload-current"; // For E-Load
  }
  if (action === "set_trigger") {
    valueActions.set_trigger = "value-scope-trigger";
  }

  if (action in valueActions) {
    payload.value = document.getElementById(valueActions[action]).value;
  }

  if (instrumentType === "daq" && action === "read") {
    payload.value = [];
    document.querySelectorAll(".daq-channel-row").forEach((row) => {
      const channel = row.querySelector('input[type="text"]').value;
      const unit = row.querySelector("select").value;
      if (channel) payload.value.push({ channel, unit });
    });
  }

  console.log("Sending payload:", JSON.stringify(payload, null, 2));
  showStatus(instrumentType, `⚙️ 正在執行 ${action}...`, "info");
  const panel = document.getElementById(`panel-${instrumentType}`);
  panel.querySelectorAll("button").forEach((b) => (b.disabled = true));

  try {
    const response = await fetch("/api/control", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const result = await response.json();

    if (response.ok && result.success) {
      showStatus(instrumentType, `✅ 操作成功`, "success");
      if (instrumentType === "daq" && action === "read") {
        updateDaqResults(result.results);
      }
      if (action === "get_waveform") {
        plotWaveform(instrumentType, result.data);
      }
    } else {
      showStatus(
        instrumentType,
        `❌ 操作失敗: ${result.detail || result.message}`,
        "error"
      );
    }
  } catch (error) {
    showStatus(instrumentType, `❌ 操作時發生網路錯誤`, "error");
  } finally {
    setTimeout(() => {
      panel
        .querySelectorAll("button")
        .forEach((b) => (b.disabled = address === ""));
    }, 1000);
  }
}

// --- INSTRUMENT SPECIFIC LOGIC ---

function updateDaqResults(results) {
  const rows = document.querySelectorAll(".daq-channel-row");
  rows.forEach((row) => {
    const channelInput = row.querySelector('input[type="text"]');
    const channel = channelInput.value;
    const resultSpan = row.querySelector(".daq-result");
    const unitSelect = row.querySelector("select");
    const unit = unitSelect.options[unitSelect.selectedIndex].text
      .split("(")[1]
      .replace(")", "");

    if (channel && results.hasOwnProperty(channel) && resultSpan) {
      const value = results[channel];
      if (typeof value === "number" && !isNaN(value)) {
        resultSpan.textContent = `${value.toFixed(4)} ${unit}`;
        resultSpan.classList.remove("error");
      } else {
        resultSpan.textContent = "讀取失敗";
        resultSpan.classList.add("error");
      }
    } else if (channel && resultSpan) {
      // If channel was in the request but not in the result
      resultSpan.textContent = "無回傳值";
      resultSpan.classList.add("error");
    }
  });
}

function addDaqChannel() {
  daqChannelCount++;
  const container = document.getElementById("daq-channels-container");
  const newChannel = document.createElement("div");
  newChannel.className = "panel-controls daq-channel-row";
  newChannel.innerHTML = `
        <div class="form-group">
            <label for="value-daq-channels-${daqChannelCount}">通道 ${daqChannelCount}</label>
            <input type="text" id="value-daq-channels-${daqChannelCount}" placeholder="e.g., 102">
        </div>
        <div class="form-group">
            <label for="value-daq-unit-${daqChannelCount}">單位</label>
            <select id="value-daq-unit-${daqChannelCount}">
                <option value="VOLT">電壓 (V)</option>
                <option value="RES">電阻 (Ω)</option>
                <option value="TEMP">溫度 (°C)</option>
            </select>
        </div>
        <div class="form-group result-group">
            <label>讀值</label>
            <span class="daq-result">-.-- V</span>
        </div>
    `;
  container.appendChild(newChannel);
}

function plotWaveform(instrumentType, data) {
  const container = document.getElementById(`waveform-${instrumentType}`);
  if (!container) return;

  if (!data || !data.x || !data.y) {
    container.innerHTML =
      '<p style="color: red; text-align: center;">無效的波形資料</p>';
    return;
  }

  Plotly.newPlot(
    container,
    [
      {
        x: data.x,
        y: data.y,
        type: "scatter",
        mode: "lines",
        marker: { color: "#03dac6" },
      },
    ],
    {
      margin: { t: 20, l: 40, r: 20, b: 40 },
      paper_bgcolor: "#1e1e1e",
      plot_bgcolor: "#1e1e1e",
      font: { color: "#e0e0e0" },
      xaxis: { gridcolor: "#444" },
      yaxis: { gridcolor: "#444" },
    }
  );
}

// --- INITIALIZATION ---

function displayInstruments(instruments) {
  const instrumentList = document.getElementById("instrumentsList");
  instrumentList.innerHTML = ""; // Clear old list

  if (!instruments || instruments.length === 0) {
    instrumentList.innerHTML =
      '<div class="no-instruments">未發現任何 GPIB 儀器。</div>';
    return;
  }

  // Populate the global list (for reference)
  instruments.forEach((inst) => {
    const item = document.createElement("div");
    item.className = "instrument-item";
    item.innerHTML = `<div class="instrument-details"><div class="instrument-name">${inst.name}</div><div class="instrument-address">${inst.address}</div></div>`;
    instrumentList.appendChild(item);
  });

  // Populate dropdowns in each panel
  instrumentTypes.forEach((type) => {
    const select = document.getElementById(`address-${type}`);
    select.innerHTML = '<option value="">-- 請選擇儀器 --</option>';
    instruments.forEach((inst) => {
      const option = new Option(`${inst.name} (${inst.address})`, inst.address);
      select.add(option);
    });
    select.disabled = false;
  });
}

function startStatusPolling(instrumentType, address) {
  stopStatusPolling(instrumentType); // Stop any existing polling for this panel
  // TODO: Uncomment when backend /api/status is ready
  /*
    pollingIntervals[instrumentType] = setInterval(async () => {
        try {
            const response = await fetch(`/api/status?instrument_type=${instrumentType}&address=${encodeURIComponent(address)}`);
            if (response.ok) {
                const data = await response.json();
                updateStatusDisplay(instrumentType, data);
            } else {
                // Stop polling on error to prevent spamming
                stopStatusPolling(instrumentType);
            }
        } catch (error) {
            console.error(`Polling error for ${instrumentType}:`, error);
            stopStatusPolling(instrumentType);
        }
    }, 2000); // Poll every 2 seconds
    */
}

function stopStatusPolling(instrumentType) {
  if (pollingIntervals[instrumentType]) {
    clearInterval(pollingIntervals[instrumentType]);
    delete pollingIntervals[instrumentType];
  }
}

function initializePanels() {
  instrumentTypes.forEach((type) => {
    const select = document.getElementById(`address-${type}`);
    const panel = document.getElementById(`panel-${type}`);
    if (select && panel) {
      select.addEventListener("change", () => {
        const hasValue = select.value !== "";
        panel
          .querySelectorAll("button")
          .forEach((b) => (b.disabled = !hasValue));
        if (hasValue) {
          startStatusPolling(type, select.value);
        } else {
          stopStatusPolling(type);
        }
      });
    }
  });

  const addChannelBtn = document.getElementById("add-daq-channel");
  if (addChannelBtn) {
    addChannelBtn.addEventListener("click", addDaqChannel);
  }
}

function initializeApp() {
  initializePanels();
  checkClientStatus();
  setInterval(checkClientStatus, 15000);
  showGlobalStatus("🎉 歡迎使用 ATE 儀器控制系統！", "info");
}
