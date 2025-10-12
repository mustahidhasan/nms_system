# Stage 1: Build
FROM node:20 AS build

# Set build argument for environment file (default to .env.dev)
ARG ENV_FILE=../.env.prod
WORKDIR /app

# Copy package.json and install dependencies
COPY package*.json ./
RUN npm install

# Copy source code
COPY src ./src
COPY public ./public

# Copy env from parent folder
COPY ${ENV_FILE} .env

# Build React app
RUN npm run build

# Stage 2: Production (Nginx)
FROM nginx:stable-alpine AS prod
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]

# Stage 3: Development
FROM node:20 AS dev
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY src ./src
COPY public ./public
EXPOSE 3000
CMD ["npm", "start"]
