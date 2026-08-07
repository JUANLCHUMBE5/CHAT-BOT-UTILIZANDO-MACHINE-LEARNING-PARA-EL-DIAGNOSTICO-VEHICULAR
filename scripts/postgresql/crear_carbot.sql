-- Ejecutar una sola vez en pgAdmin conectado como administrador de PostgreSQL.
-- Sustituir la contraseña antes de ejecutar. No usar esta clave de ejemplo.

CREATE ROLE carbot_app
    WITH LOGIN
    NOSUPERUSER
    NOCREATEDB
    NOCREATEROLE
    NOINHERIT
    PASSWORD 'CarBot_App_Sec2026!';

CREATE DATABASE carbot_db
    WITH OWNER = carbot_app
    ENCODING = 'UTF8'
    TEMPLATE = template0;

REVOKE ALL ON DATABASE carbot_db FROM PUBLIC;
GRANT CONNECT, TEMPORARY ON DATABASE carbot_db TO carbot_app;
