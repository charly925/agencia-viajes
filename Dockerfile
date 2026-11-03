# Receta de la "caja" que corre la app de la agencia
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py schema.sql ./
COPY templates templates
EXPOSE 5000
CMD ["python", "app.py"]
