from sqlalchemy import text

from .database import engine


def migrate():
    with engine.begin() as conn:
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