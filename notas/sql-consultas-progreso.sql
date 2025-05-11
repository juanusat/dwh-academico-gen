--~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
--~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
--S01: Cantidad de filas en tablas relevantes
SELECT 'estudiante' AS tabla, COUNT(*) AS cantidad FROM estudiante
UNION ALL
SELECT 'matricula', COUNT(*) FROM matricula
UNION ALL
SELECT 'detalle_matricula', COUNT(*) FROM detalle_matricula
UNION ALL
SELECT 'curso_programado', COUNT(*) FROM curso_programado;
