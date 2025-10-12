# Stage 1: Build React app
FROM node:20 as build
WORKDIR /app

# Copy package.json & package-lock.json & install dependencies
COPY package*.json ./
RUN npm install

# Copy source code
COPY . .

# Copy environment file for production
ARG ENV_FILE=.env.prod.fe
COPY ${ENV_FILE} .env

# Build React app
RUN npm run build

# Stage 2: Serve with Nginx
FROM nginx:stable-alpine as prod

# Remove default nginx website
RUN rm -rf /usr/share/nginx/html/*

# Copy built React app
COPY --from=build /app/build /usr/share/nginx/html

# Copy custom Nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]
