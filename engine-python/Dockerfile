FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml README.md ./
COPY ragforge_engine ./ragforge_engine
RUN pip install --no-cache-dir ".[server]"
EXPOSE 8000
CMD ["uvicorn", "ragforge_engine.service:app", "--host", "0.0.0.0", "--port", "8000"]
