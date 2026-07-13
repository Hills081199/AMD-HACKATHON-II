FROM node:20-alpine AS base

WORKDIR /app
COPY apps/web/package.json apps/web/package-lock.json* ./
RUN npm install

COPY apps/web/ ./
RUN npm run build

# Copy static files to the standalone server directory
# Next.js standalone output doesn't include static files by default (expects CDN)
RUN mkdir -p .next/standalone/public .next/standalone/.next/static
RUN cp -r public/* .next/standalone/public/ || true
RUN cp -r .next/static/* .next/standalone/.next/static/ || true

ENV HOSTNAME="0.0.0.0"
ENV PORT=3000

EXPOSE 3000
CMD ["node", ".next/standalone/server.js"]
