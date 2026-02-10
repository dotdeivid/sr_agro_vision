# SR Agro Vision - Backend API

Backend FastAPI para SR Agro Vision.

## Instalación

```bash
cd backend
pip install -r requirements.txt
```

## Configuración

```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

## Ejecutar

```bash
uvicorn app.main:app --reload --port 8000
```

## Documentación

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Endpoints

### Auth
- POST /api/v1/auth/register - Registrar usuario
- POST /api/v1/auth/login - Login

### Users
- GET /api/v1/users/me - Info usuario actual

### Images
- POST /api/v1/images/upload - Subir imagen
- GET /api/v1/images/ - Listar imágenes
- GET /api/v1/images/{id} - Ver imagen
