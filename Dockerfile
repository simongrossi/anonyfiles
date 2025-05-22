FROM python:3.11-slim

WORKDIR /app

COPY anonyfiles_api/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY anonyfiles_api/ ./anonyfiles_api/

CMD ["uvicorn", "anonyfiles_api.api:app", "--host", "0.0.0.0", "--port", "8000"]
