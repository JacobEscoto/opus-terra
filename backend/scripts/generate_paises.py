"""Genera etiquetas de países desde Natural Earth para una región."""

from __future__ import annotations

import argparse
import json
import tomllib
from pathlib import Path

import geopandas as gpd

ROOT = Path(__file__).resolve().parents[2]
SHP = ROOT / "data" / "external" / "naturalearth" / "ne_10m_admin_0_countries.shp"
DATASETS = ROOT / "backend" / "config" / "datasets.toml"
OUTPUT = ROOT / "frontend" / "public" / "data"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--region", required=True)
    args = parser.parse_args()
    with DATASETS.open("rb") as archivo:
        regiones = tomllib.load(archivo)["regions"]
    if args.region not in regiones:
        raise SystemExit(f'La región "{args.region}" no existe en datasets.toml.')
    if not SHP.exists():
        raise SystemExit(f"No existe el shapefile: {SHP}")
    lon_min, lat_min, lon_max, lat_max = regiones[args.region]["bbox"]
    tabla = gpd.read_file(SHP)
    requeridas = {"NAME_ES", "LABEL_X", "LABEL_Y", "ISO_A2"}
    faltantes = requeridas - set(tabla.columns)
    if faltantes:
        raise SystemExit(f"Faltan columnas en Natural Earth: {', '.join(sorted(faltantes))}")
    paises = [
        {"nombre": str(fila.NAME_ES), "iso": str(fila.ISO_A2), "lat": round(float(fila.LABEL_Y), 3), "lon": round(float(fila.LABEL_X), 3)}
        for _, fila in tabla.iterrows()
        if lon_min <= float(fila.LABEL_X) <= lon_max and lat_min <= float(fila.LABEL_Y) <= lat_max
    ]
    paises.sort(key=lambda pais: pais["nombre"])
    destino = OUTPUT / args.region
    destino.mkdir(parents=True, exist_ok=True)
    (destino / "paises.json").write_text(json.dumps(paises, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{args.region}: {len(paises)} países -> {destino / 'paises.json'}")


if __name__ == "__main__":
    main()
