# Base stage
FROM node:20-alpine AS base

WORKDIR /app

# Enable corepack for pnpm
RUN corepack enable

# Dependencies stage
FROM base AS dependencies

# Copy package files
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY apps/web/package.json apps/web/

# Install all dependencies (including dev)
RUN pnpm install --filter @apps/web... --frozen-lockfile

# Development stage
FROM base AS development

ENV NODE_ENV=development

# Copy package files
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY apps/web/package.json apps/web/

# Install dependencies
RUN pnpm install --filter @apps/web...

# Copy application code
COPY apps/web apps/web

WORKDIR /app/apps/web

# Expose port
EXPOSE 3000

# Run with hot-reload
CMD ["pnpm", "dev", "--hostname", "0.0.0.0", "--port", "3000"]

# Builder stage - build the application
FROM dependencies AS builder

# Copy application code
COPY apps/web apps/web

# Build the application
WORKDIR /app/apps/web
RUN pnpm build

# Production stage
FROM base AS production

WORKDIR /app

# Create non-root user
# Use GID/UID 1001 to avoid conflicts with existing system users
RUN addgroup -g 1001 appuser && \
    adduser -D -u 1001 -G appuser appuser && \
    chown -R appuser:appuser /app

# Copy package files for production dependencies
COPY --chown=appuser:appuser package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY --chown=appuser:appuser apps/web/package.json apps/web/

# Install production dependencies only
RUN pnpm install --filter @apps/web... --frozen-lockfile --prod

# Copy built application from builder
COPY --from=builder --chown=appuser:appuser /app/apps/web/.next /app/apps/web/.next
COPY --from=builder --chown=appuser:appuser /app/apps/web/public /app/apps/web/public
COPY --chown=appuser:appuser apps/web/next.config.ts /app/apps/web/

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 3000

# Set working directory
WORKDIR /app/apps/web

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD node -e "require('http').get('http://localhost:3000', (r) => {process.exit(r.statusCode === 200 ? 0 : 1)})"

# Run the application
CMD ["pnpm", "start"]
