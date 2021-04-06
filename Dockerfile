FROM prominentedgestatengine/firecares:base

USER firecares

COPY requirements.txt /webapps/firecares/

WORKDIR /webapps/firecares/

RUN pip install -r requirements.txt

COPY . .

USER root

RUN chown -R firecares /webapps/firecares/

USER firecares

EXPOSE 8000

STOPSIGNAL SIGTERM

CMD ["./start.sh"]
