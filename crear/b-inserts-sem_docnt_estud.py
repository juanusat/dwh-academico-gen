import json
import os
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

# ---------- Configuración de archivos ----------
BASE_CONFIG = Path("data-configuracion")
BASE_PROCESADA = Path("data-procesada")
BASE_INSERTS = Path("inserts")

SEMESTRES_FILE = BASE_CONFIG / "semestres.csv"
APELLIDOS_FILE = BASE_PROCESADA / "apellidos.csv"
NOMBRES_H_FILE = BASE_PROCESADA / "nombres-hombres.csv"
NOMBRES_M_FILE = BASE_PROCESADA / "nombres-mujeres.csv"
PAISES_FILE = BASE_PROCESADA / "paises.csv"
JSON_FILE = BASE_CONFIG / "facultades_escuelas_cursos.json"
OUTPUT_SQL = BASE_INSERTS / "b-sem-docnt-estud.sql"

# ---------- Constantes ----------
CANT_ALU_MIN = 50
CANT_ALU_MAX = 80
CANT_DOCENTES_CARRERA = 40
SUFIJO_CORREO = "@gmail.com"

# ---------- Carga de datos ----------
def load_list(path):
    if not os.path.exists(path):
        print(f"Error: El archivo '{path}' no fue encontrado.")
        return []
    try:
        with open(path, encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    except Exception as e:
        print(f"Error al leer el archivo '{path}': {e}")
        return []

print("Cargando datos de archivos...")
semestres = load_list(SEMESTRES_FILE)
apellidos = load_list(APELLIDOS_FILE)
nombres_h = load_list(NOMBRES_H_FILE)
nombres_m = load_list(NOMBRES_M_FILE)
paises = load_list(PAISES_FILE)

if not all([semestres, apellidos, nombres_h, nombres_m, paises]):
    print("Error: Faltan archivos de datos esenciales (semestres, nombres, apellidos, paises). Abortando.")
    exit()

try:
    with open(JSON_FILE, encoding="utf-8") as f:
        data = json.load(f)
    facultades = data.get("facultades", {})
    if not facultades:
        print(f"Advertencia: No se encontraron 'facultades' en {JSON_FILE}.")

except FileNotFoundError:
    print(f"Error: El archivo JSON '{JSON_FILE}' no fue encontrado. Abortando.")
    exit()
except json.JSONDecodeError as e:
    print(f"Error al decodificar el archivo JSON '{JSON_FILE}': {e}. Abortando.")
    exit()
except Exception as e:
    print(f"Error inesperado al cargar '{JSON_FILE}': {e}. Abortando.")
    exit()

print("Datos cargados exitosamente.")

dni_usados = set()
email_usados = set()

def generar_nombre(sexo):
    if sexo == 'M':
        lista = nombres_h
    elif sexo == 'F':
        lista = nombres_m
    else:
        raise ValueError("Sexo debe ser 'M' o 'F'")
    
    if len(lista) == 0:
        sys.exit(f"No hay nombres disponibles para sexo '{sexo}'")

    nombres_cantidad = random.choices([1, 2, 3], weights=[0.05, 0.91, 0.04], k=1)[0]

    if len(lista) < nombres_cantidad:
        sys.exit(f"No hay suficientes nombres en la lista para escoger {nombres_cantidad} sin repetición")

    seleccionados = []
    while len(seleccionados) < nombres_cantidad:
        nombre = random.choice(lista)
        if nombre not in seleccionados:
            seleccionados.append(nombre)

    return " ".join(seleccionados)

def generar_dni():
    while True:
        dni = f"{random.randint(0, 99_999_999):08d}"
        if dni not in dni_usados:
            dni_usados.add(dni)
            return dni

def generar_apellidos():
    if not apellidos:
        print("Advertencia: Lista de apellidos vacía. Usando 'ApellidoTemporal'.")
        return "ApellidoTemporal", "ApellidoTemporal"
    return random.choice(apellidos), random.choice(apellidos)

def generar_correo(apepat, apemat, nombres):
    nombre_iniciales = ''.join(n[0].lower() for n in nombres.split() if n)
    base = f"{nombre_iniciales}{apepat.lower()}{apemat.lower()[0]}"
    base = ''.join(filter(str.isalnum, base))

    correo = f"{base}{SUFIJO_CORREO}"
    
    if correo in email_usados:
        for _ in range(100):
            numeros = random.randint(10, 99)
            correo = f"{base}{numeros}{SUFIJO_CORREO}"
            if correo not in email_usados:
                break
        else:
            numeros = random.randint(100, 9999)
            correo = f"{base}{numeros}{SUFIJO_CORREO}"

    email_usados.add(correo)
    return correo

def generar_direccion():
    pref = random.choice(["Jr.", "Ca.", "Av.", "Psj."])
    nombre_lugar = random.choice(paises)
    num = random.randint(100, 1999)
    return f"{pref} {nombre_lugar} {num}"

def generar_fecha_nacimiento(semestre_ingreso):
    año_ingreso = int(semestre_ingreso.split('-')[0])
    edad = random.randint(17, 21)
    año_nacimiento = año_ingreso - edad
    mes = random.randint(1, 12)
    dia = random.randint(1, 28)
    try:
        fecha = datetime(año_nacimiento, mes, dia)
        return fecha.strftime('%Y-%m-%d')
    except ValueError:
        return f"{año_nacimiento}-{mes:02d}-01"

def generar_fecha_semestre(semestre):
    año, ciclo = semestre.split('-')
    año = int(año)
    if ciclo == '1':
        inicio = datetime(año, 3, 17) + timedelta(days=random.randint(0, 7))
        fin = datetime(año, 7, 1) + timedelta(days=random.randint(0, 7))
    else:
        inicio = datetime(año, 8, 12) + timedelta(days=random.randint(0, 7))
        fin = datetime(año, 12, 2) + timedelta(days=random.randint(0, 7))
    return inicio.date(), fin.date()

print(f"Generando archivo SQL: {OUTPUT_SQL}")
try:
    with open(OUTPUT_SQL, 'w', encoding='utf-8') as sqlf:
        sqlf.write("SET client_encoding = 'UTF8';\n\n")

        sqlf.write("-- Inserts para la tabla SEMESTRE\n")
        if not semestres:
            sqlf.write("-- ADVERTENCIA: No se generaron semestres porque la lista estaba vacía.\n")
        for idx, sem in enumerate(semestres):
            try:
                ini, fin = generar_fecha_semestre(sem)
                if idx == len(semestres) - 1: estado = 'A'
                else: estado = 'I'
                sqlf.write(f"INSERT INTO semestre (idsemestre, fecha_inicio, fecha_fin, estado_semestre) VALUES ('{sem}', '{ini}', '{fin}', '{estado}');\n")
            except Exception as e:
                sqlf.write(f"-- ERROR generando semestre {sem}: {e}\n")
        sqlf.write('\n')

        docente_id_counter = 1
        estudiante_id_counter = 1
        current_plan_estudio_id = 1

        sqlf.write("-- Inserts para la tabla DOCENTE\n")
        total_docentes_generados = 0
        num_total_carreras = sum(len(carreras) for carreras in facultades.values())
        total_docentes_estimado = num_total_carreras * CANT_DOCENTES_CARRERA

        print(f"Generando {total_docentes_estimado} docentes...")

        docentes_pool = []
        for i in range(total_docentes_estimado):
            sexo = random.choice(['M', 'F'])
            nombres = generar_nombre(sexo)
            apepat, apemat = generar_apellidos()
            dni = generar_dni()
            correo = generar_correo(apepat, apemat, nombres)
            direccion = generar_direccion()
            tipo_doc = random.choice(['NO', 'PA']) # razon: Nombrado, Parcial
            grado = random.choice(['B', 'M', 'D', 'T']) # razon: Bachiller, Magister, Doctor, Titulado

            docentes_pool.append({
                "id":           docente_id_counter + i,
                "nombres":      nombres,
                "apepat":       apepat,
                "apemat":       apemat,
                "dni":          dni,
                "correo":       correo,
                "sexo":         sexo,
                "direccion":    direccion,
                "tipo_docente": tipo_doc,
                "grado_academico": grado,
                "estado_docente": True
            })
        for doc in docentes_pool:
            sqlf.write(
                f"INSERT INTO docente (iddocente, nombres, apepat, apemat, dni, correo, sexo, direccion, "
                f"tipo_docente, grado_academico, estado_docente) "
                f"VALUES ("
                f"{doc['id']}, "
                f"'{doc['nombres']}', "
                f"'{doc['apepat']}', "
                f"'{doc['apemat']}', "
                f"'{doc['dni']}', "
                f"'{doc['correo']}', "
                f"'{doc['sexo']}', "
                f"'{doc['direccion']}', "
                f"'{doc['tipo_docente']}', "
                f"'{doc['grado_academico']}', "
                f"{str(doc['estado_docente']).upper()}"
                f");\n"
            )
            total_docentes_generados += 1
        print(f"  Total Docentes generados e insertados: {total_docentes_generados}")
        sqlf.write('\n')


        sqlf.write("-- Inserts para la tabla ESTUDIANTE y MATRICULA (inicial)\n")
        if not facultades:
            sqlf.write("-- ADVERTENCIA: No hay facultades definidas en el JSON, no se generarán estudiantes.\n")

        for facultad_nombre, carreras_list in facultades.items():
            if not carreras_list:
                sqlf.write(f"-- ADVERTENCIA: Facultad '{facultad_nombre}' no tiene carreras definidas.\n")
                continue

            for carrera_data in carreras_list:
                carrera_nombre = carrera_data.get('carrera', 'Carrera Desconocida')
                planes_list = carrera_data.get('planes_estudio', [])
                print(f"\n+ Procesando carrera: {carrera_nombre}")

                if not planes_list:
                    sqlf.write(f"-- ADVERTENCIA: Carrera '{carrera_nombre}' no tiene planes de estudio definidos.\n")
                    continue

                for plan_data in planes_list:
                    plan_nombre = plan_data.get('nombre', 'PlanDesconocido')
                    plan_version = plan_data.get('version', '?')
                    plan_label = f"{plan_nombre}-v{plan_version}"
                    print(f"  + Procesando plan: {plan_label} (ID Plan Estudio: {current_plan_estudio_id})")

                    count_h_plan = count_m_plan = total_est_plan = total_mat_plan = 0

                    for sem_ingreso in semestres:
                        n_ingresantes_sem = random.randint(CANT_ALU_MIN, CANT_ALU_MAX)
                        estudiantes_generados_sem = 0

                        for _ in range(n_ingresantes_sem):
                            sexo = random.choice(['M', 'F'])
                            if sexo == 'M': count_h_plan += 1
                            else: count_m_plan += 1

                            nombres = generar_nombre(sexo)
                            apepat, apemat = generar_apellidos()
                            dni = generar_dni()
                            correo = generar_correo(apepat, apemat, nombres)
                            fechanac = generar_fecha_nacimiento(sem_ingreso)
                            direccion = generar_direccion()
                            estado_inicial_alu = 'A'

                            sqlf.write(
                                f"INSERT INTO estudiante (idestudiante, idsemestreing, idplanestudio, nombres, apepat, apemat, dni, correo, sexo, fechanac, direccion, estadoalu) "
                                f"VALUES ({estudiante_id_counter}, '{sem_ingreso}', {current_plan_estudio_id}, '{nombres}', '{apepat}', '{apemat}', '{dni}', '{correo}', '{sexo}', '{fechanac}', '{direccion}', '{estado_inicial_alu}');\n"
                            )
                            estudiantes_generados_sem += 1
                            total_est_plan += 1

                            estudiante_id_counter += 1

                        print(f"    Semestre Ingreso: {sem_ingreso} -> Ingresantes Generados: {estudiantes_generados_sem}")

                    print(f"  -> Plan {plan_label}: Estudiantes Totales Generados: {total_est_plan} (H: {count_h_plan}, M: {count_m_plan})")
                    current_plan_estudio_id += 1

        print(f"\nTotal Estudiantes generados: {estudiante_id_counter - 1}")

except IOError as e:
    print(f"\nError de E/S al escribir en el archivo '{OUTPUT_SQL}': {e}")
except Exception as e:
    print(f"\nOcurrió un error inesperado durante la generación del SQL: {e}")
    import traceback
    traceback.print_exc()
finally:
    print(f"\nArchivo SQL '{OUTPUT_SQL}' generado.")