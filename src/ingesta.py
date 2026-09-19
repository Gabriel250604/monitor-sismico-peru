import os
import sys
import time
from datetime import datetime, timedelta, timezone

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import execute_values

from api import consultar, normalizar

load_dotenv()

LIMA = timezone(timedelta(hours=-5))
DIAS_SOLAPAMIENTO = 90
DIAS_POR_TRAMO = 365
PAUSA_ENTRE_TRAMOS = 1

INSERTAR = """
INSERT INTO sismo (
    id_usgs, fecha_utc, fecha_local, anio, magnitud, tipo_magnitud,
    magnitud_momento, profundidad_km, profundidad_fijada, latitud, longitud,
    lugar, pais, significancia, tsunami, estado, actualizado_utc
) VALUES %s
ON CONFLICT (id_usgs) DO UPDATE SET
    fecha_utc = EXCLUDED.fecha_utc,
    fecha_local = EXCLUDED.fecha_local,
    anio = EXCLUDED.anio,
    magnitud = EXCLUDED.magnitud,
    tipo_magnitud = EXCLUDED.tipo_magnitud,
    magnitud_momento = EXCLUDED.magnitud_momento,
    profundidad_km = EXCLUDED.profundidad_km,
    profundidad_fijada = EXCLUDED.profundidad_fijada,
    latitud = EXCLUDED.latitud,
    longitud = EXCLUDED.longitud,
    lugar = EXCLUDED.lugar,
    pais = EXCLUDED.pais,
    significancia = EXCLUDED.significancia,
    tsunami = EXCLUDED.tsunami,
    estado = EXCLUDED.estado,
    actualizado_utc = EXCLUDED.actualizado_utc
WHERE sismo.actualizado_utc < EXCLUDED.actualizado_utc
RETURNING (xmax = 0) AS insertado
"""

REGISTRAR = """
INSERT INTO ingesta_log (modo, rango_desde, rango_hasta, recibidos, nuevos,
                         actualizados, duracion_seg, estado, mensaje)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
"""


def conectar():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )


def fecha_maxima(cur):
    cur.execute("SELECT max(fecha_utc) FROM sismo")
    return cur.fetchone()[0]


def tramos(desde, hasta):
    inicio = desde
    while inicio < hasta:
        fin = min(inicio + timedelta(days=DIAS_POR_TRAMO), hasta)
        yield inicio, fin
        inicio = fin


def a_fila(evento):
    fecha_utc = datetime.fromtimestamp(evento["tiempo_ms"] / 1000, tz=timezone.utc)
    fecha_local = fecha_utc.astimezone(LIMA)
    return (
        evento["id_usgs"],
        fecha_utc,
        fecha_local.replace(tzinfo=None),
        fecha_local.year,
        evento["magnitud"],
        evento["tipo_magnitud"],
        evento["magnitud_momento"],
        evento["profundidad_km"],
        evento["profundidad_fijada"],
        evento["latitud"],
        evento["longitud"],
        evento["lugar"],
        evento["pais"],
        evento["significancia"],
        evento["tsunami"],
        evento["estado"],
        datetime.fromtimestamp(evento["actualizado_ms"] / 1000, tz=timezone.utc),
    )


def main():
    arranque = time.time()
    ahora = datetime.now(timezone.utc)
    modo, desde, hasta = "desconocido", ahora, ahora
    recibidos = nuevos = actualizados = 0

    conexion = conectar()
    try:
        with conexion.cursor() as cur:
            ultima = fecha_maxima(cur)
            if ultima is None:
                modo = "inicial"
                desde = datetime(int(os.getenv("USGS_ANIO_INICIO")), 1, 1, tzinfo=timezone.utc)
            else:
                modo = "incremental"
                desde = ultima - timedelta(days=DIAS_SOLAPAMIENTO)
            hasta = ahora
            print(f"Modo {modo}: de {desde:%Y-%m-%d} a {hasta:%Y-%m-%d}")

            for tramo_desde, tramo_hasta in tramos(desde, hasta):
                eventos = normalizar(consultar(
                    tramo_desde.strftime("%Y-%m-%dT%H:%M:%S"),
                    tramo_hasta.strftime("%Y-%m-%dT%H:%M:%S"),
                ))
                recibidos += len(eventos)
                if eventos:
                    resultado = execute_values(
                        cur, INSERTAR, [a_fila(e) for e in eventos], fetch=True
                    )
                    nuevos += sum(1 for r in resultado if r[0])
                    actualizados += sum(1 for r in resultado if not r[0])
                print(f"  {tramo_desde:%Y-%m-%d} a {tramo_hasta:%Y-%m-%d}: {len(eventos)}")
                time.sleep(PAUSA_ENTRE_TRAMOS)

            cur.execute(REGISTRAR, (modo, desde, hasta, recibidos, nuevos,
                                    actualizados, round(time.time() - arranque, 2),
                                    "ok", None))
        conexion.commit()
        print(f"Recibidos {recibidos}, nuevos {nuevos}, actualizados {actualizados}")
    except Exception as error:
        conexion.rollback()
        with conexion.cursor() as cur:
            cur.execute(REGISTRAR, (modo, desde, hasta, recibidos, 0, 0,
                                    round(time.time() - arranque, 2),
                                    "error", str(error)[:500]))
        conexion.commit()
        print(f"La ejecucion fallo: {error}")
        sys.exit(1)
    finally:
        conexion.close()


if __name__ == "__main__":
    main()