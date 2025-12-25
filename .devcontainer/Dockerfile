FROM mcr.microsoft.com/devcontainers/javascript-node:18

# Install git and essential build tools for analyzing legacy code
RUN apt-get update && apt-get install -y git build-essential

# Pre-create the workspace directory
WORKDIR /workspaces/Legacy-Code-Archaeologist
