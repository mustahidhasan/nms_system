# Stage 1: Build
FROM node:20 AS build

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY src ./src
COPY public ./public

ARG ENV_FILE=.env
RUN cp ${ENV_FILE} .env

RUN npm run build

# Stage 2: Production server (nginx)
FROM nginx:stable-alpine AS prod

COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]

# Stage 3: Dev
FROM node:20 AS dev

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY src ./src
COPY public ./public

EXPOSE 3000
CMD ["npm", "start"]
