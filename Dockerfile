FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY mediator ./mediator
COPY gui ./gui
COPY sql ./sql
COPY docs ./docs
CMD ["python", "-m", "uvicorn", "mediator.main:app", "--host", "0.0.0.0", "--port", "8000"]
