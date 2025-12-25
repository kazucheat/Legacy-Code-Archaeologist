FROM mcr.microsoft.com/devcontainers/javascript-node:18-bullseye

# Install global tools
RUN npm install -g vls typescript

# Set up environment variables for the app to find the DB
ENV DB_HOST=localhost
ENV DB_USER=postgres
ENV DB_PASSWORD=postgres
ENV DB_NAME=archeologist
FROM mcr.microsoft.com/devcontainers/javascript-node:18

# Install git and essential build tools for analyzing legacy code
RUN apt-get update && apt-get install -y git build-essential

# Pre-create the workspace directory
WORKDIR /workspaces/Legacy-Code-Archaeologist
