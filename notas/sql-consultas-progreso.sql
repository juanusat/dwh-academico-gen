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
--~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
--~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
--S02: Cantidad de filas en cada tabla
SELECT
    relname AS table_name,
    n_live_tup AS row_count
FROM
    pg_stat_user_tables
ORDER BY
    row_count DESC;