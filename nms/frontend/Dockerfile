# Stage 1: Build React app
FROM node:20 AS build

# Set working directory
WORKDIR /app

# Copy package.json and package-lock.json
COPY package.json package-lock.json ./

# Install dependencies
RUN npm install

# Copy the rest of the frontend source code
COPY . .

# Symlink the .env from project root
# Assuming you mount or copy .env from nms/.env when building via docker-compose
RUN ln -s /app/../.env .env

# Build React app
RUN npm run build

# Stage 2: Serve with nginx
FROM nginx:stable-alpine

# Set working directory
WORKDIR /usr/share/nginx/html

# Copy build output from Stage 1
COPY --from=build /app/build .

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
