import os
import sys
import subprocess
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

def cargar_env(path_env='.env'):
    if os.path.exists(path_env):
        load_dotenv(path_env)
    else:
        print(f"Advertencia: {path_env} no encontrado, se usarán las variables de entorno.")


def obtener_conexion_bd():
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            dbname=os.getenv('DB_NAME'),
            cursor_factory=RealDictCursor
        )
        print("Conexión a la base de datos establecida.")
        return conn
    except Exception as e:
        print(f"Error al conectar a la base de datos: {e}")
        sys.exit(1)


def ejecutar_archivo_sql(conn, ruta_archivo):
    try:
        with open(ruta_archivo, 'r', encoding='utf-8') as f:
            sql = f.read()
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
        print(f"Archivo SQL ejecutado: {ruta_archivo}")
    except Exception as e:
        print(f"Error al ejecutar archivo SQL {ruta_archivo}: {e}")
        conn.rollback()
        sys.exit(1)


def ejecutar_script_python(ruta_script):
    try:
        print(f"Ejecutando script: {ruta_script}")
        subprocess.run([sys.executable, ruta_script], check=True)
        print(f"Script finalizado correctamente: {ruta_script}")
    except subprocess.CalledProcessError as e:
        print(f"Error al ejecutar el script {ruta_script}: código de retorno {e.returncode}")
        sys.exit(1)


def main():
    cargar_env()
    conn = obtener_conexion_bd()

    # Paso 1: borrar toda la base de datos
    ejecutar_archivo_sql(conn, os.path.join('notas', 'drop_db.sql'))

    # Paso 2: ejecutar scripts de generación de inserts
    ejecutar_script_python(os.path.join('crear', 'a-inserts-carreras_cursos.py'))
    ejecutar_script_python(os.path.join('crear', 'b-inserts-sem_docnt_estud.py'))

    # Paso 3: aplicar inserts generados
    ejecutar_archivo_sql(conn, os.path.join('inserts', 'a-carreras-cursos.sql'))
    ejecutar_archivo_sql(conn, os.path.join('inserts', 'b-sem-docnt-estud.sql'))

    # Paso 4: generar progreso estudiantil
    ejecutar_script_python(os.path.join('crear', 'c-generar-progreso-estudiantil.py'))

    conn.close()
    print("Todos los pasos se completaron correctamente.")

if __name__ == '__main__':
    main()
