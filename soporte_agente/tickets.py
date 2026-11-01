"""Persistencia de tickets de soporte en SQLite."""

import sqlite3
import threading
from datetime import datetime, timezone

PRIORIDADES = ("baja", "media", "alta")
ESTADOS = ("abierto", "en_progreso", "escalado", "resuelto")

ESQUEMA = """
CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente TEXT NOT NULL,
    equipo TEXT NOT NULL,
    descripcion TEXT NOT NULL,
    prioridad TEXT NOT NULL,
    estado TEXT NOT NULL DEFAULT 'abierto',
    creado_en TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS notas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER NOT NULL REFERENCES tickets(id),
    texto TEXT NOT NULL,
    creado_en TEXT NOT NULL
);
"""


class TicketNoEncontrado(Exception):
    pass


def _ahora() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class RepositorioTickets:
    def __init__(self, ruta: str = ":memory:"):
        # La API web atiende peticiones en varios hilos.
        self._conexion = sqlite3.connect(ruta, check_same_thread=False)
        self._conexion.row_factory = sqlite3.Row
        self._conexion.executescript(ESQUEMA)
        self._candado = threading.Lock()

    def crear(self, cliente: str, equipo: str, descripcion: str, prioridad: str) -> int:
        if prioridad not in PRIORIDADES:
            raise ValueError(f"Prioridad inválida: {prioridad}")
        with self._candado, self._conexion:
            cursor = self._conexion.execute(
                "INSERT INTO tickets (cliente, equipo, descripcion, prioridad, creado_en) "
                "VALUES (?, ?, ?, ?, ?)",
                (cliente, equipo, descripcion, prioridad, _ahora()),
            )
        return cursor.lastrowid

    def obtener(self, ticket_id: int) -> dict:
        with self._candado:
            fila = self._conexion.execute(
                "SELECT * FROM tickets WHERE id = ?", (ticket_id,)
            ).fetchone()
            if fila is None:
                raise TicketNoEncontrado(f"No existe el ticket {ticket_id}")
            notas = self._conexion.execute(
                "SELECT texto, creado_en FROM notas WHERE ticket_id = ? ORDER BY id",
                (ticket_id,),
            ).fetchall()
        return {**dict(fila), "notas": [dict(nota) for nota in notas]}

    def actualizar(self, ticket_id: int, estado: str, nota: str) -> dict:
        if estado not in ESTADOS:
            raise ValueError(f"Estado inválido: {estado}")
        with self._candado, self._conexion:
            cursor = self._conexion.execute(
                "UPDATE tickets SET estado = ? WHERE id = ?", (estado, ticket_id)
            )
            if cursor.rowcount == 0:
                raise TicketNoEncontrado(f"No existe el ticket {ticket_id}")
            self._conexion.execute(
                "INSERT INTO notas (ticket_id, texto, creado_en) VALUES (?, ?, ?)",
                (ticket_id, nota, _ahora()),
            )
        return self.obtener(ticket_id)

    def listar(self) -> list[dict]:
        with self._candado:
            filas = self._conexion.execute(
                "SELECT * FROM tickets ORDER BY id DESC"
            ).fetchall()
        return [dict(fila) for fila in filas]
