FROM node:22-alpine AS build

WORKDIR /app
COPY package*.json /app/
RUN npm ci --no-audit --no-fund
COPY . /app
RUN npm run build

FROM node:22-alpine
WORKDIR /app
ENV NODE_ENV=production
COPY --from=build /app/.output /app/.output
COPY --from=build /app/package.json /app/package.json

EXPOSE 3000
CMD ["node", ".output/server/index.mjs"]
