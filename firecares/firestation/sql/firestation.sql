--
-- PostgreSQL database dump
--

DROP VIEW IF EXISTS firestations;

SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

SET search_path = public, pg_catalog;

--
-- Name: firestations; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW firestations AS
 SELECT
    a.name,
    a.address,
    a.city,
    a.state,
    a.zipcode,
    a.geom,
    'http://192.168.99.100/jurisdictions/fire-stations/' || a.id AS "URL",
    COALESCE(sum(d.firefighter), 0) AS "Total Firefighters",
    COALESCE(sum(d.firefighter_emt), 0) AS "Total Firefighter/EMTS",
    COALESCE(sum(d.firefighter_paramedic), 0) AS "Total Firefighter/Paramedics",
    COALESCE(sum(d.ems_emt), 0) AS "Total EMS only EMTs",
    COALESCE(sum(d.ems_paramedic), 0) AS "Total EMS only Paramedics",
    COALESCE(sum(d.officer), 0) AS "Total Officers",
    COALESCE(sum(d.officer_paramedic), 0) AS "Total Officer/Paramedics",
    COALESCE(sum(d.ems_supervisor), 0) AS "Total EMS Supervisors",
    COALESCE(sum(d.chief_officer), 0) AS "Total Chief Officers"
   FROM (firestation_usgsstructuredata a
     JOIN firestation_firestation b ON (b.usgsstructuredata_ptr_id = a.id)
     LEFT JOIN firestation_staffing d ON (b.usgsstructuredata_ptr_id = d.firestation_id))
  GROUP BY a.id;


--
-- PostgreSQL database dump complete
--

