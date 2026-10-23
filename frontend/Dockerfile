# ==============================================================================
# Multi-stage Dockerfile for Next.js 14 Frontend (MASDS)
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Dependencies
# ------------------------------------------------------------------------------
FROM node:20-alpine AS deps

# Check https://github.com/nodejs/docker-node/tree/b4117f9333da4138b03a546ec926ef50a31506c3#nodealpine
# to understand why libc6-compat might be needed.
RUN apk add --no-cache libc6-compat
WORKDIR /app

# Copy dependency lock files
COPY package.json package-lock.json* yarn.lock* pnpm-lock.yaml* ./

# Install dependencies based on available lockfile
RUN \
  if [ -f package-lock.json ]; then npm ci; \
  elif [ -f yarn.lock ]; then yarn --frozen-lockfile; \
  elif [ -f pnpm-lock.yaml ]; then corepack enable pnpm && pnpm i --frozen-lockfile; \
  else npm install; \
  fi

# ------------------------------------------------------------------------------
# Stage 2: Builder
# ------------------------------------------------------------------------------
FROM node:20-alpine AS builder

WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Environment variables for build time
ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=production

# Run Next.js build (generates standalone server output)
RUN npm run build

# ------------------------------------------------------------------------------
# Stage 3: Runner
# ------------------------------------------------------------------------------
FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Add non-root system group and user
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy static assets and public directory if available
COPY --from=builder /app/public ./public

# Automatically leverage output traces to reduce image size
# https://nextjs.org/docs/advanced-features/output-file-tracing
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

# Health check to ensure frontend is responding
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3000 || exit 1

# Start standalone Next.js server
CMD ["node", "server.js"]
