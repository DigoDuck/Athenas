# Build context is ./frontend.
FROM node:22-alpine AS dev
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
# Source is bind-mounted at /app/src etc. by docker-compose.dev.yml.
CMD ["npm", "run", "dev"]

FROM dev AS build
COPY . .
RUN npm run build

FROM nginx:alpine AS use
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
