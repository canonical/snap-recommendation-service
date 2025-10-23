# --- Build frontend ---
FROM node:22-alpine AS frontend
WORKDIR /frontend

COPY frontend/package.json frontend/yarn.lock* ./
RUN yarn install

COPY frontend/ ./
RUN yarn build


# --- Build backend ---
FROM python:3.11-alpine 

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . . 
COPY --from=frontend /frontend/dist/static/ ./snaprecommend/static/
COPY --from=frontend /frontend/dist/index.html ./snaprecommend/templates/index.html

# ENTRYPOINT ["./entrypoint.sh"]
CMD ["flask", "run", "--host=0.0.0.0", "--port=80"]
