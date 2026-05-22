# LocalMind Portal - Production Dockerfile
FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci --only=production

# Copy built app
COPY .next/standalone ./
COPY .next/static ./.next/static
COPY public ./public
COPY src ./src

# Create data directory for SQLite
RUN mkdir -p /data
ENV DATABASE_URL=/data/localmind.db

# Expose port
EXPOSE 3000

ENV NODE_ENV=production
ENV PORT=3000

CMD ["node", "server.js"]
