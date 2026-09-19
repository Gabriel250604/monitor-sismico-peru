\echo '== Conteo y rango temporal =='
SELECT count(*) AS eventos,
       min(fecha_utc) AS primero,
       max(fecha_utc) AS ultimo
FROM sismo;

\echo '== Identificadores repetidos =='
SELECT count(*) AS repetidos
FROM (SELECT id_usgs FROM sismo GROUP BY id_usgs HAVING count(*) > 1) AS d;

\echo '== Valores fuera de rango =='
SELECT
    count(*) FILTER (WHERE magnitud < 4.0 OR magnitud > 10.0)        AS magnitud_imposible,
    count(*) FILTER (WHERE profundidad_km < 0 OR profundidad_km > 800) AS profundidad_imposible,
    count(*) FILTER (WHERE latitud < -18.5 OR latitud > 0)           AS latitud_fuera,
    count(*) FILTER (WHERE longitud < -81.5 OR longitud > -68.5)     AS longitud_fuera,
    count(*) FILTER (WHERE fecha_utc > now())                        AS fecha_futura
FROM sismo;

\echo '== Coherencia entre hora UTC y hora local =='
SELECT count(*) AS desfase_incorrecto
FROM sismo
WHERE fecha_local <> ((fecha_utc AT TIME ZONE 'UTC') - interval '5 hours');

\echo '== Distribucion por pais =='
SELECT pais, count(*) AS eventos
FROM sismo
GROUP BY pais
ORDER BY eventos DESC;

\echo '== Banderas derivadas =='
SELECT
    count(*) FILTER (WHERE profundidad_fijada) AS con_profundidad_fijada,
    count(*) FILTER (WHERE magnitud_momento)   AS en_escala_de_momento,
    round(100.0 * count(*) FILTER (WHERE profundidad_fijada) / count(*), 1) AS pct_fijada
FROM sismo;

\echo '== Eventos por anio =='
SELECT anio,
       count(*)                            AS eventos,
       count(*) FILTER (WHERE magnitud >= 5) AS m5_o_mayor
FROM sismo
GROUP BY anio
ORDER BY anio;

\echo '== Historial de ejecuciones =='
SELECT id, ejecutado_en, modo, recibidos, nuevos, actualizados, duracion_seg, estado
FROM ingesta_log
ORDER BY id;