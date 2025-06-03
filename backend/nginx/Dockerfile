FROM nginx:latest

RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d
COPY proxy_params /etc/nginx
RUN mkdir -p /etc/nginx/ssl/
COPY ssl/certificate.key /etc/nginx/ssl/certificate.key
COPY ssl/fullchain.pem /etc/nginx/ssl/fullchain.pem
