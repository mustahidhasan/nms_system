# Stage 1: Build
FROM node:20 AS build

# Set build argument for environment file (default to .env.dev)
ARG ENV_FILE=.env.dev
WORKDIR /app

# Copy package.json and install dependencies
COPY package*.json ./
RUN npm install

# Copy source code
COPY src ./src
COPY public ./public

# Copy environment file safely if it exists
COPY ${ENV_FILE} .env

# Build the React app
RUN npm run build

# Stage 2: Production (Nginx)
FROM nginx:stable-alpine AS prod
# Copy build output
COPY --from=build /app/build /usr/share/nginx/html
# Copy nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]

# Stage 3: Development
FROM node:20 AS dev
WORKDIR /app

# Copy package.json and install dependencies
COPY package*.json ./
RUN npm install

# Copy source code for live dev
COPY src ./src
COPY public ./public
EXPOSE 3000
CMD ["npm", "start"]
