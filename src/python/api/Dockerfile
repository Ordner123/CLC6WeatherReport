FROM python:3.11-slim

WORKDIR /app

COPY ReportApi.py MetarTaf.py api/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

CMD ["uvicorn", "ReportApi:app", "--host", "0.0.0.0", "--port", "8000"]