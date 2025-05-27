FROM node:20-alpine AS development

# Set the working directory in the container
WORKDIR /app

# Copy the initialization script into the container
COPY init-frontend.sh /app/init-frontend.sh

# Make the script executable
RUN chmod +x /app/init-frontend.sh

# Expose the Vite default port
EXPOSE 5173

# Command to run the initialization script
# The script will handle 'npm install' and 'npm run dev'
CMD ["/app/init-frontend.sh"] 