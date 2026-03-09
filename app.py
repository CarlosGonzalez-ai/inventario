from flask import Flask, request, jsonify, send_from_directory, redirect, url_for
import mysql.connector
from mysql.connector import Error
import os
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.config['CARPETA_FOTOS'] = "static/fotos"
os.makedirs(app.config['CARPETA_FOTOS'], exist_ok=True)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  

def conectar_bd():
    try:
        conexion = mysql.connector.connect(
    host="MYSQLHOST",
    port="MYSQLPORT",
    user="MYSQLUSER",
    password="MYSQLPASSWORD",
    database="MYSQLDATABASE"
        )
        return conexion
    except Error as e:
        print("Error de conexion:", e)
        return None
@app.route("/")
def index():
 return send_from_directory(os.getcwd(), "inventario.html")
@app.route("/cargar", methods=["GET"])
def cargar_datos():
    conexion = conectar_bd()
    if not conexion: 
        return jsonify([])

    cursor = conexion.cursor()
    cursor.execute("SELECT numero, articulo, inicio, actual, foto, justificacion, utilizados FROM inventario ORDER BY numero")
    datos = cursor.fetchall()
    cursor.close()
    conexion.close()

    return jsonify(datos)
@app.route("/guardar", methods=["POST"])
def guardar_datos():
    numero = request.form.get("numero")
    articulo = request.form.get("articulo")
    inicio = request.form.get("inicio") or 0
    actual = request.form.get("actual") or 0
    justificacion = request.form.get("justificacion")
    utilizados = request.form.get("utilizados") or 0

    archivo = request.files.get("foto")
    nombre_foto = None
    if archivo and archivo.filename != "":
        nombre_seguro = secure_filename(archivo.filename)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        nombre_foto = f"{timestamp}_{nombre_seguro}"
        archivo.save(os.path.join(app.config['CARPETA_FOTOS'], nombre_foto))

    conexion = conectar_bd()
    if not conexion:
        return "Error de conexion a la base de datos", 500

    cursor = conexion.cursor()
    cursor.execute("SELECT COUNT(*) FROM inventario WHERE numero=%s", (numero,))
    existe = cursor.fetchone()[0]

    if existe:
        if nombre_foto:
            cursor.execute("""
                UPDATE inventario
                SET articulo=%s, inicio=%s, actual=%s, foto=%s, justificacion=%s, utilizados=%s
                WHERE numero=%s
            """, (articulo, inicio, actual, nombre_foto, justificacion, utilizados, numero))
        else:
            cursor.execute("""
                UPDATE inventario
                SET articulo=%s, inicio=%s, actual=%s, justificacion=%s, utilizados=%s
                WHERE numero=%s
            """, (articulo, inicio, actual, justificacion, utilizados, numero))
    else:
        cursor.execute("""
            INSERT INTO inventario (numero, articulo, inicio, actual, foto, justificacion, utilizados)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (numero, articulo, inicio, actual, nombre_foto, justificacion, utilizados))

    conexion.commit()
    cursor.close()
    conexion.close()

    return "Datos guardados correctamente"

@app.route("/subir_foto", methods=["POST"])
def subir_foto():
    archivo = request.files.get("foto")
    if not archivo or archivo.filename == "":
        return jsonify({"error": "No hay archivo"}), 400

    nombre_seguro = secure_filename(archivo.filename)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    nombre_foto = f"{timestamp}_{nombre_seguro}"
    ruta = os.path.join(app.config['CARPETA_FOTOS'], nombre_foto)
    archivo.save(ruta)

    return jsonify({"nombre": nombre_foto})

@app.route("/static/fotos/<nombre>")
def ver_foto(nombre):
    return send_from_directory(app.config['CARPETA_FOTOS'], nombre)

@app.route("/respaldo", methods=["POST"])
def respaldo():
    conexion = conectar_bd()
    if not conexion:
        return "Error de conexion a la base de datos", 500

    cursor = conexion.cursor()
    cursor.execute("SELECT numero, articulo, inicio, actual, foto, justificacion, utilizados FROM inventario")
    filas = cursor.fetchall()
    cursor.close()
    conexion.close()

    try:
        conexion_respaldo = mysql.connector.connect(
            host="localhost",
            port=3306,
            user="root",
            password="gonzalez30",
            database="almacen_respaldo"
        )
        cursor_respaldo = conexion_respaldo.cursor()
        for fila in filas:
            cursor_respaldo.execute("""
                INSERT INTO backup (numero, articulo, inicio, actual, foto, justificacion, utilizados)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, fila)
        conexion_respaldo.commit()
        cursor_respaldo.close()
        conexion_respaldo.close()
    except Error as e:
        print("Error respaldo:", e)
        return "Error al generar respaldo", 500

    return "Respaldo completado"
@app.route("/actualizar_resultados", methods=["POST"])
def actualizar_resultados():
    conexion = conectar_bd()
    if not conexion:
        return "Error de conexion a la base de datos", 500

    cursor = conexion.cursor()
    cursor.execute("SELECT numero, articulo, actual FROM inventario")
    filas = cursor.fetchall()
    cursor.close()
    conexion.close()

    try:
        conexion_resultados = mysql.connector.connect(
            host="localhost",
            port=3306,
            user="root",
            password="gonzalez30",
            database="almacen_resultados"
        )
        cursor_result = conexion_resultados.cursor()
        cursor_result.execute("TRUNCATE TABLE resumen")
        for fila in filas:
            cursor_result.execute("INSERT INTO resumen (numero, articulo, disponible) VALUES (%s, %s, %s)", fila)
        conexion_resultados.commit()
        cursor_result.close()
        conexion_resultados.close()
    except Error as e:
        print("Error actualizar resultados:", e)
        return "Error al actualizar resultados", 500

    return "Resultados actualizados"
@app.route("/eliminar", methods=["POST"])
def eliminar():
    datos = request.get_json()
    numero = datos.get("numero")

    conexion = conectar_bd()
    if not conexion:
        return jsonify({"status": False, "error": "Error de conexion"}), 500

    cursor = conexion.cursor()

    cursor.execute("SELECT foto FROM inventario WHERE numero=%s", (numero,))
    foto = cursor.fetchone()
    if foto and foto[0]:
        ruta_foto = os.path.join(app.config['CARPETA_FOTOS'], foto[0])
        if os.path.exists(ruta_foto):
            os.remove(ruta_foto)

    cursor.execute("DELETE FROM inventario WHERE numero=%s", (numero,))
    conexion.commit()
    cursor.close()
    conexion.close()

    return jsonify({"status": True})

    if __name__ == "__main__":
     import os
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)