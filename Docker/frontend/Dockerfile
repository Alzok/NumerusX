# Stage 1: Build the React application
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package.json and package-lock.json (or yarn.lock)
COPY numerusx-ui/package.json numerusx-ui/package-lock.json* ./
# If using yarn, uncomment below and comment out npm ci
# COPY numerusx-ui/yarn.lock ./

# Install dependencies
# Use npm ci for reproducible builds if package-lock.json is present
RUN npm ci
# If using yarn, uncomment below and comment out npm ci
# RUN yarn install --frozen-lockfile

# Copy the rest of the frontend application code
COPY numerusx-ui/ .

# Set build-time environment variables if needed
# ARG REACT_APP_BACKEND_URL
# ENV REACT_APP_BACKEND_URL=$REACT_APP_BACKEND_URL

# Build the application
RUN npm run build

# Stage 2: Serve the built application with Nginx
FROM nginx:1.25-alpine

# Copy the build output from the builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy a custom Nginx configuration file (optional, but recommended)
# This file would handle proxying API requests to the backend and serving React app
COPY Docker/frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80 (or the port Nginx is configured to listen on)
EXPOSE 80

# Start Nginx when the container launches
CMD ["nginx", "-g", "daemon off;"] 