FROM python:3.10-slim
WORKDIR /app
COPY app.py .
RUN pip install fastapi uvicorn --no-cache-dir
EXPOSE 7860
CMD ["python", "app.py"]
