FROM node:18-alpine

# Global workdir for the application
WORKDIR /app

# Set NODE_PATH to help Node resolve shared modules.
# This path should contain the 'shared' directory.
ENV NODE_PATH=/app

# --- Install dependencies for shared kafka-client module ---
# Copy only package files first to leverage Docker cache
COPY api/shared/kafka-client/package*.json /tmp/shared/kafka-client/
RUN cd /tmp/shared/kafka-client && npm install --production

# --- Install dependencies for the main user-service ---
COPY api/user-service/package*.json ./
RUN npm install --production

# --- Copy source code ---
# Copy shared module source code (e.g., kafka-client, etc.)
COPY api/shared /app/shared

# Copy main user-service source code
# Ensure all necessary subdirectories of api/user-service are copied.
# If your user-service has more than just 'src', add COPY lines for them.
# For example: COPY api/user-service/config ./config
COPY api/user-service/src ./src

# Now, move the pre-installed node_modules for kafka-client to its final location
# Ensure the target directory exists and remove any existing node_modules
RUN mkdir -p /app/shared/kafka-client && rm -rf /app/shared/kafka-client/node_modules
# Move node_modules. If it doesn't exist from the temp install, this won't create an error.
RUN if [ -d /tmp/shared/kafka-client/node_modules ]; then mv /tmp/shared/kafka-client/node_modules /app/shared/kafka-client/; fi
# Clean up temp directory
RUN rm -rf /tmp/shared

# Healthcheck (update path if your healthcheck script is located elsewhere)
HEALTHCHECK --interval=30s --timeout=30s --start-period=30s --retries=3 CMD node src/utils/healthcheck.js || exit 1

# Command to run the application
CMD ["node", "src/app.js"]