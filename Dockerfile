FROM python:3.11-slim AS base
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

FROM base AS production
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "src.api.server:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
