-- Corregir fechas matrículas
CREATE OR REPLACE FUNCTION actualizar_fechas_matricula()
RETURNS void AS $$
DECLARE
    rec RECORD;
    dias_antes INTEGER;
BEGIN
    FOR rec IN
        SELECT m.idmatricula, s.fecha_inicio
        FROM matricula m
        INNER JOIN semestre s ON m.idsemestre = s.idsemestre
    LOOP
        -- Genera un número aleatorio entre 2 y 20
        dias_antes := FLOOR(random() * 19 + 2); -- 19 + 2 = rango de 2 a 20
        -- Actualiza la fecha de matrícula restando esos días
        UPDATE matricula
        SET fecha_matricula = rec.fecha_inicio - (dias_antes || ' days')::interval
        WHERE idmatricula = rec.idmatricula;
    END LOOP;
END;
$$ LANGUAGE plpgsql;
SELECT actualizar_fechas_matricula();