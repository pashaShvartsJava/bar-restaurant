FROM python:3.12-slim
LABEL authors="ctrad"

WORKDIR /warehouse_service

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt
COPY . .

EXPOSE 8011

CMD ["uvicorn", "warehouse_service.main:app", "--host", "0.0.0.0", "--port", "8011", "--reload"]