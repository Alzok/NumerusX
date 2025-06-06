FROM node:20-alpine AS development

# Set the working directory in the container
WORKDIR /app

# Copy package.json and package-lock.json first for better caching
COPY numerusx-ui/package*.json ./numerusx-ui/

# Copy .env.example and entrypoint script
COPY numerusx-ui/.env.example ./numerusx-ui/
COPY Docker/frontend/entrypoint.sh /app/

# Make the script executable
RUN chmod +x /app/entrypoint.sh

# Install system dependencies needed for node-gyp and native modules
RUN apk add --no-cache python3 make g++

# Expose the Vite default port
EXPOSE 5173

# Use entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]

# Command to run Vite dev server
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"] 