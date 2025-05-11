--~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
--~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
--S01: Cantidad de matrículas de los alumnos retirados
SELECT 
    e.idestudiante,
	esc.nomescuela,
	e.nombres || ' ' || e.apepat || ' ' || e.apemat as estudiante,
    e.idsemestreing,
    MAX(m.idsemestre) AS ultimo_semestre_matriculado,
    COUNT(m.idmatricula) AS total_matriculas
FROM 
    estudiante e
LEFT JOIN matricula m ON e.idestudiante = m.idestudiante
INNER JOIN plan_estudio pe on pe.idplanestudio = e.idplanestudio
INNER JOIN escuela esc on esc.idescuela = pe.idescuela
WHERE 
    e.estadoalu = 'R'
GROUP BY 
    e.idestudiante, esc.nomescuela, e.nombres, e.apepat, e.apemat, e.idsemestreing
ORDER BY 
    ultimo_semestre_matriculado DESC;
--~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
--~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
--S02: Consistencia de cursos, retiros y matrículas por estudiante
/*
idestudiante, nombre_completo
carrera
semestre_ingreso, fecha_inicio_ingreso
cantidad_matriculas, primer_semestre_matricula, ultimo_semestre_matricula
fecha_primera_matricula, hora_primera_matricula, dias_anticipacion
cursos_llevados, total_cursos_plan, cursos_faltantes
semestre_retiro
*/
SELECT
  e.idestudiante,
  -- Nombres completos
  e.nombres
    || ' '
    || e.apepat
    || ' '
    || e.apemat                  AS nombre_completo,
  -- Carrera (escuela + plan)
  esc.nomescuela
    || ' '
    || ps.nombre
    || '-'
    || ps.version               AS carrera,
  -- Semestre de ingreso
  e.idsemestreing              AS semestre_ingreso,
  -- Fecha de inicio de ese semestre
  sem_ing.fecha_inicio         AS fecha_inicio_ingreso,
  -- Cantidad de matrículas
  COALESCE(m.cant_matriculas, 0)    AS cantidad_matriculas,
  -- Primer semestre en que se matriculó (mínimo sobre todas sus matrículas)
  m.primer_semestre               AS primer_semestre_matricula,
  -- Último semestre en que se matriculó (máximo)
  m.ultimo_semestre               AS ultimo_semestre_matricula,
  -- Fecha y hora de la matrícula en su semestre de ingreso
  (m.primera_matricula_ts)::date   AS fecha_primera_matricula,
  (m.primera_matricula_ts)::time   AS hora_primera_matricula,
  -- Días de anticipación: inicio_semestre - fecha_primera_matricula
  (sem_ing.fecha_inicio
     - (m.primera_matricula_ts)::date
  )                                AS dias_anticipacion,
  -- Cantidad de cursos que ha llevado
  COALESCE(d.cant_cursos, 0)       AS cursos_llevados,
  -- Total de cursos en su plan
  COALESCE(p.total_cursos, 0)      AS total_cursos_plan,
  -- Cuántos cursos le faltan
  COALESCE(p.total_cursos, 0)
    - COALESCE(d.cant_cursos, 0)    AS cursos_faltantes,
  -- Semestre de retiro (o '-' si sigue activo)
  CASE
    WHEN e.estadoalu = 'R'
      THEN COALESCE(m.ultimo_semestre, '-')
    ELSE '-'
  END                               AS semestre_retiro
FROM estudiante e

-- Datos de plan y escuela
JOIN plan_estudio ps
  ON e.idplanestudio = ps.idplanestudio
JOIN escuela esc
  ON ps.idescuela = esc.idescuela

-- Fecha de inicio del semestre de ingreso
JOIN semestre sem_ing
  ON e.idsemestreing = sem_ing.idsemestre

-- Métricas de matrícula y timestamp de la matrícula en semestre de ingreso
LEFT JOIN LATERAL (
  SELECT
    COUNT(*)                                        AS cant_matriculas,
    MIN(idsemestre)                                 AS primer_semestre,
    MAX(idsemestre)                                 AS ultimo_semestre,
    MIN(fecha_matricula + hora_matricula)
      FILTER (WHERE idsemestre = e.idsemestreing)   AS primera_matricula_ts
  FROM matricula m2
  WHERE m2.idestudiante = e.idestudiante
) AS m
  ON TRUE

-- Conteo de cursos llevados
LEFT JOIN (
  SELECT
    m3.idestudiante,
    COUNT(*)        AS cant_cursos
  FROM matricula m3
  JOIN detalle_matricula dm
    ON m3.idmatricula = dm.idmatricula
  GROUP BY m3.idestudiante
) d
  ON e.idestudiante = d.idestudiante

