import json

from conftest import ClienteFalso, herramienta, mensaje, texto
from soporte_agente.agente import (
    AVISO_LARGO,
    AVISO_LIMITE,
    AVISO_RECHAZO,
    MAX_PASOS,
    Agente,
)
from soporte_agente.herramientas import HERRAMIENTAS


def test_respuesta_directa_sin_herramientas(ejecutor):
    cliente = ClienteFalso(mensaje("end_turn", texto("Hola, ¿en qué te ayudo?")))
    respuesta = Agente(cliente, ejecutor).responder("Hola")
    assert respuesta.texto == "Hola, ¿en qué te ayudo?"
    assert respuesta.herramientas == []


def test_busca_en_la_guia_y_devuelve_el_resultado_a_claude(ejecutor):
    cliente = ClienteFalso(
        mensaje("tool_use", herramienta("buscar_guia", {"consulta": "cámara sin imagen"})),
        mensaje("end_turn", texto("Revisa el puerto PoE.")),
    )
    respuesta = Agente(cliente, ejecutor).responder("La cámara no da imagen")

    assert respuesta.herramientas == ["buscar_guia"]
    resultado = cliente.peticiones[1]["messages"][-1]["content"][0]
    assert resultado["tool_use_id"] == "toolu_1"
    assert "Cámara IP sin imagen" in resultado["content"]


def test_flujo_completo_crea_y_escala_ticket(ejecutor):
    entrada = {
        "cliente": "Sede Norte",
        "equipo": "NVR",
        "descripcion": "Disco no detectado",
        "prioridad": "alta",
    }
    cliente = ClienteFalso(
        mensaje("tool_use", herramienta("crear_ticket", entrada)),
        mensaje(
            "tool_use",
            herramienta(
                "actualizar_ticket",
                {"ticket_id": 1, "estado": "escalado", "nota": "Requiere visita"},
            ),
        ),
        mensaje("end_turn", texto("Ticket 1 escalado.")),
    )
    Agente(cliente, ejecutor).responder("El NVR no detecta el disco en Sede Norte")

    ticket = ejecutor.tickets.obtener(1)
    assert ticket["estado"] == "escalado"
    assert ticket["notas"][0]["texto"] == "Requiere visita"


def test_varias_herramientas_vuelven_en_un_solo_mensaje(ejecutor):
    cliente = ClienteFalso(
        mensaje(
            "tool_use",
            herramienta("buscar_guia", {"consulta": "alarma"}, "toolu_1"),
            herramienta("buscar_guia", {"consulta": "huella"}, "toolu_2"),
        ),
        mensaje("end_turn", texto("Listo.")),
    )
    Agente(cliente, ejecutor).responder("Dos problemas")

    resultados = cliente.peticiones[1]["messages"][-1]["content"]
    assert [r["tool_use_id"] for r in resultados] == ["toolu_1", "toolu_2"]


def test_error_de_herramienta_se_informa_a_claude(ejecutor):
    cliente = ClienteFalso(
        mensaje("tool_use", herramienta("consultar_ticket", {"ticket_id": 99})),
        mensaje("end_turn", texto("Ese ticket no existe.")),
    )
    respuesta = Agente(cliente, ejecutor).responder("¿Cómo va el ticket 99?")

    resultado = cliente.peticiones[1]["messages"][-1]["content"][0]
    assert resultado["is_error"] is True
    assert "99" in resultado["content"]
    assert respuesta.texto == "Ese ticket no existe."


def test_herramienta_desconocida_no_rompe_el_ciclo(ejecutor):
    cliente = ClienteFalso(
        mensaje("tool_use", herramienta("borrar_todo", {})),
        mensaje("end_turn", texto("No puedo hacer eso.")),
    )
    Agente(cliente, ejecutor).responder("Borra todo")
    assert cliente.peticiones[1]["messages"][-1]["content"][0]["is_error"] is True


def test_limite_de_pasos_evita_un_ciclo_infinito(ejecutor):
    pasos = [
        mensaje("tool_use", herramienta("buscar_guia", {"consulta": "alarma"}))
        for _ in range(MAX_PASOS + 1)
    ]
    cliente = ClienteFalso(*pasos)
    respuesta = Agente(cliente, ejecutor).responder("Bucle")
    assert respuesta.texto == AVISO_LIMITE
    assert len(cliente.peticiones) == MAX_PASOS


def test_max_tokens_no_deja_herramientas_incompletas_en_el_historial(ejecutor):
    cliente = ClienteFalso(
        mensaje("max_tokens", herramienta("buscar_guia", {})),
        mensaje("end_turn", texto("Ahora sí.")),
    )
    agente = Agente(cliente, ejecutor)
    assert agente.responder("Primera").texto == AVISO_LARGO
    assert all(m["role"] == "user" for m in agente.mensajes)
    assert agente.responder("Segunda").texto == "Ahora sí."


def test_rechazo_devuelve_un_aviso(ejecutor):
    cliente = ClienteFalso(mensaje("refusal"))
    assert Agente(cliente, ejecutor).responder("Algo").texto == AVISO_RECHAZO


def test_pause_turn_continua_la_consulta(ejecutor):
    cliente = ClienteFalso(mensaje("pause_turn"), mensaje("end_turn", texto("Fin.")))
    assert Agente(cliente, ejecutor).responder("Algo").texto == "Fin."
    assert len(cliente.peticiones) == 2


def test_la_conversacion_conserva_el_contexto(ejecutor):
    cliente = ClienteFalso(mensaje("end_turn", texto("Uno")), mensaje("end_turn", texto("Dos")))
    agente = Agente(cliente, ejecutor)
    agente.responder("Primero")
    agente.responder("Segundo")
    assert len(cliente.peticiones[1]["messages"]) == 3


def test_peticion_usa_los_parametros_esperados(ejecutor):
    cliente = ClienteFalso(mensaje("end_turn", texto("Ok")))
    Agente(cliente, ejecutor, modelo="claude-opus-5-5").responder("Hola")
    peticion = cliente.peticiones[0]
    assert peticion["model"] == "claude-opus-5-5"
    assert peticion["fallbacks"] == "default"
    assert "budget_tokens" not in peticion["thinking"]
    assert "tool_choice" not in peticion


def test_esquemas_de_herramientas_son_estrictos_y_serializables():
    for definicion in HERRAMIENTAS:
        esquema = definicion["input_schema"]
        assert definicion["strict"] is True
        assert esquema["additionalProperties"] is False
        assert set(esquema["required"]) == set(esquema["properties"])
    json.dumps(HERRAMIENTAS)
