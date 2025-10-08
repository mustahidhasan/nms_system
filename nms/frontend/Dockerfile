# Build stage
FROM node:20 AS build

WORKDIR /app

# Copy dependencies first for caching
COPY package.json package-lock.json ./
RUN npm install

# Copy all frontend code and build React app
COPY . .
RUN npm run build

# Production stage
FROM nginx:stable-alpine

# Copy React build
COPY --from=build /app/build /usr/share/nginx/html

# Copy custom Nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
