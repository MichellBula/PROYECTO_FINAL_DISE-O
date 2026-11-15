
import argparse
import getpass
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from roble import RobleClient, RobleError, RobleHttpError


# ============================================
# CONFIGURACIÓN
# ============================================

CARPETA_ACTUAL = Path(__file__).resolve().parent
load_dotenv(CARPETA_ACTUAL / ".env")

BASE_URL = os.getenv("ROBLE_BASE_URL", "").strip()
CONTRACT_ID = os.getenv("ROBLE_CONTRACT_ID", "").strip()

EMAIL = os.getenv("ROBLE_TEST_EMAIL", "").strip()
PASSWORD = os.getenv("ROBLE_TEST_PASSWORD", "")
NAME = os.getenv("ROBLE_TEST_NAME", "Usuario Prueba").strip()


def validar_configuracion():
    campos = {
        "ROBLE_BASE_URL": BASE_URL,
        "ROBLE_CONTRACT_ID": CONTRACT_ID,
        "ROBLE_TEST_EMAIL": EMAIL,
        "ROBLE_TEST_PASSWORD": PASSWORD,
        "ROBLE_TEST_NAME": NAME,
    }

    for nombre, valor in campos.items():
        if not valor or valor.startswith("COLOCA_AQUI"):
            raise ValueError(
                f"Falta configurar {nombre} en backend/tests/.env"
            )

    if not BASE_URL.startswith("https://"):
        raise ValueError(
            "ROBLE_BASE_URL debe comenzar con https://"
        )


# ============================================
# OPERACIONES
# ============================================

def solicitar_registro(roble):
    print()
    print("[1] SOLICITAR REGISTRO CON VERIFICACIÓN")

    roble.register_with_verification(
        email=EMAIL,
        password=PASSWORD,
        name=NAME,
    )

    print()
    print("Solicitud aceptada por Roble.")
    print("Revisa tu bandeja de entrada y correo no deseado.")
    print("La cuenta aún NO está creada.")
    print("Debes confirmar el código recibido.")


def verificar_correo(roble):
    print()
    print("[2] VERIFICAR CORREO ELECTRÓNICO")

    codigo = getpass.getpass(
        "Introduce el código recibido por correo: "
    ).strip()

    if not codigo:
        raise ValueError("El código no puede estar vacío.")

    roble.verify_email(
        email=EMAIL,
        code=codigo,
    )

    print()
    print("¡Correo verificado correctamente!")
    print("La cuenta ha sido creada en Roble.")
    print("Ya puedes iniciar sesión.")


def iniciar_sesion(roble):
    print()
    print("[3] PRUEBA DE INICIO DE SESIÓN")

    usuario = roble.login(
        email=EMAIL,
        password=PASSWORD,
        persist_session=False,
    )

    print()
    print("¡LOGIN EXITOSO!")
    print("Nombre:", usuario.name)
    print("Correo:", usuario.email)
    print("User ID:", usuario.user_id)

    perfil = roble.current_user()

    if perfil.user_id != usuario.user_id:
        raise RuntimeError(
            "El perfil no coincide con el usuario autenticado."
        )

    print("Perfil verificado correctamente.")

    roble.logout()

    print("Sesión cerrada correctamente.")
    print()
    print("PRUEBA DE AUTENTICACIÓN COMPLETADA.")


def reenviar_codigo(roble):
    print()
    print("[OPCIONAL] REENVIAR CÓDIGO")

    roble.resend_code(email=EMAIL)

    print("Solicitud de reenvío aceptada.")
    print("Revisa tu correo electrónico.")


# ============================================
# PROGRAMA PRINCIPAL
# ============================================

def main():
    parser = argparse.ArgumentParser(
        description="Registro con verificación de correo en Roble"
    )

    parser.add_argument(
        "accion",
        choices=["solicitar", "verificar", "entrar", "reenviar"],
        help="Operación de autenticación que deseas realizar",
    )

    argumentos = parser.parse_args()

    try:
        validar_configuracion()

        print()
        print("=" * 55)
        print("AUTENTICACIÓN ROBLE - GESTIÓN DE DATOS PERSONALES")
        print("=" * 55)

        with RobleClient(
            base_url=BASE_URL,
            contract_id=CONTRACT_ID,
        ) as roble:

            if argumentos.accion == "solicitar":
                solicitar_registro(roble)

            elif argumentos.accion == "verificar":
                verificar_correo(roble)

            elif argumentos.accion == "entrar":
                iniciar_sesion(roble)

            elif argumentos.accion == "reenviar":
                reenviar_codigo(roble)

    except RobleHttpError as error:
        print()
        print("ERROR HTTP DE ROBLE")
        print("Código:", error.status_code)
        print("Mensaje:", error.message)

        if error.status_code == 429:
            print(
                "Roble está limitando las solicitudes. "
                "No repitas la operación inmediatamente."
            )

        elif error.status_code == 400:
            print(
                "Revisa los datos o si el código "
                "de verificación ha caducado."
            )

        elif error.status_code == 401:
            print(
                "Las credenciales fueron rechazadas."
            )

        sys.exit(1)

    except (RobleError, ValueError, RuntimeError) as error:
        print()
        print("ERROR:")
        print(error)
        sys.exit(1)


if __name__ == "__main__":
    main()
