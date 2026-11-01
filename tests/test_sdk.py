"""Usa el SDK real con un servidor simulado para validar lo que viaja por la red."""

import json

import anthropic
import httpx2

from soporte_agente.agente import Agente


def respuesta_api(stop_reason, contenido):
    return {
        "id": "msg_1",
        "type": "message",
        "role": "assistant",
        "model": "claude-opus-5-5",
        "content": contenido,
        "stop_reason": stop_reason,
        "stop_sequence": None,
        "usage": {"input_tokens": 10, "output_tokens": 5},
    }


def test_peticion_real_del_sdk_y_retorno_del_historial(ejecutor):
    guion = [
        respuesta_api(
            "tool_use",
            [
                {"type": "thinking", "thinking": "", "signature": "firma"},
                {
                    "type": "tool_use",
                    "id": "toolu_1",
                    "name": "buscar_guia",
                    "input": {"consulta": "huella"},
                },
            ],
        ),
        respuesta_api("end_turn", [{"type": "text", "text": "Limpia el sensor."}]),
    ]
    recibidas = []

    def servidor(peticion):
        recibidas.append((peticion, json.loads(peticion.content)))
        return httpx2.Response(200, json=guion[len(recibidas) - 1])

    cliente = anthropic.Anthropic(
        api_key="clave-de-prueba",
        http_client=httpx2.Client(transport=httpx2.MockTransport(servidor)),
    )
    respuesta = Agente(cliente, ejecutor).responder("No lee la huella")

    assert respuesta.texto == "Limpia el sensor."

    peticion, cuerpo = recibidas[0]
    assert peticion.url.path == "/v1/messages"
    assert "server-side-fallback-2026-07-01" in peticion.headers["anthropic-beta"]
    assert cuerpo["fallbacks"] == "default"
    assert cuerpo["thinking"] == {"type": "adaptive"}
    assert cuerpo["output_config"] == {"effort": "medium"}
    assert all(h["strict"] is True for h in cuerpo["tools"])

    # El bloque de razonamiento debe volver intacto en el siguiente turno.
    _, segundo = recibidas[1]
    asistente = segundo["messages"][1]
    assert asistente["content"][0] == {
        "type": "thinking",
        "thinking": "",
        "signature": "firma",
    }
    resultado = segundo["messages"][2]["content"][0]
    assert resultado["type"] == "tool_result"
    assert resultado["tool_use_id"] == "toolu_1"
    assert "huella" in resultado["content"]
