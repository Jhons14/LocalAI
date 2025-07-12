# 🧠 LLM Chat Interface

Una aplicación de código abierto para interactuar fácilmente con modelos de lenguaje (LLM), ya sea en local usando [Ollama](https://ollama.com/) o en la nube a través de OpenAI (ChatGPT) con una API key.

## 🚀 Características

- ✅ Compatible con modelos LLM locales (Ollama)  
- ☁️ Soporte para ChatGPT vía API Key (OpenAI)  
- 🧩 Frontend moderno con React + Vite  
- 🐍 Backend robusto en Python (FastAPI)  
- 🔐 Gestión segura de claves API  
- 💬 Interfaz tipo chat con historial  
- 🎨 UI responsiva y amigable  

## 🧱 Tecnologías

| Parte      | Tecnología                |
|------------|---------------------------|
| Frontend   | React, Vite, Tailwind CSS |
| Backend    | Python, FastAPI           |
| LLM Local  | Ollama                    |
| LLM Nube   | OpenAI (ChatGPT)          |

## 🛠️ Instalación

### 1. Clona el repositorio

```bash
git clone https://github.com/Jhons14/LocalAI.git
cd LocalAI
```

### 2. Configura el backend (Python)

```bash
cd backend
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Crea un archivo `.env` con tus variables necesarias:


Inicia el backend:

```bash
fastapi run --reload
```

### 3. Configura el frontend (React + Vite)

```bash
cd ../frontend
npm install
npm run dev
```

## ⚙️ Configuración

- Puedes alternar entre LLM local y remoto mediante una configuración en el backend.
- El frontend se comunica con el backend mediante endpoints REST para enviar preguntas y recibir respuestas por chunks.

## 📦 Despliegue con Docker

Puedes usar [Docker](https://www.docker.com/) o [Docker Compose](https://docs.docker.com/compose/) para ejecutar toda la app fácilmente:

```bash
docker-compose up --build
```

Asegúrate de tener tus variables de entorno configuradas en los archivos `.env` correspondientes antes de levantar los contenedores.

## 🔒 Seguridad

- La API key de OpenAI **no se expone** en el frontend.
- Agrega restricciones CORS apropiadas para producción.
- Considera usar HTTPS en despliegues reales.

## 🧪 TODO

- [ ] Autenticación de usuario  
- [ ] Guardar historial en base de datos  
- [ ] Soporte para múltiples modelos en tiempo real  
- [ ] Soporte para carga de archivos y análisis de documentos  

## 📄 Licencia

Este proyecto está bajo la licencia MIT.

## ✨ Autor

Desarrollado por [Jhon Steven Orjuela](https://www.jstevenon.com/) — ¡Contribuciones y estrellas son bienvenidas!
