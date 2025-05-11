--~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
--~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
--S01: Lista de planes de estudio por carrera con ID

SELECT
    e.nomescuela AS "Carrera",
    pe.nombre || ' V' || pe.version AS "Plan de estudio",
	pe.idplanestudio
FROM facultad f
JOIN escuela e ON e.idfacultad = f.idfacultad
JOIN plan_estudio pe ON pe.idescuela = e.idescuela
ORDER BY
    e.nomescuela

--~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
--~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
--S02: Lista de cursos con créditos por plan de estudio por carrera

SELECT
    e.nomescuela AS "Carrera",
    pe.nombre || ' V' || pe.version AS "Plan de estudio",
    pc.ciclo AS "Ciclo",
    c.nomcurso AS "Curso",
    c.creditos AS "Créditos"
FROM facultad f
JOIN escuela e ON e.idfacultad = f.idfacultad
JOIN plan_estudio pe ON pe.idescuela = e.idescuela
JOIN plan_curso pc ON pc.idplanestudio = pe.idplanestudio
JOIN curso c ON c.idcurso = pc.idcurso
ORDER BY
    e.nomescuela,
    pc.ciclo,
    c.nomcurso;

--~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
--~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
--S03: Cantidad de cursos por plan de estudio por carrera

SELECT
    e.nomescuela AS "Carrera",
    pe.nombre || ' V' || pe.version AS "Plan de estudio",
    COUNT(pc.idcurso) AS "Cantidad de cursos"
FROM facultad f
JOIN escuela e ON e.idfacultad = f.idfacultad
JOIN plan_estudio pe ON pe.idescuela = e.idescuela
JOIN plan_curso pc ON pc.idplanestudio = pe.idplanestudio
GROUP BY
    e.nomescuela,
    pe.nombre,
    pe.version
ORDER BY
    e.nomescuela,
    pe.nombre;

--~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
--~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
--S04: Cursos prerequisitos de cada curso por un plan de estudio (REQ: ID_PE)

SELECT
    c.codcurso AS "Código Curso",
    c.nomcurso AS "Nombre Curso",
    cp.codcurso AS "Código Prerrequisito",
    cp.nomcurso AS "Nombre Prerrequisito"
FROM plan_curso pc
JOIN curso c ON pc.idcurso = c.idcurso
JOIN curso_curso cc ON c.idcurso = cc.cursoid
JOIN curso cp ON cc.curso_prereqid = cp.idcurso
WHERE
    pc.idplanestudio = 1
ORDER BY
    c.nomcurso,
    cp.nomcurso;

--~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
--~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
--S05: Hombres y mujeres matriculados por semestre por plan de estudio con total

SELECT
    e.nomescuela AS carrera,
    pe.nombre || ' V' || pe.version AS plan_estudio,
    m.idsemestre AS semestre,
    SUM(CASE WHEN est.sexo = 'M' THEN 1 ELSE 0 END) AS hombres,
    SUM(CASE WHEN est.sexo = 'F' THEN 1 ELSE 0 END) AS mujeres,
    COUNT(*) AS total
FROM estudiante est
JOIN matricula m ON m.idestudiante = est.idestudiante
JOIN plan_estudio pe ON est.idplanestudio = pe.idplanestudio
JOIN escuela e ON pe.idescuela = e.idescuela
GROUP BY
    e.nomescuela,
    pe.nombre,
    pe.version,
    m.idsemestre
ORDER BY
    e.nomescuela,
    pe.nombre,
    pe.version,
    m.idsemestre;

--~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
--~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
--S06: Cantidad de matriculados por carrera incluyendo retirados

SELECT
    e.nomescuela AS carrera,
    COUNT(DISTINCT est.idestudiante) AS total_matriculados,
    COUNT(DISTINCT CASE WHEN est.estadoalu = 'R' THEN est.idestudiante END) AS retirados,
    COUNT(DISTINCT CASE WHEN est.estadoalu = 'A' THEN est.idestudiante END) AS inscritos
FROM estudiante est
JOIN matricula m ON m.idestudiante = est.idestudiante
JOIN plan_estudio pe ON est.idplanestudio = pe.idplanestudio
JOIN escuela e ON pe.idescuela = e.idescuela
GROUP BY
    e.nomescuela
ORDER BY
    e.nomescuela;

--~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
--~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
--S07: Cantidad de estudiantes por edad por semestre de ingreso por plan de estudios por carrera

SELECT
    e.nomescuela AS carrera,
    pe.nombre || ' V' || pe.version AS plan_estudio,
    est.idsemestreing AS semestre_ingreso,
    DATE_PART('year', s.fecha_inicio) - DATE_PART('year', est.fechanac) -
        CASE 
            WHEN DATE_TRUNC('year', s.fecha_inicio) < DATE_TRUNC('year', est.fechanac) + 
                (s.fecha_inicio - DATE_TRUNC('year', s.fecha_inicio)) 
            THEN 1 ELSE 0 
        END AS edad,
    COUNT(*) AS cantidad_estudiantes
FROM estudiante est
JOIN plan_estudio pe ON est.idplanestudio = pe.idplanestudio
JOIN escuela e ON pe.idescuela = e.idescuela
JOIN semestre s ON est.idsemestreing = s.idsemestre
GROUP BY
    e.nomescuela,
    pe.nombre,
    pe.version,
    est.idsemestreing,
    edad
ORDER BY
    e.nomescuela,
    plan_estudio,
    est.idsemestreing,
    edad;

--~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
--~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
--S08: Cantidad de aprobados y desaprobados por cada curso con su dificultad en cada semestre por ciclo de curso para el plan de estudios 2

