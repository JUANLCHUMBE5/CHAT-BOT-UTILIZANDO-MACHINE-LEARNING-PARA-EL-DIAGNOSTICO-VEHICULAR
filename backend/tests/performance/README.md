# Pruebas de rendimiento

Las pruebas de carga están separadas de Pytest porque requieren un servidor
activo y credenciales de ensayo.

```powershell
cd backend
..\.venv\Scripts\locust.exe -f tests\performance\locustfile.py --host http://127.0.0.1:8000
```

Nunca deben ejecutarse con credenciales o números reales de producción.

