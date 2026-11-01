"""Herramientas que Claude puede usar y su ejecución."""

import json

from .base_conocimiento import BaseConocimiento
from .tickets import ESTADOS, PRIORIDADES, RepositorioTickets, TicketNoEncontrado

HERRAMIENTAS = [
    {
        "name": "buscar_guia",
        "description": (
            "Busca procedimientos en las guías técnicas de cámaras, grabadores, "
            "control de acceso y alarmas. Úsala antes de indicar pasos al usuario."
        ),
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "consulta": {
                    "type": "string",
                    "description": "Síntoma o equipo, por ejemplo: cámara sin imagen",
                },
            },
            "required": ["consulta"],
            "additionalProperties": False,
        },
    },
    {
        "name": "crear_ticket",
        "description": (
            "Registra un caso de soporte. Úsala cuando el problema no se resuelva "
            "con las guías, requiera visita técnica o el usuario lo pida."
        ),
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "cliente": {"type": "string", "description": "Nombre del cliente o sede"},
                "equipo": {"type": "string", "description": "Equipo afectado"},
                "descripcion": {
                    "type": "string",
                    "description": "Síntoma y pasos que ya se intentaron",
                },
                "prioridad": {
                    "type": "string",
                    "enum": list(PRIORIDADES),
                    "description": "alta si afecta la seguridad de un sitio o de las personas",
                },
            },
            "required": ["cliente", "equipo", "descripcion", "prioridad"],
            "additionalProperties": False,
        },
    },
    {
        "name": "consultar_ticket",
        "description": "Consulta el estado y las notas de un ticket existente.",
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "ticket_id": {"type": "integer", "description": "Número del ticket"},
            },
            "required": ["ticket_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "actualizar_ticket",
        "description": (
            "Cambia el estado de un ticket y deja una nota. Usa 'escalado' cuando "
            "necesite un técnico y 'resuelto' solo si el usuario confirma la solución."
        ),
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "ticket_id": {"type": "integer", "description": "Número del ticket"},
                "estado": {"type": "string", "enum": list(ESTADOS)},
                "nota": {"type": "string", "description": "Motivo del cambio"},
            },
            "required": ["ticket_id", "estado", "nota"],
            "additionalProperties": False,
        },
    },
]


class ErrorHerramienta(Exception):
    """Error que se le devuelve a Claude para que pueda corregir la llamada."""


class EjecutorHerramientas:
    def __init__(self, base: BaseConocimiento, tickets: RepositorioTickets):
        self.base = base
        self.tickets = tickets

    def ejecutar(self, nombre: str, entrada: dict) -> str:
        try:
            if nombre == "buscar_guia":
                resultado = self._buscar_guia(entrada["consulta"])
            elif nombre == "crear_ticket":
                resultado = {"ticket_id": self.tickets.crear(**entrada), "estado": "abierto"}
            elif nombre == "consultar_ticket":
                resultado = self.tickets.obtener(entrada["ticket_id"])
            elif nombre == "actualizar_ticket":
                resultado = self.tickets.actualizar(**entrada)
            else:
                raise ErrorHerramienta(f"Herramienta desconocida: {nombre}")
        except (KeyError, TypeError, ValueError, TicketNoEncontrado) as error:
            raise ErrorHerramienta(str(error)) from error
        return json.dumps(resultado, ensure_ascii=False)

    def _buscar_guia(self, consulta: str) -> dict:
        secciones = self.base.buscar(consulta)
        return {
            "resultados": [
                {"guia": s.guia, "titulo": s.titulo, "contenido": s.contenido}
                for s in secciones
            ]
        }