SELECT 
    c.codcurso AS "Código de Curso",
    c.nomcurso AS "Nombre de Curso",
    s.idsemestre AS "Semestre",
    pc.ciclo AS "Ciclo",
    c.dificultad AS "Dificultad",
    ROUND(
        100.0 * COUNT(CASE WHEN dm.nota_promedio >= 13.5 THEN 1 END) / COUNT(*),
        2
    ) AS "Aprobados%",
    COUNT(CASE WHEN dm.nota_promedio >= 13.5 THEN 1 END) AS "Aprobados",
    COUNT(*) AS "Total",
    COUNT(CASE WHEN dm.nota_promedio < 13.5 THEN 1 END) AS "Desaprobados"
FROM 
    detalle_matricula dm
JOIN curso_programado cp ON dm.idcursoprog = cp.idcursoprog
JOIN plan_curso pc ON cp.idplancurso = pc.idplancurso
JOIN curso c ON pc.idcurso = c.idcurso
JOIN semestre s ON cp.idsemestre = s.idsemestre
JOIN matricula m ON dm.idmatricula = m.idmatricula
JOIN plan_estudio pe ON pc.idplanestudio = pe.idplanestudio
WHERE 
    pe.idplanestudio = 2
GROUP BY 
    c.codcurso, c.nomcurso, c.dificultad, s.idsemestre, pc.ciclo
ORDER BY 
    pc.ciclo, s.idsemestre, c.nomcurso;


--~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
--~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
--S09: Cantidad de cursos por dificultad


SELECT dificultad, COUNT(*) AS cantidad_cursos
FROM curso
GROUP BY dificultad
ORDER BY dificultad;

--~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
--~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-- S10 Cantidad y porcentaje de cursos por dificultad, por plan de estudios y carrera
SELECT
  e.nomescuela                   AS escuela,
  pe.nombre || ' v' || pe.version AS plan_estudio,
  c.dificultad,
  COUNT(*)                       AS cantidad_cursos,
  ROUND(
    COUNT(*)::numeric
    / SUM(COUNT(*)) OVER (PARTITION BY pe.idplanestudio)
    * 100
    , 2
  )                               AS porcentaje
FROM plan_estudio pe
JOIN escuela e
  ON pe.idescuela = e.idescuela
JOIN plan_curso pc
  ON pc.idplanestudio = pe.idplanestudio
JOIN curso c
  ON pc.idcurso = c.idcurso
GROUP BY
  e.nomescuela,
  pe.idplanestudio,
  pe.nombre,
  pe.version,
  c.dificultad
ORDER BY
  e.nomescuela,
  pe.nombre,
  pe.version,
  c.dificultad;

--~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
--~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
--S11: Dnis repetidos


WITH todos_dnis AS (
    SELECT dni FROM docente
    UNION ALL
    SELECT dni FROM estudiante
)
SELECT dni, COUNT(*) AS cantidad
FROM todos_dnis
GROUP BY dni
HAVING COUNT(*) > 1;

--~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
--~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
--S12: Ver progreso acedémico de un estudiante (RED: id estudiante)

SELECT 
    c.nomcurso AS nombre_curso,
    pc.ciclo AS ciclo_curso,
    d.nomcompleto AS docente,
    dm.nota_promedio AS nota,
    pe.nombre AS plan_estudio,
    pe.version AS version_plan,
    esc.nomescuela AS escuela,
    s.idsemestre AS semestre
FROM 
    estudiante est
JOIN matricula m ON est.idestudiante = m.idestudiante
JOIN detalle_matricula dm ON m.idmatricula = dm.idmatricula
JOIN curso_programado cp ON dm.idcursoprog = cp.idcursoprog
JOIN plan_curso pc ON cp.idplancurso = pc.idplancurso
JOIN curso c ON pc.idcurso = c.idcurso
JOIN docente d ON cp.iddocente = d.iddocente
JOIN plan_estudio pe ON est.idplanestudio = pe.idplanestudio
JOIN escuela esc ON pe.idescuela = esc.idescuela
JOIN semestre s ON m.idsemestre = s.idsemestre
WHERE 
    est.idestudiante = 1
ORDER BY 
    s.fecha_inicio;

--~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
--~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
--S13: Estudiantes retirados y el ciclo de retiro

SELECT 
    e.idestudiante,
    e.nombres,
    e.apepat,
    e.apemat,
    e.idsemestreing               AS semestre_ingreso,
    pe.idplanestudio,
    es.nomescuela                  AS escuela,
    MAX(m.idsemestre)              AS ultimo_semestre_matriculado,
    COUNT(m.idmatricula)           AS total_matriculas
FROM estudiante e
LEFT JOIN matricula m 
    ON e.idestudiante = m.idestudiante
JOIN plan_estudio pe 
    ON e.idplanestudio = pe.idplanestudio
JOIN escuela es 
    ON pe.idescuela = es.idescuela
WHERE e.estadoalu = 'R'
GROUP BY 
    e.idestudiante,
    e.nombres,
    e.apepat,
    e.apemat,
    e.idsemestreing,
    pe.idplanestudio,
    es.nomescuela
ORDER BY ultimo_semestre_matriculado DESC;

--~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
--~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
--S14: Alumnos cuyo semestre de ingresob es diferente al semestre de sus primera matrícula
SELECT
  e.idestudiante,
  e.nombres || ' ' || e.apepat || ' ' || e.apemat AS nombre_completo,
  e.idsemestreing                                AS semestre_ingreso,
  m.primer_semestre                              AS primer_semestre_matricula
FROM estudiante e
JOIN (
  SELECT
    idestudiante,
    MIN(idsemestre) AS primer_semestre
  FROM matricula
  GROUP BY idestudiante
) m
  ON e.idestudiante = m.idestudiante
WHERE e.idsemestreing <> m.primer_semestre
ORDER BY e.idestudiante;