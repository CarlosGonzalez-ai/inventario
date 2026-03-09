import mysql.connector
import os

host = os.environ.get("MYSQLHOST")
port = int(os.environ.get("MYSQLPORT", 3306))
user = os.environ.get("MYSQLUSER")
password = os.environ.get("MYSQLPASSWORD")
database = os.environ.get("MYSQLDATABASE")

try:
    conexion = mysql.connector.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database
    )
    
    cursor = conexion.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventario (
            numero INT PRIMARY KEY,
            articulo VARCHAR(255),
            inicio INT,
            actual INT,
            foto VARCHAR(255),
            justificacion TEXT,
            utilizados INT
        )
    """)
    
    conexion.commit()
    cursor.close()
    conexion.close()
    
    print("✅ Tabla 'inventario' creada exitosamente")
    
except Exception as e:
    print(f"❌ Error: {e}")
