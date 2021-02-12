FROM prominentedgestatengine/firecares:base

COPY requirements.txt /webapps/firecares/

WORKDIR /webapps/firecares/

RUN pip install -r requirements.txt

COPY . .

RUN mkdir -p /webapps/firecares/temp /webapps/firecares/logs/ && \
    chmod -R 0755 /webapps/firecares/ && \
    chmod -R 0777 /webapps/firecares/logs
    #chmod -R 0777 /webapps/firecares/media

EXPOSE 8000

STOPSIGNAL SIGTERM

CMD ["./start.sh"]
