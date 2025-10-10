# Stage 1: build
FROM node:20 AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm install

COPY src ./src
COPY public ./public

ARG ENV_FILE=.env.local
RUN if [ "$ENV_FILE" = ".env.prod" ]; then cp ../.env.prod .env; else cp ../.env.local .env; fi

RUN npm run build

# Stage 2: prod server
FROM nginx:stable-alpine AS prod
WORKDIR /usr/share/nginx/html
COPY --from=build /app/build .
COPY ../nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]

# Stage dev
FROM node:20 AS dev
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm install
COPY src ./src
COPY public ./public
EXPOSE 3000
CMD ["npm", "start"]
