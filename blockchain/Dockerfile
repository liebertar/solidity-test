FROM node:18-alpine

# Install system dependencies
RUN apk add --no-cache \
    curl \
    bash \
    git

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies with legacy peer deps for compatibility
RUN npm install --legacy-peer-deps

# Copy source code
COPY . .

# Compile contracts
RUN npm run compile

# Create shared directory for contract addresses
RUN mkdir -p /shared

# Expose ports
EXPOSE 8545 8546

# Default command (can be overridden)
CMD ["node_modules/.bin/hardhat", "node", "--hostname", "0.0.0.0"] 