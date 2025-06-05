FROM node:20-alpine AS development

# Set the working directory in the container
WORKDIR /app

# Copy package.json and package-lock.json first for better caching
COPY numerusx-ui/package*.json ./numerusx-ui/

# Copy the initialization script into the container
COPY Docker/frontend/init-frontend.sh /app/init-frontend.sh

# Make the script executable
RUN chmod +x /app/init-frontend.sh

# Install system dependencies needed for node-gyp and native modules
RUN apk add --no-cache python3 make g++

# Expose the Vite default port
EXPOSE 5173

# Command to run the initialization script
# The script will handle 'npm install' and 'npm run dev'
CMD ["/app/init-frontend.sh"] 
# Expose the Vite default port
EXPOSE 5173

# Command to run the initialization script
# The script will handle 'npm install' and 'npm run dev'
CMD ["/app/init-frontend.sh"] 