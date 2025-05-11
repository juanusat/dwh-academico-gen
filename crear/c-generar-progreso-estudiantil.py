import os
import random
import time
from datetime import datetime, timedelta
from collections import defaultdict
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv


def main():
    start_time = datetime.now()
    print("🕒 Inicio del script:", start_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3])

    load_dotenv()

    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        dbname=os.getenv("DB_NAME"),
    )
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # 0.1 Sincronizar secuencia de matrícula
        cur.execute("""
            SELECT setval(
                pg_get_serial_sequence('matricula', 'idmatricula'),
                COALESCE(MAX(idmatricula), 1)
            ) FROM matricula
        """)
        conn.commit()
        # Dificultad por curso
        cur.execute("ALTER TABLE curso ADD COLUMN IF NOT EXISTS dificultad SMALLINT")
        conn.commit()
        cur.execute("SELECT idcurso FROM curso")
        cursos = [r["idcurso"] for r in cur.fetchall()]
        dificultad = {}
        cur.execute("SELECT idcurso, dificultad FROM curso WHERE dificultad IS NOT NULL")
        for row in cur.fetchall():
            dificultad[row["idcurso"]] = row["dificultad"]

        cursos_sin_dificultad = [cid for cid in cursos if cid not in dificultad]
        if cursos_sin_dificultad:
            print(f"Asignando dificultad a {len(cursos_sin_dificultad)} cursos nuevos...")
            opciones_dificultad = [
                (1, 2),
                (3, 4),
                (5, 6),
                (7, 7),
            ]
            pesos = [0.30, 0.64, 0.04 ,0.02]
            for curso_id in cursos_sin_dificultad:
                grupo = random.choices(opciones_dificultad, weights=pesos, k=1)[0]
                dificultad_asignada = random.choice(grupo)

                dificultad[curso_id] = dificultad_asignada
                cur.execute(
                    "UPDATE curso SET dificultad = %s WHERE idcurso = %s",
                    (dificultad_asignada, curso_id)
                )
            conn.commit()
            print("Dificultad asignada.")
        else:
            print("Todos los cursos ya tienen dificultad asignada.")
        # Facilidad por docente
        cur.execute("""
            ALTER TABLE docente
            ADD COLUMN IF NOT EXISTS facilidad VARCHAR(2)
        """)
        conn.commit()

        cur.execute("SELECT iddocente FROM docente")
        todos_docentes = [r["iddocente"] for r in cur.fetchall()]

        cur.execute("SELECT iddocente FROM docente WHERE facilidad IS NOT NULL")
        docentes_con_facilidad = {r["iddocente"] for r in cur.fetchall()}
        docentes_sin_facilidad = [d for d in todos_docentes if d not in docentes_con_facilidad]

        opciones = ["SI", "NO", "NC"]
        pesos   = [0.10, 0.10, 0.80]

        for did in docentes_sin_facilidad:
            valor = random.choices(opciones, weights=pesos, k=1)[0]
            cur.execute(
                "UPDATE docente SET facilidad = %s WHERE iddocente = %s",
                (valor, did)
            )

        conn.commit()
        print(f"Facilidad asignada a {len(docentes_sin_facilidad)} docentes (SI/NO/NC).")
        facilidad = {}
        cur.execute("SELECT iddocente, facilidad FROM docente WHERE facilidad IS NOT NULL")
        for row in cur.fetchall():
            facilidad[row["iddocente"]] = row["facilidad"]

        # 2. Cargar planes de estudio con al menos un curso asignado
        cur.execute("""
            SELECT DISTINCT pe.idplanestudio,
                   pe.nombre AS plan_nombre,
                   pe.version AS plan_version,
                   e.idfacultad,
                   f.nomfacultad,
                   e.nomescuela AS carrera
            FROM plan_estudio pe
            JOIN plan_curso pc ON pc.idplanestudio = pe.idplanestudio
            JOIN escuela e ON pe.idescuela = e.idescuela
            JOIN facultad f ON e.idfacultad = f.idfacultad
        """)
        plan_info = {r["idplanestudio"]: r for r in cur.fetchall()}
        print(f"Planes de estudio cargados: {len(plan_info)}")

        # 3. Ordenar semestres cronológicamente
        cur.execute("SELECT idsemestre FROM semestre ORDER BY fecha_inicio")
        semestres = [r["idsemestre"] for r in cur.fetchall()]
        print(f"Semestres ordenados: {len(semestres)}")

        # 4. Cargar plan_curso -> (plan_estudio, curso)
        cur.execute("""
            SELECT idplancurso,
                idplanestudio,
                idcurso,
                ciclo
            FROM plan_curso
        """)
        plan_curso_map = {
            r["idplancurso"]: (r["idplanestudio"], r["idcurso"], r["ciclo"])
            for r in cur.fetchall()
        }

        print(f"Mapeo Plan-Curso cargado: {len(plan_curso_map)} entradas")

        # 5. Docentes activos
        cur.execute("SELECT iddocente FROM docente WHERE estado_docente = TRUE")
        docentes_activos = [r["iddocente"] for r in cur.fetchall()]
        print(f"Docentes activos: {len(docentes_activos)}")
        if not docentes_activos:
            print("⚠️ ADVERTENCIA: No hay docentes activos. No se podrán asignar docentes a los cursos.")


        # 6. Simulación por semestre
        cur.execute("SELECT idsemestre, fecha_inicio FROM semestre")
        
        # Inicializamos cronómetros
        loop_start = time.time()      # marca de inicio del bucle completo

        sem_inicio = {r["idsemestre"]: r["fecha_inicio"] for r in cur.fetchall()}
        for sem in semestres:
            print(f"\n=== Procesando semestre: {sem} ===")
            sem_start = time.time()

            # Inicializar contadores por plan
            stats = {pid: defaultdict(int) for pid in plan_info}

            # 6.1 Obtener estudiantes elegibles: estado != 'R' y ya ingresaron
            # Ahora la tabla estudiante tiene idplanestudio directamente
            cur.execute("""
                SELECT e.idestudiante, e.idsemestreing, e.idplanestudio, e.estadoalu
                FROM estudiante e
                JOIN semestre s_ing ON e.idsemestreing = s_ing.idsemestre
                JOIN semestre s_cur ON s_cur.idsemestre = %s
                WHERE e.estadoalu != 'R'
                  AND s_ing.fecha_inicio <= s_cur.fecha_inicio
            """, (sem,))
            estudiantes = cur.fetchall()
            print(f"  Estudiantes elegibles encontrados: {len(estudiantes)}")
            if not estudiantes:
                 print("  No hay estudiantes elegibles para procesar en este semestre.")
                 continue # Saltar al siguiente semestre si no hay estudiantes

            # 6.2 Crear o usar matrículas
            matriculas = {}
            for st in estudiantes:
                sid = st["idestudiante"]
                # --- CAMBIO PRINCIPAL AQUÍ ---
                # Obtener pid directamente del estudiante
                pid = st["idplanestudio"]
                # --- FIN CAMBIO PRINCIPAL ---

                if pid is None or pid not in plan_info:
                    # Si el plan del estudiante no está en los planes cargados (raro) o es nulo
                    print(f"⚠️ Advertencia: Estudiante {sid} tiene idplanestudio {pid} inválido o no cargado. Omitiendo.")
                    continue # Saltar este estudiante

                # Contabilizar estadísticas
                if st["idsemestreing"] == sem:
                    stats[pid]["ingresantes"] += 1
                stats[pid]["activos_inicio"] += 1

                # Buscar matrícula existente o crear una nueva
                cur.execute("SELECT idmatricula FROM matricula WHERE idestudiante = %s AND idsemestre = %s", (sid, sem))
                existing = cur.fetchone()
                if existing:
                    matriculas[sid] = existing["idmatricula"]
                    stats[pid]["mat_usadas"] += 1
                else:
                    # Calcular fecha aleatoria entre 15 y 20 días antes del inicio del semestre
                    start_date = sem_inicio.get(sem)
                    days_before = random.randint(15, 20)
                    fecha_matricula = start_date - timedelta(days=days_before)

                    # Definir bloques de 2h entre 8:00 y 17:00 con pesos que favorecen las mañanas
                    bloques = [(8, 10), (10, 12), (12, 14), (14, 16), (16, 17)]
                    pesos_bloques = [0.40,       0.30,        0.15,        0.10,        0.05]

                    bloque = random.choices(bloques, weights=pesos_bloques, k=1)[0]
                    hora = random.randint(bloque[0], bloque[1] - 1)
                    minuto = random.randint(0, 59)
                    hora_matricula = datetime.now().replace(
                        hour=hora, minute=minuto, second=0, microsecond=0
                    ).time()

                    cur.execute(
                        "INSERT INTO matricula (idestudiante, idsemestre, fecha_matricula, hora_matricula) "
                        "VALUES (%s, %s, %s, %s) RETURNING idmatricula",
                        (sid, sem, fecha_matricula, hora_matricula)
                    )
                    mid = cur.fetchone()["idmatricula"]
                    matriculas[sid] = mid
                    stats[pid]["mat_creadas"] += 1
            conn.commit()
            print(f"  Matrículas procesadas/creadas: {len(matriculas)}")
            # ——— Precalcular nº de matrículas previas usando fecha_inicio ———
            cur.execute("""
                SELECT m.idestudiante,
                    COUNT(*) AS cnt
                FROM matricula m
                JOIN semestre s ON m.idsemestre = s.idsemestre
                WHERE s.fecha_inicio < (
                    SELECT fecha_inicio
                    FROM semestre
                    WHERE idsemestre = %s
                )
                GROUP BY m.idestudiante
            """, (sem,))
            mat_counts = {r["idestudiante"]: r["cnt"] for r in cur.fetchall()}

            # 6.3 Demanda de cursos: estudiantes que cumplen prerrequisitos
            aprob_previo = {}
            for st in estudiantes:
                sid = st["idestudiante"]
                # Obtener cursos aprobados por el estudiante en semestres ANTERIORES a 'sem'
                cur.execute("""
                    SELECT pc.idcurso
                    FROM detalle_matricula dm
                    JOIN curso_programado cp ON dm.idcursoprog = cp.idcursoprog
                    JOIN plan_curso pc ON cp.idplancurso = pc.idplancurso
                    JOIN matricula m ON dm.idmatricula = m.idmatricula
                    JOIN semestre s_mat ON m.idsemestre = s_mat.idsemestre -- Semestre de la matricula del detalle
                    JOIN semestre s_cur ON s_cur.idsemestre = %s -- Semestre actual
                    WHERE dm.estado = 'A'
                      AND m.idestudiante = %s
                      AND s_mat.fecha_inicio < s_cur.fecha_inicio -- Solo semestres anteriores
                """, (sem, sid))
                aprob_previo[sid] = {r["idcurso"] for r in cur.fetchall()}

            demanda = defaultdict(list) # { idplancurso: [idestudiante1, idestudiante2,...] }
            for st in estudiantes:
                sid = st["idestudiante"]
                # --- CAMBIO PRINCIPAL AQUÍ ---
                # Obtener pid directamente del estudiante
                pid = st["idplanestudio"]
                # --- FIN CAMBIO PRINCIPAL ---

                if pid is None or pid not in plan_info:
                    # Ya se advirtió antes, pero doble check
                    continue

                # Iterar sobre todos los cursos del plan del estudiante (usando plan_curso_map)
                for pc_id, (p_plan, p_curso, ciclo) in plan_curso_map.items():
                    # Solo considerar cursos del plan del estudiante
                    if p_plan != pid:
                        continue

                    # Verificar si el curso ya fue aprobado previamente
                    if p_curso in aprob_previo.get(sid, set()):
                        continue # Ya lo aprobó, no hay demanda de este estudiante para este curso

                    # Verificar prerrequisitos para este curso (p_curso)
                    cur.execute("SELECT curso_prereqid FROM curso_curso WHERE cursoid = %s", (p_curso,))
                    prereqs = {r["curso_prereqid"] for r in cur.fetchall()}

                    # Si hay prerrequisitos, verificar si todos están en el conjunto de aprobados del estudiante
                    if prereqs and not prereqs.issubset(aprob_previo.get(sid, set())):
                        continue # No cumple prerrequisitos

                    # Si pasó todas las validaciones, el estudiante 'sid' demanda el curso 'pc_id'
                    num_previas = mat_counts.get(sid, 0)
                    if ciclo > num_previas + 1:
                        continue
                    demanda[pc_id].append(sid)

            print(f"  Demanda calculada para {len(demanda)} plan_cursos distintos.")

            # 6.4 Programar cursos para TODOS los plan_curso (incluso sin demanda)
            grupos = {} # { idcursoprog: [idestudiante1, idestudiante2,...] }
            cursos_programados_count = 0
            for pc_id, (p_plan, p_curso, ciclo) in plan_curso_map.items():
                # Asegurarse que el plan del curso exista en plan_info (por si acaso)
                if p_plan not in plan_info:
                    continue

                sids_demandantes = demanda.get(pc_id, [])
                num_demandantes = len(sids_demandantes)

                # Asegurar al menos un grupo por curso, incluso si no hay demanda.
                # Dividir la demanda en grupos de ~20 (o crear 1 si hay 0 demanda)
                num_grupos_necesarios = max(1, (num_demandantes + 19) // 20)

                stats[p_plan]["plan_cursos_evaluados"] += 1

                for g in range(num_grupos_necesarios):
                    # Tomar el subconjunto de estudiantes para este grupo
                    subset_sids = sids_demandantes[g * 20:(g + 1) * 20]
                    doc = random.choice(docentes_activos) if docentes_activos else None

                    # Insertar el curso programado
                    cur.execute(
                        "INSERT INTO curso_programado (promedfinal, condicion, idsemestre, idplancurso, iddocente) VALUES (0,'P',%s,%s,%s) RETURNING idcursoprog",
                        (sem, pc_id, doc)
                    )
                    cp_id = cur.fetchone()["idcursoprog"]
                    grupos[cp_id] = subset_sids # Guardar qué estudiantes van a este grupo específico
                    stats[p_plan]["cursoprog_creados"] += 1
                    cursos_programados_count += 1
            conn.commit()
            print(f"  Cursos programados creados: {cursos_programados_count} grupos.")

            # 6.5 Crear detalle_matricula y asignar notas
            detalles_creados_count = 0
            if not grupos:
                 print("  No se crearon grupos de cursos programados, omitiendo detalles de matrícula.")
            else:
                for cp_id, sids_grupo in grupos.items():
                    # MODIFICADO: Obtener idplancurso, idcurso y iddocente del curso programado
                    cur.execute(
                        "SELECT cp.idplancurso, pc.idcurso, cp.iddocente "
                        "FROM curso_programado cp "
                        "JOIN plan_curso pc ON cp.idplancurso = pc.idplancurso "
                        "WHERE cp.idcursoprog = %s",
                        (cp_id,)
                    )
                    row = cur.fetchone()
                    if not row:
                        print(f"⚠️ Error: No se encontró información para curso programado {cp_id}. Omitiendo.")
                        continue

                    ipc = row["idplancurso"]
                    cid = row["idcurso"]
                    doc_id = row["iddocente"]

                    # Obtener el idplanestudio asociado a este idplancurso usando el mapeo
                    pid_curso = plan_curso_map.get(ipc, (None, None))[0]
                    if pid_curso is None or pid_curso not in plan_info:
                         print(f"⚠️ Error: Plan de estudio no encontrado para idplancurso {ipc}. Omitiendo grupo {cp_id}.")
                         continue # No se puede asignar estadísticas si no se sabe el plan

                    # AÑADIDO: ajustar la dificultad base según la facilidad del docente
                    base_diff = dificultad.get(cid, 3)           # dificultad original (o 3 por defecto)
                    facilidad_val = facilidad.get(doc_id, 'NC')  # "SI"/"NO"/"NC" (NC por defecto)
                    # Lógica de ajuste según facilidad:
                    if facilidad_val == 'SI':
                        # Si el curso era difícil (>5) hacerlo fácil (nivel 2); si ya era fácil, mantenerlo
                        diff = base_diff if base_diff <= 5 else 2
                    elif facilidad_val == 'NO':
                        # Si el curso era fácil (<=3) hacerlo difícil (nivel 6); si ya era difícil, mantenerlo
                        diff = base_diff if base_diff > 3 else 6
                    else:
                        # 'NC': no cambia
                        diff = base_diff
                    if diff <= 2: # Ajustado: 1-2 fáciles
                        mu = 17
                        sigma = 1.5
                    elif diff <= 5: # Ajustado: 3-5 intermedios
                        mu = 14
                        sigma = 2.0
                    else: # Ajustado: 6-7 difíciles
                        mu = 11
                        sigma = 2.5

                    # Crear detalle de matrícula para cada estudiante asignado a este grupo
                    for sid in sids_grupo:
                        mid = matriculas.get(sid) # Obtener idmatricula del estudiante para este semestre
                        if not mid:
                            # Esto no debería pasar si la lógica anterior es correcta
                            print(f"⚠️ Error: No se encontró matrícula para estudiante {sid} en semestre {sem}. Omitiendo detalle.")
                            continue

                        # Generar nota aleatoria con distribución gaussiana
                        nota = round(min(20, max(0, random.gauss(mu, sigma))), 2) # Asegurar rango 0-20
                        estado = 'A' if nota >= 10.5 else 'D' # Aprobado con 10.5 o más

                        cur.execute(
                            "INSERT INTO detalle_matricula (idcursoprog,idmatricula,estado,nota_promedio,modalidad) VALUES (%s,%s,%s,%s,'R')", # Asumiendo 'R'egular
                            (cp_id, mid, estado, nota)
                        )
                        stats[pid_curso]["detalles_creados"] += 1
                        stats[pid_curso]["aprobados"] += (estado == 'A')
                        stats[pid_curso]["desaprobados"] += (estado == 'D')
                        detalles_creados_count += 1
                conn.commit()
                print(f"  Detalles de matrícula creados: {detalles_creados_count}")

            # 6.6 Evaluación de retiros (basado en historial ACUMULADO hasta este semestre INCLUSIVE)
            idx = semestres.index(sem)
            sems_hasta_ahora = tuple(semestres[:idx+1]) # Incluye el semestre actual
            retiros_count = 0
            for st in estudiantes:
                sid = st["idestudiante"]
                # --- CAMBIO PRINCIPAL AQUÍ ---
                # Obtener pid directamente del estudiante
                pid = st["idplanestudio"]
                # --- FIN CAMBIO PRINCIPAL ---

                if pid is None or pid not in plan_info:
                    continue # Ya se manejó antes

                # Contar total de cursos llevados y desaprobados hasta este semestre (inclusive)
                cur.execute("""
                    SELECT COUNT(*) AS total, SUM(CASE WHEN dm.estado='D' THEN 1 ELSE 0 END) AS failed
                    FROM detalle_matricula dm
                    JOIN matricula m ON dm.idmatricula = m.idmatricula
                    WHERE m.idestudiante = %s AND m.idsemestre IN %s
                """, (sid, sems_hasta_ahora))
                res = cur.fetchone()
                total_cursos_llevados = res["total"] if res["total"] is not None else 0
                cursos_desaprobados = res["failed"] if res["failed"] is not None else 0

                # No evaluar retiro si no ha llevado cursos aún
                if total_cursos_llevados == 0:
                    continue

                # Calcular probabilidad de retiro
                # Mayor probabilidad si más del 50% de cursos están desaprobados
                # Probabilidad base baja si el rendimiento es mejor
                tasa_desaprobados = cursos_desaprobados / total_cursos_llevados
                if tasa_desaprobados > 0.6: # Más del 60% desaprobado
                    prob_retiro = 0.6 # Alta probabilidad
                elif tasa_desaprobados > 0.4: # Entre 40% y 60%
                    prob_retiro = 0.25 # Media probabilidad
                else: # Menos del 40% desaprobado
                    prob_retiro = 0.02 # Baja probabilidad

                # Simular retiro
                if random.random() < prob_retiro:
                    cur.execute("UPDATE estudiante SET estadoalu='R' WHERE idestudiante=%s AND estadoalu != 'R'", (sid,))
                    # Verificar si la actualización afectó alguna fila para contar correctamente
                    if cur.rowcount > 0:
                        stats[pid]["retirados"] += 1
                        retiros_count +=1

            conn.commit()
            print(f"  Evaluación de retiros completada: {retiros_count} estudiantes actualizados a 'R'.")

            # 6.7 Mostrar resultados solo para planes con actividad en este semestre
            print("\n  --- Resumen del Semestre por Plan ---")
            planes_mostrados = 0
            for pid, info in plan_info.items():
                s = stats[pid]
                # Mostrar si hubo estudiantes activos, o se crearon matrículas o cursos programados para este plan
                if s['activos_inicio'] > 0 or s['mat_creadas'] > 0 or s['cursoprog_creados'] > 0 :
                    planes_mostrados += 1
                    print(f"  --- Plan {info['plan_nombre']}-{info['plan_version']} ({info['carrera']}) ---")
                    print(f"    Ingresantes: {s['ingresantes']}")
                    print(f"    Activos al inicio: {s['activos_inicio']}")
                    print(f"    Matrículas (Nuevas: {s['mat_creadas']}, Existentes: {s['mat_usadas']})")
                    # print(f"    Plan-Cursos Evaluados: {s['plan_cursos_evaluados']}") # Debug
                    print(f"    Grupos Programados: {s['cursoprog_creados']}")
                    print(f"    Detalles Matrícula: {s['detalles_creados']} (Aprob: {s['aprobados']}, Desap: {s['desaprobados']})")
                    print(f"    Retirados en este semestre: {s['retirados']}")

            if planes_mostrados == 0:
                print("  No hubo actividad significativa en ningún plan para mostrar resumen.")

            # Medir tiempo del semestre
            sem_end = time.time()
            tiempo_total_desde_inicio = sem_end - loop_start
            tiempo_procesamiento = sem_end - sem_start
            print(
                f"  ⏱ Tiempo desde inicio del bucle: {tiempo_total_desde_inicio:.2f} s\n"
                f"  ⏱ Tiempo de procesamiento de este semestre: {tiempo_procesamiento:.2f} s"
            )

    except psycopg2.Error as e:
        print("\n❌ Error de Base de Datos:")
        print(e)
        print("\nRollback de la transacción actual...")
        conn.rollback()

    except Exception as e:
        print("\n❌ Error Inesperado en el Script:")
        print(e)
        import traceback
        traceback.print_exc()
        print("\nRollback de la transacción actual...")
        conn.rollback()

    finally:
        if conn:
            cur.close()
            conn.close()
            print("\n🔌 Conexión a la base de datos cerrada.")

        end_time = datetime.now()
        print("\n✅ Fin del script:", end_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3])
        total_elapsed = (end_time - start_time).total_seconds()
        t_min, t_sec = divmod(int(total_elapsed), 60)
        print(f"⏳ Duración total: {int(total_elapsed)} seg ({t_min} min {t_sec}s)")

if __name__ == "__main__":
    main()