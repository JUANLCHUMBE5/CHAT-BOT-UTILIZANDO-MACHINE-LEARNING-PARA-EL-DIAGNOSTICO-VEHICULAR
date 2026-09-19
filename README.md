# CarBot Backend - Motor de Diagnóstico Vehicular y API

Servidor central de **CarBot** desarrollado con **FastAPI**, **PostgreSQL 17**, **Redis**, **Alembic** y procesamiento en segundo plano para webhooks de WhatsApp y panel web de administración.

---

## 🚀 Arquitectura y Componentes

* **API REST:** FastAPI (asíncrono, validación Pydantic v2).
* **Worker en Background:** Procesador de colas para diagnósticos y síntesis LLM.
* **Base de Datos:** PostgreSQL 17 Alpine con migraciones automáticas vía Alembic.
* **Caché y Límites:** Redis 7 Alpine.
* **Motor ML / RAG:** Clasificador Linear SVM con TF-IDF e índice vectorial FAISS embebidos para inferencia en tiempo real (<20 ms).

---

## 🐳 Despliegue con Docker Compose (Recomendado para Servidor)

1. Clonar el repositorio:
   ```bash
   git clone https://github.com/JUANLCHUMBE5/carbot-backend.git
   cd carbot-backend
   ```

2. Configurar el archivo de entorno `.env`:
   ```bash
   cp .env.example .env
   # Editar .env con tus contraseñas y claves de API
   ```

3. Iniciar todos los servicios en segundo plano:
   ```bash
   docker compose up -d --build
   ```

4. Verificar que todos los servicios estén saludables (`healthy`):
   ```bash
   docker compose ps
   ```

5. Ver logs en tiempo real:
   ```bash
   docker compose logs -f api
   docker compose logs -f worker
   ```

La API estará respondiendo en `http://localhost:8000/docs` (documentación Swagger interactiva).

---

## 🛠️ Ejecución Local sin Docker (Desarrollo)

1. Crear y activar entorno virtual:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # En Windows: .venv\Scripts\Activate.ps1
   ```

2. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

3. Aplicar migraciones de base de datos:
   ```bash
   python -m alembic upgrade head
   ```

4. Iniciar API:
   ```bash
   uvicorn main:app --reload --port 8000
   ```
