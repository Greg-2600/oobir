FROM python:3.9
WORKDIR /oobir
COPY requirements.txt ./
COPY ./src/ ./
COPY . .

RUN pip install --no-cache-dir -r requirements.txt
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]