-- Reporte 1: Promedio final de los estudiantes por curso, semestre y año
-- Muestra el promedio de todas las notas finales agrupadas por curso, semestre y año calendario

SELECT
  s.idsemestre,
  EXTRACT(YEAR FROM s.fecha_inicio)::INT    AS anio,
  c.codcurso,
  c.nomcurso,
  AVG(dm.nota_promedio)::NUMERIC(5,2)        AS promedio_final
FROM detalle_matricula dm
JOIN curso_programado cp   ON dm.idcursoprog = cp.idcursoprog
JOIN semestre s            ON cp.idsemestre = s.idsemestre
JOIN plan_curso pc         ON cp.idplancurso = pc.idplancurso
JOIN curso c               ON pc.idcurso = c.idcurso
GROUP BY s.idsemestre, anio, c.codcurso, c.nomcurso
ORDER BY anio, s.idsemestre, c.codcurso;

-- Reporte 2: Condición académica (Aprobado/Desaprobado) por estudiante y curso
-- Se basa en el campo estado de detalle_matricula ('A'=Aprobado, 'D'=Desaprobado, 'R'=Retirado, etc.)

SELECT
  e.idestudiante,
  e.nombres || ' ' || e.apepat || ' ' || e.apemat AS estudiante,
  c.codcurso,
  c.nomcurso,
  CASE dm.estado
    WHEN 'A' THEN 'Aprobado'
    WHEN 'D' THEN 'Desaprobado'
    WHEN 'R' THEN 'Retirado'
    ELSE 'Otro'
  END AS condicion
FROM detalle_matricula dm
JOIN matricula m          ON dm.idmatricula = m.idmatricula
JOIN estudiante e         ON m.idestudiante = e.idestudiante
JOIN curso_programado cp  ON dm.idcursoprog = cp.idcursoprog
JOIN plan_curso pc        ON cp.idplancurso = pc.idplancurso
JOIN curso c              ON pc.idcurso = c.idcurso
ORDER BY e.idestudiante, c.codcurso;

-- Reporte 3: Rendimiento promedio por docente
-- Promedio de las notas de los estudiantes para cada docente

SELECT
  d.iddocente,
  d.nombres || ' ' || d.apepat || ' ' || d.apemat AS docente,
  AVG(dm.nota_promedio)::NUMERIC(5,2)       AS promedio_docente
FROM detalle_matricula dm
JOIN curso_programado cp  ON dm.idcursoprog = cp.idcursoprog
JOIN docente d            ON cp.iddocente = d.iddocente
GROUP BY d.iddocente, docente
ORDER BY promedio_docente DESC;

-- Reporte 4: Tasa de retirados por curso y docente
-- Proporción de estudiantes con estado 'R' (Retirado) sobre el total matriculado

SELECT
  c.codcurso,
  c.nomcurso,
  d.iddocente,
  d.nombres || ' ' || d.apepat || ' ' || d.apemat AS docente,
  COUNT(*) FILTER (WHERE dm.estado = 'R')::DECIMAL / COUNT(*) AS tasa_retirados
FROM detalle_matricula dm
JOIN curso_programado cp  ON dm.idcursoprog = cp.idcursoprog
JOIN docente d            ON cp.iddocente = d.iddocente
JOIN plan_curso pc        ON cp.idplancurso = pc.idplancurso
JOIN curso c              ON pc.idcurso = c.idcurso
GROUP BY c.codcurso, c.nomcurso, d.iddocente, docente
ORDER BY tasa_retirados DESC;

-- Reporte 5: Ranking de estudiantes con mejor rendimiento por semestre
-- Se calcula el promedio por estudiante en cada semestre y se aplica RANK()

SELECT
  s.idsemestre,
  EXTRACT(YEAR FROM s.fecha_inicio)::INT AS anio,
  e.idestudiante,
  e.nombres || ' ' || e.apepat || ' ' || e.apemat AS estudiante,
  AVG(dm.nota_promedio)::NUMERIC(5,2)      AS promedio,
  RANK() OVER (PARTITION BY s.idsemestre ORDER BY AVG(dm.nota_promedio) DESC) AS ranking
FROM detalle_matricula dm
JOIN matricula m          ON dm.idmatricula = m.idmatricula
JOIN estudiante e         ON m.idestudiante = e.idestudiante
JOIN semestre s           ON m.idsemestre = s.idsemestre
GROUP BY s.idsemestre, anio, e.idestudiante, estudiante
ORDER BY s.idsemestre, ranking;

-- Reporte 6: Evolución del rendimiento académico de un estudiante
-- Promedio por semestre para un estudiante determinado (reemplazar :idestudiante)

SELECT
  s.idsemestre,
  EXTRACT(YEAR FROM s.fecha_inicio)::INT AS anio,
  AVG(dm.nota_promedio)::NUMERIC(5,2)      AS promedio_semestre
FROM detalle_matricula dm
JOIN matricula m          ON dm.idmatricula = m.idmatricula
JOIN semestre s           ON m.idsemestre = s.idsemestre
WHERE m.idestudiante = :idestudiante
GROUP BY s.idsemestre, anio
ORDER BY anio, s.idsemestre;

-- Reporte 7: Tasa de desaprobación por curso, docente y semestre
-- Proporción de estudiantes con estado 'D' (Desaprobado)

SELECT
  c.codcurso,
  c.nomcurso,
  d.iddocente,
  d.nombres || ' ' || d.apepat || ' ' || d.apemat AS docente,
  s.idsemestre,
  EXTRACT(YEAR FROM s.fecha_inicio)::INT AS anio,
  COUNT(*) FILTER (WHERE dm.estado = 'D')::DECIMAL / COUNT(*) AS tasa_desaprobacion
FROM detalle_matricula dm
JOIN curso_programado cp  ON dm.idcursoprog = cp.idcursoprog
JOIN semestre s           ON cp.idsemestre = s.idsemestre
JOIN plan_curso pc        ON cp.idplancurso = pc.idplancurso
JOIN curso c              ON pc.idcurso = c.idcurso
JOIN docente d            ON cp.iddocente = d.iddocente
GROUP BY c.codcurso, c.nomcurso, d.iddocente, docente, s.idsemestre, anio
ORDER BY anio, s.idsemestre, tasa_desaprobacion DESC;

-- Reporte 8: Comparativo de rendimiento entre estudiantes por créditos matriculados
-- Muestra el total de créditos y el promedio de notas por estudiante

SELECT
  e.idestudiante,
  e.nombres || ' ' || e.apepat || ' ' || e.apemat AS estudiante,
  SUM(c.creditos)          AS total_creditos,
  AVG(dm.nota_promedio)::NUMERIC(5,2) AS promedio
FROM detalle_matricula dm
JOIN matricula m          ON dm.idmatricula = m.idmatricula
JOIN estudiante e         ON m.idestudiante = e.idestudiante
JOIN curso_programado cp  ON dm.idcursoprog = cp.idcursoprog
JOIN plan_curso pc        ON cp.idplancurso = pc.idplancurso
JOIN curso c              ON pc.idcurso = c.idcurso
GROUP BY e.idestudiante, estudiante
ORDER BY total_creditos DESC, promedio DESC;