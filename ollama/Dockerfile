# Usa la imagen oficial de Ollama como base
FROM ollama/ollama:latest

# Opcional: configura el puerto interno (11434 por defecto en Ollama)
ENV OLLAMA_HOST 0.0.0.0:11434

# Opcional: define la ruta donde Ollama almacenará los modelos
ENV OLLAMA_MODELS = /models

# Reduce el nivel de logs para no saturar la consola
ENV OLLAMA_DEBUG false

# Indica que Ollama no descarte el modelo de la memoria GPU (si aplica)
ENV OLLAMA_KEEP_ALIVE -1

EXPOSE 11434
# Elimina el ENTRYPOINT por defecto para controlar el arranque manualmente
ENTRYPOINT []

# Comando que arranca Ollama en segundo plano, espera, descarga el modelo y mantiene el proceso vivo
CMD ["sh", "-c", "\
  ollama serve & \
  sleep 5 && \
  ollama pull qwen2.5:3b && \
  wait \
  "]
