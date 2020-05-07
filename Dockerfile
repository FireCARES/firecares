FROM firecares/base

RUN mkdir -p /webapps/firecares/ && \
    chmod -R 0755 /webapps/firecares/

WORKDIR /webapps/firecares/

COPY requirements.txt /webapps/firecares/

RUN pip install -r requirements.txt

WORKDIR /webapps/firecares/

COPY . .

RUN mkdir -p /webapps/firecares/temp /webapps/firecares/logs/ && \
    chmod -R 0755 /webapps/firecares/ && \
    chmod -R 0777 /webapps/firecares/logs
    #chmod -R 0777 /webapps/firecares/media

EXPOSE 8000 1337

STOPSIGNAL SIGTERM

CMD ["./start.sh"]
