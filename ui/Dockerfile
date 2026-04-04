# ── Stage 1: build the Next.js app ──────────────────────────────────────────
FROM node:20-alpine AS builder
WORKDIR /app

# Install dependencies based on package-lock.json
COPY package.json package-lock.json* ./
RUN npm ci

# Copy the rest of the application and build
COPY . .
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
RUN npm run build

# ── Stage 2: production runtime (smallest possible) ─────────────────────────
FROM node:20-alpine AS runtime
WORKDIR /app

ENV NODE_ENV=production

# Copy only what Next.js needs to serve the app in standalone mode
# server.js is the entry point for the standalone build
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

EXPOSE 3000

# Next.js standalone mode runs on port 3000 by default
CMD ["node", "server.js"]
