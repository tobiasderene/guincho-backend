# Imagen base de Python
FROM python:3.10-slim

# Evita que Python genere archivos .pyc
ENV PYTHONDONTWRITEBYTECODE=1
# Fuerza salida más legible de logs
ENV PYTHONUNBUFFERED=1

# Setea el directorio de trabajo
WORKDIR /app

# Copia e instala dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto del código
COPY . .

# Cloud Run expone el puerto 8080
ENV PORT=8080

# Comando para correr FastAPI con Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
