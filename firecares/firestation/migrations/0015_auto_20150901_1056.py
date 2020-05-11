# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('firestation', '0014_auto_20150901_1052'),
    ]

    sql = """
 CREATE FUNCTION department_fts_document(integer) RETURNS tsvector AS $$
    DECLARE
         department_document TEXT;
         name varchar;
         city varchar;
         state varchar(2);
         state_name varchar(40);
         postal_code varchar(10);
     BEGIN
         SELECT fd.name, add.city, fd.state, states.state_name, add.postal_code
         INTO name, city, state, state_name, postal_code
         FROM firestation_firedepartment fd
         LEFT JOIN firecares_core_address add
            ON fd.headquarters_address_id=add.id
         LEFT JOIN usgs_stateorterritoryhigh states
            ON ST_CoveredBy(ST_Centroid(fd.geom), states.geom)
        WHERE fd.id=$1;

        SELECT concat_ws(' ', name, city, state, state_name, postal_code) INTO department_document;

     RETURN to_tsvector('pg_catalog.simple', department_document);
 END;
  $$ LANGUAGE plpgsql;

-- Overload the department_fts_document by calling this version the same name but accepting a different argument type.
-- This one takes a Fire Department object.

CREATE FUNCTION department_fts_document(department firestation_firedepartment) RETURNS tsvector AS $$
 DECLARE
     department_document TEXT;
     name varchar;
     city varchar;
     state varchar(2);
     state_name varchar(40);
     postal_code varchar(10);
 BEGIN
     SELECT add.city, states.state_name, add.postal_code
     INTO city, state_name, postal_code
     FROM firestation_firedepartment fd
     LEFT JOIN firecares_core_address add
        ON fd.headquarters_address_id=add.id
     LEFT JOIN usgs_stateorterritoryhigh states
        ON ST_CoveredBy(ST_Centroid(fd.geom), states.geom)
    WHERE fd.id=department.id;

    SELECT concat_ws(' ', department.name, city, department.state, state_name, postal_code) INTO department_document;

    RETURN to_tsvector('pg_catalog.simple', department_document);
 END;
  $$ LANGUAGE plpgsql;

 CREATE FUNCTION department_fts_document_trigger() RETURNS TRIGGER AS $$
 BEGIN

     NEW.fts_document=department_fts_document(NEW);
     RETURN NEW;
END;
$$ LANGUAGE plpgsql;

"""

    operations = [
        migrations.RunSQL(sql),
        migrations.RunSQL("ALTER TABLE firestation_firedepartment ADD COLUMN fts_document tsvector"),
        migrations.RunSQL("UPDATE firestation_firedepartment SET fts_document=department_fts_document(id)"),
        migrations.RunSQL("CREATE TRIGGER department_fts_update_trigger BEFORE UPDATE OF name, headquarters_address_id, geom ON firestation_firedepartment FOR EACH ROW EXECUTE PROCEDURE department_fts_document_trigger()"),
        migrations.RunSQL("CREATE TRIGGER department_fts_insert_trigger BEFORE INSERT ON firestation_firedepartment FOR EACH ROW EXECUTE PROCEDURE department_fts_document_trigger()"),
        migrations.RunSQL("CREATE INDEX firestation_firedepartment_fts_index ON firestation_firedepartment USING gin(fts_document)")
    ]
