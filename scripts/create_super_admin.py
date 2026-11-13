from getpass import getpass

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.core.security import hash_password
from app.models.user_role import Roles               
from app.infrastructure.database.session import SessionLocal  
from app.models.usuarios import User   

def solicitar_datos() -> dict:
    """Solicita los datos iniciales del SUPER_ADMIN."""

    print("\n=== CREACIÓN DEL SUPER_ADMIN ===\n")

    nombre = input("Nombres: ").strip()
    apellido = input("Apellidos: ").strip()
    correo = input("Correo electrónico: ").strip().lower()
    telefono = input("Teléfono (opcional): ").strip()
    direccion = input("Dirección (opcional): ").strip()

    if not nombre or not apellido:
        raise ValueError("Los nombres y apellidos son obligatorios.")

    if "@" not in correo or "." not in correo.split("@")[-1]:
        raise ValueError("Debes ingresar un correo electrónico válido.")

    if len(nombre) > 50 or len(apellido) > 50:
        raise ValueError("Nombres y apellidos: máximo 50 caracteres.")

    if len(correo) > 60:
        raise ValueError("El correo admite máximo 60 caracteres.")

    if len(telefono) > 50 or len(direccion) > 50:
        raise ValueError("Teléfono y dirección: máximo 50 caracteres.")

    password = getpass("Crea una contraseña (mínimo 12 caracteres): ")
    confirmation = getpass("Confirma la contraseña: ")

    if len(password) < 12:
        raise ValueError("La contraseña debe tener al menos 12 caracteres.")

    if password != confirmation:
        raise ValueError("Las contraseñas no coinciden.")

    return {
        "nombre": nombre,
        "apellido": apellido,
        "correo": correo,
        "telefono": telefono or None,
        "direccion": direccion or None,
        "password": password,
    }

def crear_super_admin() -> None:
    """Crea el SUPER_ADMIN si todavía no existe."""

    db = SessionLocal()

    try:
        # 1. Comprobar si ya existe un SUPER_ADMIN.
        existing_admin = db.scalar(
            select(User).where(User.tipo_rol == Roles.SUPER_ADMIN)
        )

        if existing_admin:
            print(
                "\nNo se puede crear otro SUPER_ADMIN."
                "\nYa existe uno registrado en Harmony Spa."
            )
            return

        # 2. Solicitar los datos.
        datos = solicitar_datos()

        # 3. Comprobar si el correo ya está registrado.
        existing_email = db.scalar(
            select(User).where(User.correo == datos["correo"])
        )

        if existing_email:
            raise ValueError("Ese correo electrónico ya está registrado.")

        # 4. Convertir la contraseña en un hash Argon2id.
        password_hash = hash_password(datos["password"])

        # 5. Crear el usuario con el rol SUPER_ADMIN.
        super_admin = User(
            nombre=datos["nombre"],
            apellido=datos["apellido"],
            correo=datos["correo"],
            telefono=datos["telefono"],
            direccion=datos["direccion"],
            password_hash=password_hash,
            tipo_rol=Roles.SUPER_ADMIN,
            is_active=True,
        )

        # 6. Guardar el usuario en MySQL.
        db.add(super_admin)
        db.commit()
        db.refresh(super_admin)

        print("\nSUPER_ADMIN creado correctamente.")
        print(f"Identificador: {super_admin.id_usuario}")
        print(f"Correo: {super_admin.correo}")
        print("La contraseña se almacenó mediante Argon2id.")

    except IntegrityError as error:
        db.rollback()
        print(
            "\nNo se pudo crear el SUPER_ADMIN."
            "\nLa base de datos rechazó el registro por una restricción "
            "(rol inexistente en la tabla roles, otro SUPER_ADMIN ya creado "
            "o datos duplicados)."
            f"\nDetalle: {error.orig}"
        )

    except (ValueError, SQLAlchemyError) as error:
        db.rollback()
        print(f"\nNo se pudo completar la operación: {error}")

    finally:
        db.close()


if __name__ == "__main__":
    crear_super_admin()