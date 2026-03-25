FROM node:20-alpine
WORKDIR /app
COPY package.json ./
RUN npm install
COPY app ./app
COPY tsconfig.json next-env.d.ts next.config.js postcss.config.js tailwind.config.js ./
CMD ["npm","run","dev"]
