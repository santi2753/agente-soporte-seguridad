import pytest

from soporte_agente.tickets import RepositorioTickets, TicketNoEncontrado


@pytest.fixture
def tickets():
    return RepositorioTickets()


def test_crear_y_obtener(tickets):
    ticket_id = tickets.crear("Sede Norte", "Cámara 3", "Sin imagen", "alta")
    ticket = tickets.obtener(ticket_id)
    assert ticket["cliente"] == "Sede Norte"
    assert ticket["estado"] == "abierto"
    assert ticket["notas"] == []


def test_actualizar_cambia_estado_y_guarda_nota(tickets):
    ticket_id = tickets.crear("Sede Norte", "NVR", "No graba", "media")
    ticket = tickets.actualizar(ticket_id, "escalado", "Requiere visita")
    assert ticket["estado"] == "escalado"
    assert ticket["notas"][0]["texto"] == "Requiere visita"


def test_prioridad_invalida_no_crea_ticket(tickets):
    with pytest.raises(ValueError):
        tickets.crear("Sede Norte", "NVR", "No graba", "urgente")
    assert tickets.listar() == []


def test_estado_invalido_no_modifica_ticket(tickets):
    ticket_id = tickets.crear("Sede Norte", "NVR", "No graba", "media")
    with pytest.raises(ValueError):
        tickets.actualizar(ticket_id, "cerrado", "nota")
    assert tickets.obtener(ticket_id)["estado"] == "abierto"


def test_ticket_inexistente(tickets):
    with pytest.raises(TicketNoEncontrado):
        tickets.obtener(99)
    with pytest.raises(TicketNoEncontrado):
        tickets.actualizar(99, "resuelto", "nota")


def test_entrada_maliciosa_no_altera_la_base(tickets):
    malicioso = "x'); DROP TABLE tickets;--"
    ticket_id = tickets.crear(malicioso, "NVR", "No graba", "baja")
    assert tickets.obtener(ticket_id)["cliente"] == malicioso
