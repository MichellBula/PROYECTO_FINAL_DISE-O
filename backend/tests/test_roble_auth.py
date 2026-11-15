
from pathlib import Path
import os

from dotenv import load_dotenv
from roble import RobleClient, RobleError, RobleHttpError


# =====================================================
# CONFIGURACIÓN
# =====================================================

RUTA_ENV = Path(__file__).with_name(".env")

load_dotenv(RUTA_ENV)

BASE_URL = os.getenv(
    "ROBLE_BASE_URL",
    "https://roble-api.test-openlab.uninorte.edu.co",
)

CONTRACT_ID = os.getenv("ROBLE_CONTRACT_ID", "").strip()

EMAIL = os.getenv("ROBLE_TEST_EMAIL", "").strip()

PASSWORD = os.getenv("ROBLE_TEST_PASSWORD", "")

NAME = os.getenv(
    "ROBLE_TEST_NAME",
    "Usuario Prueba",
).strip()

CREAR_USUARIO = (
    os.getenv("ROBLE_CREATE_TEST_USER", "false")
    .strip()
    .lower()
    == "true"
)


# =====================================================
# VALIDAR CONFIGURACIÓN
# =====================================================

def validar_configuracion():
    if not CONTRACT_ID or CONTRACT_ID.startswith("COLOCA_"):
        raise ValueError(
            "Configura ROBLE_CONTRACT_ID en backend/tests/.env"
        )

    if not EMAIL or EMAIL.startswith("COLOCA_"):
        raise ValueError(
            "Configura ROBLE_TEST_EMAIL en backend/tests/.env"
        )

    if not PASSWORD or PASSWORD.startswith("COLOCA_"):
        raise ValueError(
            "Configura ROBLE_TEST_PASSWORD en backend/tests/.env"
        )


# =====================================================
# PRUEBA
# =====================================================

def main():
    print()
    print("=" * 55)
    print("PRUEBA DE AUTENTICACIÓN CON ROBLE")
    print("=" * 55)

    try:
        validar_configuracion()

        print()
        print("[1/5] Inicializando cliente Roble...")

        with RobleClient(
            base_url=BASE_URL,
            contract_id=CONTRACT_ID,
        ) as roble:

            print("Cliente Roble inicializado.")

            # -----------------------------------------
            # REGISTRO
            # -----------------------------------------

            print()
            print("[2/5] Comprobando registro de usuario...")

            if CREAR_USUARIO:
                roble.register(
                    email=EMAIL,
                    password=PASSWORD,
                    name=NAME,
                    auto_login=False,
                )

                print("Usuario registrado correctamente.")
            else:
                print(
                    "Registro omitido: se utilizará "
                    "una cuenta existente."
                )

            # -----------------------------------------
            # LOGIN
            # -----------------------------------------

            print()
            print("[3/5] Iniciando sesión...")

            usuario = roble.login(
                email=EMAIL,
                password=PASSWORD,
                persist_session=False,
            )

            print("Login exitoso.")
            print("Nombre:", usuario.name)
            print("Correo:", usuario.email)
            print("User ID:", usuario.user_id)

            # -----------------------------------------
            # PERFIL
            # -----------------------------------------

            print()
            print("[4/5] Consultando perfil...")

            perfil = roble.current_user()

            if perfil.user_id != usuario.user_id:
                raise AssertionError(
                    "El ID del perfil no coincide "
                    "con el usuario autenticado."
                )

            print("Perfil recuperado correctamente.")
            print("User ID confirmado:", perfil.user_id)

            # -----------------------------------------
            # LOGOUT
            # -----------------------------------------

            print()
            print("[5/5] Cerrando sesión...")

            roble.logout()

            if roble.is_logged_in:
                raise AssertionError(
                    "La sesión sigue activa después del logout."
                )

            print("Sesión cerrada correctamente.")

        print()
        print("=" * 55)
        print("PRUEBA COMPLETADA CORRECTAMENTE")
        print("=" * 55)

    except RobleHttpError as error:
        print()
        print("ERROR HTTP DE ROBLE")
        print("Código:", error.status_code)
        print("Mensaje:", error.message)

    except RobleError as error:
        print()
        print("ERROR DE ROBLE")
        print("Mensaje:", error.message)

    except (ValueError, AssertionError) as error:
        print()
        print("ERROR DE CONFIGURACIÓN O VALIDACIÓN")
        print(error)


if __name__ == "__main__":
    main()
