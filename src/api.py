import time

import requests

URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"
PERU = {
    "minlatitude": -18.5,
    "maxlatitude": 0.0,
    "minlongitude": -81.5,
    "maxlongitude": -68.5,
}
MAGNITUD_MINIMA = 4.0
PAISES = ["Peru", "Ecuador", "Bolivia", "Brazil", "Chile", "Colombia"]
PROFUNDIDADES_FIJADAS = {10.0, 33.0, 35.0, 100.0, 150.0}

INTENTOS = 4
ESPERA_INICIAL = 5
TIEMPO_LIMITE = 120


class ErrorAPI(Exception):
    pass


def consultar(inicio, fin):
    params = {
        "format": "geojson",
        "starttime": inicio,
        "endtime": fin,
        "minmagnitude": MAGNITUD_MINIMA,
        "orderby": "time-asc",
        **PERU,
    }
    espera = ESPERA_INICIAL
    for intento in range(1, INTENTOS + 1):
        try:
            respuesta = requests.get(URL, params=params, timeout=TIEMPO_LIMITE)
            if respuesta.status_code == 204:
                return []
            respuesta.raise_for_status()
            return respuesta.json()["features"]
        except (requests.RequestException, ValueError, KeyError) as error:
            if intento == INTENTOS:
                raise ErrorAPI(f"Fallo la consulta de {inicio} a {fin}: {error}") from error
            time.sleep(espera)
            espera *= 2
    return []


def detectar_pais(lugar):
    texto = (lugar or "").lower()
    for pais in PAISES:
        if pais.lower() in texto:
            return pais
    return "Sin dato"


def normalizar(features):
    eventos = []
    for f in features:
        p = f["properties"]
        lon, lat, profundidad = f["geometry"]["coordinates"]
        if p.get("mag") is None or profundidad is None:
            continue
        tipo = (p.get("magType") or "sin tipo").lower()
        lugar = p.get("place") or ""
        eventos.append({
            "id_usgs": f["id"],
            "tiempo_ms": p["time"],
            "actualizado_ms": p["updated"],
            "magnitud": float(p["mag"]),
            "tipo_magnitud": tipo,
            "magnitud_momento": tipo.startswith("mw"),
            "profundidad_km": float(profundidad),
            "profundidad_fijada": float(profundidad) in PROFUNDIDADES_FIJADAS,
            "latitud": lat,
            "longitud": lon,
            "lugar": lugar,
            "pais": detectar_pais(lugar),
            "significancia": p.get("sig"),
            "tsunami": p.get("tsunami"),
            "estado": p.get("status"),
        })
    return eventos