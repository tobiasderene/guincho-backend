# Imagen base liviana de Python
FROM python:3.11-slim

# Crear y setear el directorio de trabajo
WORKDIR /app

# Copiar dependencias
COPY requirements.txt .

# Instalar dependencias sin cache para que sea liviano
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto de tu código
COPY . .

# Puerto por defecto para Cloud Run
EXPOSE 8080

# Comando para arrancar uvicorn en el puerto correcto
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]