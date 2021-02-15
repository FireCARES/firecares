FROM prominentedgestatengine/firecares:base

USER 1000:1000

COPY requirements.txt /webapps/firecares/

WORKDIR /webapps/firecares/

RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

STOPSIGNAL SIGTERM

CMD ["./start.sh"]
