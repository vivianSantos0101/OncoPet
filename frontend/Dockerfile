# 1) Gera os arquivos do site (npm run build)
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

# 2) Caddy serve o site, faz o HTTPS e repassa /api para o backend
FROM caddy:2-alpine
COPY --from=build /app/dist /srv
