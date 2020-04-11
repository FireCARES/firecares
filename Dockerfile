FROM python:2.7.16-stretch

# FIRECARES STUFF:
RUN apt-get update && \
    apt-get install -y \
        build-essential \
        libcurl4-gnutls-dev \
        libgnutls28-dev \
        libssl-dev \
        libgcrypt20-dev \
        default-libmysqlclient-dev \
        python-pycurl \
        python-dev \
        vim \
        telnet \
        screen

RUN mkdir -p /app && \
    chmod -R 0755 /app

RUN mkdir -p /mnt && \
    chmod -R 0777 /mnt/

VOLUME /mnt/

WORKDIR /app/

COPY requirements.txt /app/

RUN pip install -r requirements.txt

COPY ./firecares /webapps/firecares/

RUN mkdir -p /webapps/firecares/temp /webapps/firecares/logs/ && \
    chmod -R 0755 /app && \
    chmod -R 0777 /webapps/firecares/logs && \
    chmod -R 0777 /webapps/firecares/media

# Nginx crap:
ENV NGINX_VERSION   1.16.0
ENV NJS_VERSION     0.3.1
ENV PKG_RELEASE     1~stretch

# forward request and error logs to docker log collector
RUN ln -sf /dev/stdout /var/log/nginx/access.log \
	&& ln -sf /dev/stderr /var/log/nginx/error.log

RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d

COPY start.sh /webapps/firecares/start.sh

WORKDIR /webapps/firecares/

EXPOSE 8000 1337

STOPSIGNAL SIGTERM

CMD ["/webapps/firecares/start.sh"]
