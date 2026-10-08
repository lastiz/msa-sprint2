FROM node:18

WORKDIR /app

COPY package.json ./
RUN npm install

COPY index.js booking.proto ./

CMD ["node", "index.js"]
