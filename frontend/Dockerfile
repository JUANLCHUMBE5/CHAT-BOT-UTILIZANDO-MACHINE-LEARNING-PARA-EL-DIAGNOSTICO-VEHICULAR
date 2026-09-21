# Etapa 1: Compilacion de la aplicacion React con Vite
FROM node:20-alpine AS builder

WORKDIR /app

# Instalar dependencias
COPY package.json package-lock.json ./
RUN npm ci

# Copiar codigo fuente y compilar
COPY . .
RUN npm run build

# Etapa 2: Servidor web de produccion ultra liviano con Nginx
FROM nginx:alpine

# Copiar configuracion personalizada de Nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copiar archivos estaticos compilados desde la etapa de builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Exponer el puerto estandar HTTP
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
