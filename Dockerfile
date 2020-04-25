FROM firecares/base

RUN mkdir -p /webapps/firecares/ && \
    chmod -R 0755 /webapps/firecares/

WORKDIR /webapps/firecares/

COPY requirements.txt /webapps/firecares/

RUN pip install -r requirements.txt

RUN pip install -e git+https://github.com/ProminentEdge/django-favit.git@1eb9b1dbbfb65667695da08b3f16c328d1ee74c4#egg=django_favit
RUN pip install -e git+https://github.com/meilinger/django-generic-m2m@1bcf600f2b40a1b56d211b00a01d688553a8be4f#egg=django_generic_m2m
RUN pip install -e git+https://github.com/FireCARES/fire-risk.git#egg=fire_risk
RUN pip install -e git://github.com/ProminentEdge/django-osgeo-importer.git@45aa4fb1ee091416c761a9906c457014c1a7251c#egg=django_osgeo_importer

WORKDIR /webapps/firecares/

COPY . .

RUN mkdir -p /webapps/firecares/temp /webapps/firecares/logs/ && \
    chmod -R 0755 /webapps/firecares/ && \
    chmod -R 0777 /webapps/firecares/logs
    #chmod -R 0777 /webapps/firecares/media

EXPOSE 8000 1337

STOPSIGNAL SIGTERM

CMD ["./start.sh"]
