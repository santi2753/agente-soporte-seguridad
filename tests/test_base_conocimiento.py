from pathlib import Path

from soporte_agente.base_conocimiento import BaseConocimiento, normalizar

CARPETA_GUIAS = Path(__file__).resolve().parent.parent / "conocimiento"


def test_normalizar_quita_tildes_y_palabras_vacias():
    assert normalizar("La Cámara no da imagen") == ["camara", "da", "imagen"]


def test_buscar_encuentra_la_seccion_mas_relevante():
    base = BaseConocimiento(CARPETA_GUIAS)
    resultados = base.buscar("camara sin imagen")
    assert resultados[0].titulo == "Cámara IP sin imagen o desconectada"


def test_buscar_funciona_entre_guias():
    base = BaseConocimiento(CARPETA_GUIAS)
    assert base.buscar("huella biometrico")[0].guia == "control_acceso"
    assert base.buscar("disco duro no graba")[0].guia == "grabadores"


def test_buscar_sin_coincidencias_devuelve_lista_vacia():
    assert BaseConocimiento(CARPETA_GUIAS).buscar("xyzzy") == []


def test_buscar_respeta_el_limite():
    assert len(BaseConocimiento(CARPETA_GUIAS).buscar("revisa", limite=2)) == 2
