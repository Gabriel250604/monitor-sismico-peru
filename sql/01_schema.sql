DROP TABLE IF EXISTS ingesta_log;
DROP TABLE IF EXISTS sismo;

CREATE TABLE sismo (
    id_usgs            VARCHAR(40) PRIMARY KEY,
    fecha_utc          TIMESTAMPTZ NOT NULL,
    fecha_local        TIMESTAMP NOT NULL,
    anio               SMALLINT NOT NULL,
    magnitud           NUMERIC(3,1) NOT NULL,
    tipo_magnitud      VARCHAR(10) NOT NULL,
    magnitud_momento   BOOLEAN NOT NULL,
    profundidad_km     NUMERIC(7,3) NOT NULL,
    profundidad_fijada BOOLEAN NOT NULL,
    latitud            NUMERIC(8,4) NOT NULL,
    longitud           NUMERIC(9,4) NOT NULL,
    lugar              TEXT,
    pais               VARCHAR(20) NOT NULL,
    significancia      INTEGER,
    tsunami            SMALLINT,
    estado             VARCHAR(15),
    actualizado_utc    TIMESTAMPTZ NOT NULL,
    cargado_en         TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_sismo_fecha ON sismo (fecha_utc);
CREATE INDEX idx_sismo_anio ON sismo (anio);
CREATE INDEX idx_sismo_pais ON sismo (pais);
CREATE INDEX idx_sismo_magnitud ON sismo (magnitud);

CREATE TABLE ingesta_log (
    id           SERIAL PRIMARY KEY,
    ejecutado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
    modo         VARCHAR(15) NOT NULL,
    rango_desde  TIMESTAMPTZ NOT NULL,
    rango_hasta  TIMESTAMPTZ NOT NULL,
    recibidos    INTEGER NOT NULL DEFAULT 0,
    nuevos       INTEGER NOT NULL DEFAULT 0,
    actualizados INTEGER NOT NULL DEFAULT 0,
    duracion_seg NUMERIC(8,2),
    estado       VARCHAR(15) NOT NULL,
    mensaje      TEXT
);

CREATE INDEX idx_log_ejecutado ON ingesta_log (ejecutado_en);