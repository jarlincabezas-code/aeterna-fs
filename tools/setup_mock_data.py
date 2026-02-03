import sqlite3

def create_mock_db():
    conn = sqlite3.connect('empresa_auditada.db')
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS transacciones")
    cursor.execute("""
        CREATE TABLE transacciones (
            id INTEGER PRIMARY KEY,
            monto REAL,
            fecha TEXT,
            usuario TEXT,
            proveedor TEXT
        )
    """)
    
    # Insertar transacciones normales y algunas sospechosas (Benford Violation)
    # Muchos montos empezando con '9' (anomalía típica de manipulación)
    data = [
        (1, 950.00, "2026-01-20T10:00:00", "admin", "VND_001"),
        (2, 980.50, "2026-01-20T11:30:00", "admin", "VND_001"),
        (3, 45.00, "2026-01-21T09:00:00", "user1", "VND_002"),
        (4, 910.00, "2026-01-21T10:00:00", "admin", "VND_001"),
        (5, 12500.00, "2026-01-22T15:00:00", "manager", "VND_999"), # OUTLIER
    ]
    cursor.executemany("INSERT INTO transacciones VALUES (?,?,?,?,?)", data)
    conn.commit()
    conn.close()
    print("Escena del crimen digital preparada: empresa_auditada.db creada.")

if __name__ == "__main__":
    create_mock_db()