"""Búsqueda por palabras clave en las guías técnicas en Markdown."""

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

PALABRAS_VACIAS = {
    "a", "al", "con", "de", "del", "el", "en", "es", "la", "las", "lo", "los",
    "me", "mi", "no", "para", "por", "que", "se", "si", "sin", "su", "un",
    "una", "y",
}
PESO_TITULO = 3


@dataclass(frozen=True)
class Seccion:
    guia: str
    titulo: str
    contenido: str


def normalizar(texto: str) -> list[str]:
    """Convierte el texto en palabras sin tildes ni palabras vacías."""
    descompuesto = unicodedata.normalize("NFD", texto.lower())
    sin_tildes = "".join(c for c in descompuesto if unicodedata.category(c) != "Mn")
    palabras = re.findall(r"[a-z0-9]+", sin_tildes)
    return [p for p in palabras if p not in PALABRAS_VACIAS]


def _dividir_secciones(ruta: Path) -> list[Seccion]:
    secciones = []
    bloques = re.split(r"^## ", ruta.read_text(encoding="utf-8"), flags=re.MULTILINE)
    for bloque in bloques[1:]:
        titulo, _, contenido = bloque.partition("\n")
        secciones.append(Seccion(ruta.stem, titulo.strip(), contenido.strip()))
    return secciones


class BaseConocimiento:
    def __init__(self, carpeta: Path):
        self.secciones = [
            seccion
            for ruta in sorted(carpeta.glob("*.md"))
            for seccion in _dividir_secciones(ruta)
        ]

    def buscar(self, consulta: str, limite: int = 3) -> list[Seccion]:
        terminos = set(normalizar(consulta))
        puntajes = []
        for seccion in self.secciones:
            en_titulo = normalizar(seccion.titulo)
            en_contenido = normalizar(seccion.contenido)
            puntaje = sum(
                en_titulo.count(t) * PESO_TITULO + en_contenido.count(t)
                for t in terminos
            )
            if puntaje > 0:
                puntajes.append((puntaje, seccion))
        puntajes.sort(key=lambda par: par[0], reverse=True)
        return [seccion for _, seccion in puntajes[:limite]]
