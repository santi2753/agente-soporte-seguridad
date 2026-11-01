"""Crea las dependencias compartidas por la consola y la API web."""

import os
from pathlib import Path

import anthropic

from .base_conocimiento import BaseConocimiento
from .herramientas import EjecutorHerramientas
from .tickets import RepositorioTickets

RAIZ = Path(__file__).resolve().parent.parent


class CredencialesFaltantes(Exception):
    pass


def crear_cliente_claude() -> anthropic.Anthropic:
    # Sin esta validación, el SDK solo falla con un TypeError al primer mensaje.
    if not (os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")):
        raise CredencialesFaltantes("Define la variable ANTHROPIC_API_KEY.")
    return anthropic.Anthropic()


def crear_ejecutor() -> EjecutorHerramientas:
    (RAIZ / "datos").mkdir(exist_ok=True)
    base = BaseConocimiento(RAIZ / "conocimiento")
    tickets = RepositorioTickets(str(RAIZ / "datos" / "tickets.db"))
    return EjecutorHerramientas(base, tickets)
