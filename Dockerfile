FROM prominentedgestatengine/firecares:base

ARG USER=firecares
ARG UID=1000
ARG GID=1000
ARG PW=firecares

USER 1000:1000

COPY requirements.txt /webapps/firecares/

WORKDIR /webapps/firecares/

RUN pip install -r requirements.txt

COPY . .

USER root

RUN chown -R $USER:$USER /webapps/firecares/

USER ${UID}:${GID}

EXPOSE 8000

STOPSIGNAL SIGTERM

CMD ["./start.sh"]
