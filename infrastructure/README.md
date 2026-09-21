# Infraestructura de despliegue

Recursos para levantar dependencias externas del sistema.

- `database/postgresql/`: SQL inicial, utilidades de conexión y preparación de pruebas.

La configuración de servicios se orquesta desde `../docker-compose.yml`. El
código Python de acceso a datos permanece dentro del backend porque es un
adaptador de la aplicación, en `backend/src/infrastructure/database/`.

Se conserva el nombre `infrastructure/` para no romper los volúmenes, scripts y
rutas de Docker existentes. Esta carpeta equivale a la capa operativa o
`deploy`; no contiene reglas de negocio ni una segunda implementación del
backend.
