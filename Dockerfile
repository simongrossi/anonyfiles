FROM python:3.11-slim

WORKDIR /app

COPY . /app

RUN python3 -m ensurepip --upgrade && \
    python3 -m pip install --upgrade pip setuptools wheel && \
    sed -i '/-e \./d' requirements.txt && \
    pip install . && \
    pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["uvicorn", "anonyfiles_api.api:app", "--host", "0.0.0.0", "--port", "8000"]
