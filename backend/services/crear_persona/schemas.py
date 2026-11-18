
import re
from datetime import date

from pydantic import BaseModel, Field, field_validator


class PersonaCrear(BaseModel):

    tipo_documento: str
    numero_documento: str

    primer_nombre: str = Field(max_length=30)
    segundo_nombre: str | None = Field(default=None, max_length=30)
    apellidos: str = Field(max_length=60)

    fecha_nacimiento: date
    genero: str

    correo: str | None = None
    celular: str | None = None

    @field_validator("tipo_documento")
    @classmethod
    def validar_tipo_documento(cls, valor):
        if valor not in ("Cédula", "Tarjeta de identidad"):
            raise ValueError("Tipo de documento no permitido")
        return valor

    @field_validator("numero_documento")
    @classmethod
    def validar_documento(cls, valor):
        if not re.fullmatch(r"[0-9]{1,10}", valor):
            raise ValueError(
                "El documento debe contener máximo 10 dígitos"
            )
        return valor

    @field_validator("primer_nombre", "apellidos")
    @classmethod
    def validar_nombres_obligatorios(cls, valor):
        if not valor.strip() or re.search(r"[0-9]", valor):
            raise ValueError(
                "El campo no puede estar vacío ni contener números"
            )
        return valor.strip()

    @field_validator("segundo_nombre")
    @classmethod
    def validar_segundo_nombre(cls, valor):
        if valor is None or valor == "":
            return None

        if not valor.strip() or re.search(r"[0-9]", valor):
            raise ValueError(
                "El segundo nombre no puede contener números"
            )
        return valor.strip()

    @field_validator("fecha_nacimiento")
    @classmethod
    def validar_fecha(cls, valor):
        if valor > date.today():
            raise ValueError(
                "La fecha de nacimiento no puede ser futura"
            )
        return valor

    @field_validator("genero")
    @classmethod
    def validar_genero(cls, valor):
        opciones = (
            "Masculino",
            "Femenino",
            "No binario",
            "Prefiero no reportar",
        )

        if valor not in opciones:
            raise ValueError("Género no permitido")

        return valor

    @field_validator("correo")
    @classmethod
    def validar_correo(cls, valor):
        if valor is None or valor == "":
            return None

        patron = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"

        if not re.fullmatch(patron, valor):
            raise ValueError(
                "El correo electrónico no tiene un formato válido"
            )

        return valor

    @field_validator("celular")
    @classmethod
    def validar_celular(cls, valor):
        if valor is None or valor == "":
            return None

        if not re.fullmatch(r"[0-9]{10}", valor):
            raise ValueError(
                "El celular debe contener exactamente 10 dígitos"
            )

        return valor
