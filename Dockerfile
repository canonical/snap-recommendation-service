# build frontend
FROM node:22-alpine as frontend-builder
WORKDIR /frontend

COPY frontend/package.json frontend/yarn.lock* ./
RUN yarn install

COPY frontend/ ./

RUN yarn build-prod

# build backend
FROM python:3.11-alpine 

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . . 

CMD ["flask", "run", "--host=0.0.0.0", "--port=80"]
