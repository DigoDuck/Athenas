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
# Compose defaults; the host overrides both (docs/hosting.md).
ENV PORT=80 BACKEND_URL=http://backend:8000
# The image then exports NGINX_LOCAL_RESOLVERS from /etc/resolv.conf for the template.
ENV NGINX_ENTRYPOINT_LOCAL_RESOLVERS=1
COPY nginx.conf /etc/nginx/templates/default.conf.template
COPY --from=build /app/dist /usr/share/nginx/html
