# ============================================================
# Sarthi Frontend - Production Multi-Stage Dockerfile
# Next.js 16.2.6 with standalone output for minimal image size
# ============================================================

# --------------- Stage 1: Build ---------------
FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies first (layer cache optimization)
COPY package.json package-lock.json* ./
RUN npm ci

# Copy source code
COPY . .

# Build-time env var — injected at build so Next.js can inline it
ARG NEXT_PUBLIC_API_URL=""
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

# Build the Next.js application (output: standalone)
RUN npm run build

# --------------- Stage 2: Production Runner ---------------
FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production
ENV PORT=3000

# Copy the standalone server and required assets
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

# Copy public assets if they exist (fonts, images, icons, etc.)
# Using a wildcard so the build won't fail if the directory is empty
COPY --from=builder /app/public ./public

EXPOSE 3000

CMD ["node", "server.js"]
