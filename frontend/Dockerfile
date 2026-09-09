# Step 1: Build app
FROM node:18 AS builder
WORKDIR /app
COPY . .
RUN npm install && npm run build

# Step 2: Run app
FROM node:18-alpine AS runner
WORKDIR /app
COPY --from=builder /app ./
EXPOSE 3000
CMD ["npm", "start"]
