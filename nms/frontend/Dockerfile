# =============================
# Stage 1: Build React app
# =============================
FROM node:20 AS build
WORKDIR /app

# Copy dependencies and install
COPY package*.json ./
RUN npm install

# Copy source code
COPY . .

# Copy environment file for production
ARG ENV_FILE=.env.prod.fe
COPY ${ENV_FILE} .env

# Build React app
RUN npm run build

# =============================
# Stage 2: Serve with Nginx + SSL
# =============================
FROM nginx:stable-alpine AS prod

# Remove default nginx website
RUN rm -rf /usr/share/nginx/html/*

# Copy built React app from build stage
COPY --from=build /app/build /usr/share/nginx/html

# Copy custom Nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Create SSL directory (mounted via Docker Compose)
RUN mkdir -p /etc/ssl/private

# Expose ports
EXPOSE 80
EXPOSE 443

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]
