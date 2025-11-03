# 使用 Python 3.12 作為基礎映像
FROM python:3.12-slim

# 設置工作目錄
WORKDIR /app

# 設置環境變數
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 複製依賴文件
COPY pyproject.toml ./

# 安裝依賴
RUN pip install --no-cache-dir fastapi==0.119.1 \
    httpx==0.28.1 \
    jinja2==3.1.6 \
    uvicorn==0.38.0

# 複製應用程式代碼
COPY app_server.py ./
COPY templates/ ./templates/
COPY static/ ./static/

# 暴露端口
EXPOSE 8000

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/my-status')" || exit 1

# 啟動命令
CMD ["python", "-m", "uvicorn", "app_server:app", "--host", "0.0.0.0", "--port", "8000"]
