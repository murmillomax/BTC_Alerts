from sqlalchemy import text

from .database import engine


def migrate():
    with engine.begin() as conn:
        # Campos para acceso por correo y recuperación de contraseña
        columns = conn.execute(
            text("PRAGMA table_info(users)")
        ).fetchall()

        user_columns = {column[1] for column in columns}

        new_columns = {
            "login_code": "VARCHAR(10)",
            "login_code_expires": "DATETIME",
            "reset_code": "VARCHAR(10)",
            "reset_code_expires": "DATETIME",
            "login_requested_at": "DATETIME",
            "login_attempts": "INTEGER NOT NULL DEFAULT 0",
            "reset_requested_at": "DATETIME",
            "reset_attempts": "INTEGER NOT NULL DEFAULT 0",
        }

        for column_name, column_type in new_columns.items():
            if column_name not in user_columns:
                conn.execute(
                    text(
                        f"ALTER TABLE users "
                        f"ADD COLUMN {column_name} {column_type}"
                    )
                )
                print(f"Agregada: users.{column_name}")
            else:
                print(f"Ya existe: users.{column_name}")

        # users.password_changed_at
        columns = conn.execute(
            text("PRAGMA table_info(users)")
        ).fetchall()

        user_columns = {column[1] for column in columns}

        if "password_changed_at" not in user_columns:
            conn.execute(
                text("""
                    ALTER TABLE users
                    ADD COLUMN password_changed_at DATETIME
                """)
            )
            print("Agregada: users.password_changed_at")
        else:
            print("Ya existe: users.password_changed_at")
        # users.subscription_started
        columns = conn.execute(
            text("PRAGMA table_info(users)")
        ).fetchall()

        user_columns = {column[1] for column in columns}

        if "subscription_started" not in user_columns:
            conn.execute(
                text(
                    """
                    ALTER TABLE users
                    ADD COLUMN subscription_started DATETIME
                    """
                )
            )
            print("Agregada: users.subscription_started")
        else:
            print("Ya existe: users.subscription_started")

        # users.is_admin
        if "is_admin" not in user_columns:
            conn.execute(
                text(
                    """
                    ALTER TABLE users
                    ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT 0
                    """
                )
            )
            print("Agregada: users.is_admin")
        else:
            print("Ya existe: users.is_admin")

        # payments.approved_at
        columns = conn.execute(
            text("PRAGMA table_info(payments)")
        ).fetchall()

        payment_columns = {column[1] for column in columns}

        if "approved_at" not in payment_columns:
            conn.execute(
                text(
                    """
                    ALTER TABLE payments
                    ADD COLUMN approved_at DATETIME
                    """
                )
            )
            print("Agregada: payments.approved_at")
        else:
            print("Ya existe: payments.approved_at")

        if "user_reported_paid" not in payment_columns:
            conn.execute(text("""
                ALTER TABLE payments
                ADD COLUMN user_reported_paid BOOLEAN NOT NULL DEFAULT 0
            """))
            print("Agregada: payments.user_reported_paid")
        else:
            print("Ya existe: payments.user_reported_paid")

        if "user_reported_paid_at" not in payment_columns:
            conn.execute(text("""
                ALTER TABLE payments
                ADD COLUMN user_reported_paid_at DATETIME
            """))
            print("Agregada: payments.user_reported_paid_at")
        else:
            print("Ya existe: payments.user_reported_paid_at")


if __name__ == "__main__":
    migrate()