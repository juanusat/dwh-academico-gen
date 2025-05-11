import json
import csv
import os
from collections import defaultdict
from pathlib import Path

def main():
    
    CURSOS_DIR = Path("data-configuracion")
    sql_filename = Path("inserts") / "a-carreras-cursos.sql"

    config_file = Path("data-configuracion") / "facultades_escuelas_cursos.json"
    
    try:
        with config_file.open(encoding='utf-8') as f:
            raw = json.load(f)
    except FileNotFoundError:
        print(f"Error: El archivo '{config_file}' no fue encontrado.")
        return
    except json.JSONDecodeError:
        print(f"Error: El archivo '{config_file}' no es un JSON válido.")
        return

    data = raw.get('facultades', raw.get('facultades', {}))

    career_courses = defaultdict(dict)
    course_details = {}
    common_course_details = defaultdict(set)
    course_name_to_code_map = {}

    print("Procesando archivos CSV...")
    for faculty, careers in data.items():
        for carr in careers:
            career_name = carr['carrera']
            for plan in carr['planes_estudio']:
                suffix = plan['cursos']
                filename = CURSOS_DIR / f"cursos_{suffix}.csv"
                if not filename.is_file():
                    print(f"¡Advertencia! Archivo no encontrado, se omitirá: {filename}")
                    continue
                try:
                    with open(filename, mode='r', encoding='utf-8') as csvfile:
                        header_line = csvfile.readline()
                        headers = [h.strip() for h in header_line.strip().split(',')]
                        csvfile.seek(0)

                        reader = csv.DictReader(csvfile)
                        required_headers = ['CODIGO', 'NOMBRE', 'CICLO', 'OBLIGATORIO', 'CREDITOS', 'H_TEORICAS']
                        if not all(h in reader.fieldnames for h in required_headers):
                            print(f"¡Advertencia! Faltan columnas requeridas en {filename}. Columnas encontradas: {reader.fieldnames}")
                            continue

                        for row in reader:
                            code = row.get('CODIGO', '').strip()
                            if not code: continue

                            raw_name = row.get('NOMBRE', 'SIN NOMBRE').strip()
                            cleaned_name = raw_name.replace("'", "''")
                            ciclo_str = row.get('CICLO', '0').strip()
                            creditos_str = row.get('CREDITOS', '0').strip()
                            h_teoricas_str = row.get('H_TEORICAS', '0').strip()
                            h_practicas_str = row.get('H_PRACTICAS', '0').strip()
                            prereq_str = row.get('PREREQUISITO', '').strip()
                            obligatorio_str = row.get('OBLIGATORIO', 'FALSE').strip().upper()

                            try:
                                ciclo = int(ciclo_str) if ciclo_str else 0
                                creditos = int(creditos_str) if creditos_str else 0
                                h_teorica = int(h_teoricas_str) if h_teoricas_str else 0
                                h_practica = int(h_practicas_str) if h_practicas_str else 0
                            except ValueError as e:
                                print(f"¡Advertencia! Error de conversión de número en {filename}, fila con código {code}: {e}. Usando 0.")
                                ciclo = ciclo if 'ciclo' in locals() else 0
                                creditos = creditos if 'creditos' in locals() else 0
                                h_teorica = h_teorica if 'h_teorica' in locals() else 0
                                h_practica = h_practica if 'h_practica' in locals() else 0


                            if code not in course_details:
                                prereq_names = [name.strip() for name in prereq_str.split('-') if name.strip()]

                                obligator = obligatorio_str == 'TRUE'
                                course_details[code] = {
                                    'codcurso': code,
                                    'nomcurso': cleaned_name,
                                    'creditos': creditos,
                                    'h_teorica': h_teorica,
                                    'h_practica': h_practica,
                                    'tipo_curso': 'TRUE' if obligator else 'FALSE',
                                    'prerequisitos': prereq_names
                                }
                                course_name_to_code_map[raw_name] = code

                            career_courses[career_name][code] = ciclo
                except FileNotFoundError:
                    print(f"¡Advertencia! Archivo no encontrado al intentar abrir de nuevo: {filename}")
                    continue
                except Exception as e:
                    print(f"Error procesando el archivo {filename}: {e}")
                    continue

    careers = list(career_courses.keys())
    print("\n=== Cursos en común entre carreras ===")
    for i in range(len(careers)):
        for j in range(i + 1, len(careers)):
            c1, c2 = careers[i], careers[j]
            common = set(career_courses[c1].keys()) & set(career_courses[c2].keys())

            for code in sorted(common):
                common_course_details[code].add(
                    f"{c1} [Ciclo {career_courses[c1][code]}]"
                )
                common_course_details[code].add(
                    f"{c2} [Ciclo {career_courses[c2][code]}]"
                )

    fac_id_map = {}
    esc_id_map = {}
    plan_estudio_map = {}
    cur_id_map = {}

    try:
        print(f"\nGenerando archivo SQL: {sql_filename}")

        sql_filename.parent.mkdir(parents=True, exist_ok=True)
        sql_filename.write_text("", encoding="utf-8")

        with open(sql_filename, 'w', encoding='utf-8') as sqlf:
            sqlf.write("-- Inserts para facultad\n")
            fid = 1
            for faculty in data:
                fac_name_sql = faculty.replace("'", "''")
                sqlf.write(f"INSERT INTO facultad (idfacultad, nomfacultad) VALUES ({fid}, '{fac_name_sql}');\n")
                fac_id_map[faculty] = fid
                fid += 1
            sqlf.write("\n")

            sqlf.write("-- Inserts para escuela\n")
            eid = 1
            for faculty, careers_list in data.items():
                for carr in careers_list:
                    esc_name = carr['carrera']
                    esc_name_sql = esc_name.replace("'", "''")
                    idf = fac_id_map[faculty]
                    sqlf.write(f"INSERT INTO escuela (idescuela, nomescuela, idfacultad) VALUES ({eid}, '{esc_name_sql}', {idf});\n")
                    esc_id_map[esc_name] = eid
                    eid += 1
            sqlf.write("\n")

            sqlf.write("-- Inserts para plan_estudio\n")
            pid = 1
            for faculty, careers_list in data.items():
                 for carr in careers_list:
                    esc_name = carr['carrera']
                    if esc_name not in esc_id_map:
                        print(f"¡Advertencia! No se encontró ID para la escuela '{esc_name}' al crear planes de estudio. Omitiendo planes para esta escuela.")
                        continue

                    esc_id = esc_id_map[esc_name]
                    for plan in carr['planes_estudio']:
                        nombre = plan['nombre'].replace("'", "''")
                        version = plan['version'].replace("'", "''")
                        plan_key = (esc_name, plan['nombre'], plan['version'])
                        sqlf.write(
                            f"INSERT INTO plan_estudio (idplanestudio, idescuela, nombre, version) "
                            f"VALUES ({pid}, {esc_id}, '{nombre}', '{version}');\n"
                        )
                        plan_estudio_map[plan_key] = pid
                        pid += 1
            sqlf.write("\n")

            sqlf.write("-- Inserts para curso\n")
            cid = 1
            sorted_course_codes = sorted(course_details.keys())
            for code in sorted_course_codes:
                det = course_details[code]
                cred_val = det.get('creditos', 0)
                ht_val = det.get('h_teorica', 0)
                hp_val = det.get('h_practica', 0)
                tipo_val = det.get('tipo_curso', 'FALSE')

                sqlf.write(
                    f"INSERT INTO curso (idcurso, codcurso, nomcurso, creditos, h_teorica, h_practica, tipo_curso) "
                    f"VALUES ({cid}, '{det['codcurso']}', '{det['nomcurso']}', {cred_val}, {ht_val}, {hp_val}, {tipo_val});\n"
                )
                cur_id_map[code] = cid
                cid += 1
            sqlf.write("\n")

            sqlf.write("-- Inserts para curso_curso (Prerrequisitos)\n")
            for code, details in course_details.items():
                if code not in cur_id_map:
                    print(f"¡Advertencia! Código de curso '{code}' no encontrado en cur_id_map al procesar prerrequisitos.")
                    continue

                current_course_id = cur_id_map[code]
                prereq_names = details.get('prerequisitos', [])

                for prereq_name in prereq_names:
                    prereq_code = course_name_to_code_map.get(prereq_name)

                    if not prereq_code:
                        print(f"¡Advertencia! Nombre de prerrequisito '{prereq_name}' no encontrado en el mapa para curso '{details['nomcurso']}' ({code}). Omitiendo este prerrequisito.")
                        continue

                    prereq_course_id = cur_id_map.get(prereq_code)

                    if not prereq_course_id:
                        print(f"¡Advertencia! ID de curso no encontrado para código de prerrequisito '{prereq_code}' (nombre: '{prereq_name}'). Omitiendo.")
                        continue

                    sqlf.write(f"INSERT INTO curso_curso (cursoid, curso_prereqid) VALUES ({current_course_id}, {prereq_course_id});\n")
            sqlf.write("\n")

            sqlf.write("-- Inserts para plan_curso\n")
            pcid = 1
            for faculty, careers_list in data.items():
                for carr in careers_list:
                    esc_name = carr['carrera']
                    for plan in carr['planes_estudio']:
                        plan_key = (esc_name, plan['nombre'], plan['version'])
                        if plan_key not in plan_estudio_map:
                            print(f"¡Advertencia! No se encontró ID para el plan {plan_key}. Omitiendo cursos de este plan.")
                            continue

                        peid = plan_estudio_map[plan_key]
                        suffix = plan['cursos']
                        filename = CURSOS_DIR / f"cursos_{suffix}.csv"
                        if not filename.is_file():
                            print(f"¡Advertencia! Archivo no encontrado, se omitirá: {filename}")
                            continue
                        try:
                            with open(filename, mode='r', encoding='utf-8') as csvfile:
                                reader = csv.DictReader(csvfile)
                                for row in reader:
                                    code = row.get('CODIGO','').strip()
                                    ciclo_str = row.get('CICLO', '').strip()

                                    if not code or not ciclo_str: continue 
                                    try:
                                        ciclo = int(ciclo_str)
                                    except ValueError:
                                        print(f"¡Advertencia! Valor de ciclo no numérico '{ciclo_str}' en {filename} para curso {code}. Omitiendo esta entrada de plan_curso.")
                                        continue

                                    if code not in cur_id_map:
                                        print(f"¡Advertencia! Código de curso '{code}' de {filename} no encontrado en cur_id_map al crear plan_curso. Omitiendo.")
                                        continue

                                    curid = cur_id_map[code]
                                    sqlf.write(
                                        f"INSERT INTO plan_curso (idplancurso, idplanestudio, idcurso, ciclo) "
                                        f"VALUES ({pcid}, {peid}, {curid}, {ciclo});\n"
                                    )
                                    pcid += 1
                        except FileNotFoundError:
                            continue
                        except Exception as e:
                            print(f"Error procesando {filename} para plan_curso: {e}")
                            continue
            sqlf.write("\n")

    except IOError as e:
        print(f"Error de E/S al escribir en el archivo SQL {sql_filename}: {e}")
        return
    except KeyError as e:
        print(f"Error de clave no encontrada: {e}. Verifica que los nombres en el JSON coincidan con las claves usadas.")
        return
    except Exception as e:
        print(f"Ocurrió un error inesperado durante la generación del SQL: {e}")
        import traceback
        traceback.print_exc()
        return


    print("\n=== Detalles de Cursos Comunes ===")
    sorted_common_codes = sorted(
        common_course_details.keys(),
        key=lambda code: course_details.get(code, {}).get('nomcurso', code)
    )

    for code in sorted_common_codes:
        details = course_details.get(code)
        if details:
            print(f"{code}, {details['nomcurso']}")
            careers_set = common_course_details.get(code, set())
            for career_ciclo in sorted(list(careers_set)):
                print(f"     {career_ciclo}")
            print()
        else:
            print(f"¡Advertencia! Detalles no encontrados para el código de curso común: {code}")

    print(f"Proceso completado. Archivo SQL generado: {sql_filename}")

if __name__ == '__main__':
    main()