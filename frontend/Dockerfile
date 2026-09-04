# ============================================================
# JOURNEY FORENSICS - NEXT.JS FRONTEND
# ============================================================

FROM node:22-alpine AS dependencies

WORKDIR /app

ENV NEXT_TELEMETRY_DISABLED=1

COPY frontend/package.json ./

RUN npm install

FROM node:22-alpine AS builder

WORKDIR /app

ENV NEXT_TELEMETRY_DISABLED=1

COPY --from=dependencies /app/node_modules ./node_modules
COPY frontend/ ./

ARG NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
ENV NEXT_PUBLIC_API_BASE_URL=${NEXT_PUBLIC_API_BASE_URL}

RUN npm run build

FROM node:22-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000
ENV HOSTNAME=0.0.0.0

COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

EXPOSE 3000

CMD ["node", "server.js"]