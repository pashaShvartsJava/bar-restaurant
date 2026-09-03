FROM python:3.12-slim
LABEL authors="ctrad"

WORKDIR /admin_service
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt
COPY . .

EXPOSE 8000

CMD ["uvicorn", "admin_service.main:app", "--host", "0.0.0.0", "--port", "8002", "--reload"]