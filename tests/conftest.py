"""Cliente falso para probar el agente sin llamar a la API ni gastar créditos."""

import copy
from pathlib import Path
from types import SimpleNamespace

import pytest

from soporte_agente.base_conocimiento import BaseConocimiento
from soporte_agente.herramientas import EjecutorHerramientas
from soporte_agente.tickets import RepositorioTickets

CARPETA_GUIAS = Path(__file__).resolve().parent.parent / "conocimiento"


def texto(contenido):
    return SimpleNamespace(type="text", text=contenido)


def herramienta(nombre, entrada, id_bloque="toolu_1"):
    return SimpleNamespace(type="tool_use", id=id_bloque, name=nombre, input=entrada)


def mensaje(stop_reason, *bloques):
    return SimpleNamespace(stop_reason=stop_reason, content=list(bloques))


class ClienteFalso:
    """Devuelve respuestas guionizadas y guarda cada petición recibida."""

    def __init__(self, *respuestas):
        self.respuestas = list(respuestas)
        self.peticiones = []
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self._crear))

    def _crear(self, **parametros):
        parametros["messages"] = copy.copy(parametros["messages"])
        self.peticiones.append(parametros)
        return self.respuestas.pop(0)


@pytest.fixture
def ejecutor():
    return EjecutorHerramientas(BaseConocimiento(CARPETA_GUIAS), RepositorioTickets())
