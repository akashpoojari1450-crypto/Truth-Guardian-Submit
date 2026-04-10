FROM python:3.10-slim
WORKDIR /app
COPY inference.py .
RUN pip install openai --no-cache-dir
EXPOSE 7860
CMD ["python3", "inference.py"]
