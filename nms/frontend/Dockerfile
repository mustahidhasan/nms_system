# Stage 1: Build React app
FROM node:20 AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm install

COPY src ./src
COPY public ./public

# Copy .env depending on build context
ARG ENV_FILE
RUN if [ "$ENV_FILE" = "prod" ]; then cp ../.env.prod .env; else cp ../.env.local .env; fi

RUN npm run build

# Stage 2: Serve with nginx (for production)
FROM nginx:stable-alpine AS prod

WORKDIR /usr/share/nginx/html

COPY --from=build /app/build .

# Nginx config for prod
COPY ../nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]

# Stage dev: React dev server
FROM node:20 AS dev
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm install
COPY src ./src
COPY public ./public
EXPOSE 3000
CMD ["npm", "start"]