-- Total de cursos en su plan de estudios
LEFT JOIN (
  SELECT
    idplanestudio,
    COUNT(*)        AS total_cursos
  FROM plan_curso
  GROUP BY idplanestudio
) p
  ON e.idplanestudio = p.idplanestudio

ORDER BY cursos_faltantes ;
--S03: Consistencia de cursos, retiros y matrículas por estudiante
/*
idestudiante, nombre_completo, carrera, semestre_ingreso
cantidad_matriculas, primer_semestre_matricula, ultimo_semestre_matricula
cursos_llevados, total_cursos_plan, cursos_faltantes
semestre_retiro, promedio_ultimo_semestre, cursos_ultimo_semestre
cursos_desaprobados_ult_semestre, porcentaje_desaprobados_ult_semestre
*/
WITH
-- 1) Métricas de matrícula por estudiante
matri AS (
  SELECT
    m.idestudiante,
    COUNT(*)                     AS cant_matriculas,
    MIN(m.idsemestre)            AS primer_semestre,
    MAX(m.idsemestre)            AS ultimo_semestre
  FROM matricula m
  GROUP BY m.idestudiante
),

-- 2) Conteo total de cursos llevados por estudiante
cursos_llev AS (
  SELECT
    m.idestudiante,
    COUNT(*) AS cant_cursos
  FROM matricula m
  JOIN detalle_matricula dm
    ON m.idmatricula = dm.idmatricula
  GROUP BY m.idestudiante
),

-- 3) Avance y desempeño académico por estudiante (quizá reprobados)
ult_sem AS (
  SELECT
    m.idestudiante,
    ROUND( AVG(dm.nota_promedio)                    , 2) AS avg_nota_ult_sem,
    COUNT(*)                                        AS cant_cursos_ult_sem,
    SUM( CASE WHEN dm.nota_promedio < 13.5 THEN 1 ELSE 0 END ) AS cant_desaprob_ult_sem,
    ROUND(
      SUM( CASE WHEN dm.nota_promedio < 13.5 THEN 1 ELSE 0 END )::numeric
      / NULLIF(COUNT(*),0) * 100
    , 2)                                             AS pct_desaprob_ult_sem
  FROM matricula m
  JOIN matri ON m.idestudiante = matri.idestudiante
            AND m.idsemestre  = matri.ultimo_semestre
  JOIN detalle_matricula dm
    ON m.idmatricula = dm.idmatricula
  GROUP BY m.idestudiante
),

-- 4) Total de cursos por plan de estudios
plan_totales AS (
  SELECT
    idplanestudio,
    COUNT(*) AS total_cursos
  FROM plan_curso
  GROUP BY idplanestudio
)

SELECT
  e.idestudiante,
  e.nombres || ' ' || e.apepat || ' ' || e.apemat AS nombre_completo,
  esc.nomescuela || ' ' || ps.nombre || '-' || ps.version AS carrera,
  e.idsemestreing AS semestre_ingreso,

  COALESCE(matri.cant_matriculas, 0)       AS cantidad_matriculas,
  matri.primer_semestre                   AS primer_semestre_matricula,
  matri.ultimo_semestre                   AS ultimo_semestre_matricula,

  COALESCE(cursos_llev.cant_cursos, 0)     AS cursos_llevados,
  COALESCE(plan_totales.total_cursos, 0)   AS total_cursos_plan,
  COALESCE(plan_totales.total_cursos, 0)
    - COALESCE(cursos_llev.cant_cursos, 0)  AS cursos_faltantes,

  CASE WHEN e.estadoalu = 'R'
       THEN COALESCE(matri.ultimo_semestre::text, '-')
       ELSE '-'
  END                                       AS semestre_retiro,

  -- métricas del último semestre ya corregidas
  ult_sem.avg_nota_ult_sem                 AS promedio_ultimo_semestre,
  ult_sem.cant_cursos_ult_sem              AS cursos_ultimo_semestre,
  ult_sem.cant_desaprob_ult_sem            AS cursos_desaprobados_ult_semestre,
  ult_sem.pct_desaprob_ult_sem             AS porcentaje_desaprobados_ult_semestre

FROM estudiante e
JOIN plan_estudio ps    ON e.idplanestudio    = ps.idplanestudio
JOIN escuela esc        ON ps.idescuela       = esc.idescuela

LEFT JOIN matri         ON e.idestudiante     = matri.idestudiante
LEFT JOIN cursos_llev   ON e.idestudiante     = cursos_llev.idestudiante
LEFT JOIN plan_totales  ON e.idplanestudio    = plan_totales.idplanestudio
LEFT JOIN ult_sem       ON e.idestudiante     = ult_sem.idestudiante
WHERE e.estadoalu = 'R'
ORDER BY cursos_faltantes;