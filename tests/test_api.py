from fastapi.testclient import TestClient

from conftest import ClienteFalso, herramienta, mensaje, texto
from soporte_agente.api import crear_app


def crear_cliente_http(ejecutor, *respuestas):
    falso = ClienteFalso(*respuestas)
    return TestClient(crear_app(ejecutor, lambda: falso))


def test_chat_crea_sesion_y_la_conserva(ejecutor):
    http = crear_cliente_http(
        ejecutor,
        mensaje("end_turn", texto("Uno")),
        mensaje("end_turn", texto("Dos")),
    )
    primera = http.post("/chat", json={"mensaje": "Hola"}).json()
    segunda = http.post(
        "/chat", json={"mensaje": "Sigo", "sesion_id": primera["sesion_id"]}
    ).json()
    assert primera["respuesta"] == "Uno"
    assert segunda["sesion_id"] == primera["sesion_id"]
    assert segunda["respuesta"] == "Dos"


def test_chat_rechaza_sesion_inexistente(ejecutor):
    http = crear_cliente_http(ejecutor)
    respuesta = http.post("/chat", json={"mensaje": "Hola", "sesion_id": "no-existe"})
    assert respuesta.status_code == 404


def test_chat_rechaza_mensaje_vacio(ejecutor):
    http = crear_cliente_http(ejecutor)
    assert http.post("/chat", json={"mensaje": ""}).status_code == 422


def test_ticket_creado_por_el_agente_se_ve_en_la_api(ejecutor):
    entrada = {
        "cliente": "Sede Norte",
        "equipo": "Cámara 3",
        "descripcion": "Sin imagen",
        "prioridad": "media",
    }
    http = crear_cliente_http(
        ejecutor,
        mensaje("tool_use", herramienta("crear_ticket", entrada)),
        mensaje("end_turn", texto("Ticket creado.")),
    )
    respuesta = http.post("/chat", json={"mensaje": "Abre un ticket"}).json()

    assert respuesta["herramientas"] == ["crear_ticket"]
    assert http.get("/tickets").json()[0]["cliente"] == "Sede Norte"
    assert http.get("/tickets/1").json()["equipo"] == "Cámara 3"


def test_sin_credenciales_chat_responde_503_y_tickets_siguen_activos(ejecutor, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
    http = TestClient(crear_app(ejecutor))
    assert http.post("/chat", json={"mensaje": "Hola"}).status_code == 503
    assert http.get("/tickets").status_code == 200


def test_ticket_inexistente_devuelve_404(ejecutor):
    assert crear_cliente_http(ejecutor).get("/tickets/99").status_code == 404
