FROM node:23


WORKDIR /data

COPY . .

RUN npm install

RUN npx ng build

RUN cp node_modules/brotli-wasm/pkg.web/brotli_wasm_bg.wasm dist/scanner/browser

FROM nginx

COPY --from=0 /data/dist/scanner/browser /usr/share/nginx/html

COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80