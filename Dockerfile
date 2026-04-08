FROM python:3.10

WORKDIR /app

COPY . /app

RUN pip install --upgrade pip

RUN pip install -e .

EXPOSE 7860

CMD ["python", "-m", "uvicorn", "inference:app", "--host", "0.0.0.0", "--port", "7860"]
