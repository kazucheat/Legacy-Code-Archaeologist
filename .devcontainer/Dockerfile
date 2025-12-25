FROM mcr.microsoft.com/devcontainers/javascript-node:18-bullseye

# Install global tools
RUN npm install -g vls typescript

# Set up environment variables for the app to find the DB
ENV DB_HOST=localhost
ENV DB_USER=postgres
ENV DB_PASSWORD=postgres
ENV DB_NAME=archeologist
