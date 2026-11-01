"""API REST: uvicorn soporte_agente.api:app"""

import uuid
from collections.abc import Callable

import anthropic
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .agente import Agente
from .configuracion import CredencialesFaltantes, crear_cliente_claude, crear_ejecutor
from .herramientas import EjecutorHerramientas
from .tickets import TicketNoEncontrado


class PeticionChat(BaseModel):
    mensaje: str = Field(min_length=1, max_length=4000)
    sesion_id: str | None = None


class RespuestaChat(BaseModel):
    sesion_id: str
    respuesta: str
    herramientas: list[str]


def crear_app(
    ejecutor: EjecutorHerramientas,
    crear_cliente: Callable[[], object] = crear_cliente_claude,
) -> FastAPI:
    app = FastAPI(title="Agente de soporte de seguridad electrónica")
    sesiones: dict[str, Agente] = {}
    # Sin credenciales, los tickets siguen disponibles y solo /chat responde 503.
    try:
        cliente = crear_cliente()
    except CredencialesFaltantes:
        cliente = None

    @app.post("/chat", response_model=RespuestaChat)
    def chat(peticion: PeticionChat) -> RespuestaChat:
        if cliente is None:
            raise HTTPException(503, "Define la variable ANTHROPIC_API_KEY")
        sesion_id = peticion.sesion_id or str(uuid.uuid4())
        if peticion.sesion_id and peticion.sesion_id not in sesiones:
            raise HTTPException(404, "Sesión no encontrada")
        agente = sesiones.setdefault(sesion_id, Agente(cliente, ejecutor))
        try:
            respuesta = agente.responder(peticion.mensaje)
        except anthropic.RateLimitError:
            raise HTTPException(429, "Límite de uso alcanzado")
        except (anthropic.APIStatusError, anthropic.APIConnectionError):
            raise HTTPException(502, "No se pudo consultar el modelo")
        return RespuestaChat(
            sesion_id=sesion_id,
            respuesta=respuesta.texto,
            herramientas=respuesta.herramientas,
        )

    @app.get("/tickets")
    def listar_tickets() -> list[dict]:
        return ejecutor.tickets.listar()

    @app.get("/tickets/{ticket_id}")
    def obtener_ticket(ticket_id: int) -> dict:
        try:
            return ejecutor.tickets.obtener(ticket_id)
        except TicketNoEncontrado as error:
            raise HTTPException(404, str(error))

    return app


app = crear_app(crear_ejecutor())
