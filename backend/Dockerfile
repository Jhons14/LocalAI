FROM python:3.13

# 1. Evitar caché de pip y usar sólo lo necesario
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 2. Crear directorio y copiar dependencias
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. Copiar el resto del código
COPY . .

EXPOSE 8000

# 4. Ejecutar servidor en modo producción
CMD ["fastapi", "run", "main.py"]