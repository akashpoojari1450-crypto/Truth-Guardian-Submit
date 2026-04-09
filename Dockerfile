FROM python:3.10-slim
WORKDIR /app
COPY . .
RUN pip install fastapi uvicorn --no-cache-dir
EXPOSE 7860
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
