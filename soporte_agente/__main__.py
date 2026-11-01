"""Chat por consola: python -m soporte_agente"""

import anthropic

from .agente import Agente
from .configuracion import CredencialesFaltantes, crear_cliente_claude, crear_ejecutor


def main() -> None:
    try:
        cliente = crear_cliente_claude()
    except CredencialesFaltantes as error:
        print(f"Error: {error}")
        return

    agente = Agente(cliente, crear_ejecutor())
    print("Mesa de ayuda de seguridad electrónica. Escribe 'salir' para terminar.\n")

    while True:
        texto = input("Tú: ").strip()
        if texto.lower() == "salir":
            return
        if not texto:
            continue
        try:
            respuesta = agente.responder(texto)
        except anthropic.AuthenticationError:
            print("Error: revisa tu ANTHROPIC_API_KEY.")
            return
        except anthropic.RateLimitError:
            print("Error: límite de uso alcanzado. Espera un momento.")
            continue
        except anthropic.APIConnectionError:
            print("Error: no hay conexión con la API.")
            continue
        except anthropic.APIStatusError as error:
            print(f"Error de la API ({error.status_code}): {error.message}")
            continue
        if respuesta.herramientas:
            print(f"[herramientas: {', '.join(respuesta.herramientas)}]")
        print(f"Agente: {respuesta.texto}\n")


if __name__ == "__main__":
    main()
