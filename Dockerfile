FROM python:3.12.10-slim-bookworm
WORKDIR /project
COPY requirements.txt requirements.lock ./
RUN pip install --no-cache-dir -r requirements.lock
RUN useradd --create-home --uid 10001 iot
COPY app app
COPY dashboard dashboard
COPY scripts scripts
COPY tests tests
COPY requirements-dev.txt .
USER iot
ENV PYTHONUNBUFFERED=1
CMD ["uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8000"]
