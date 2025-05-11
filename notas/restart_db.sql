DO
$$
DECLARE
    r RECORD;
BEGIN
    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
        EXECUTE 'TRUNCATE TABLE ' || quote_ident(r.tablename) || ' CASCADE';
    END LOOP;
END
$$;
DO $$ 
DECLARE 
    seq RECORD;
BEGIN
    -- Itera sobre todas las secuencias del esquema público (ajusta según sea necesario)
    FOR seq IN
        SELECT sequence_schema, sequence_name
        FROM information_schema.sequences
        WHERE sequence_schema NOT IN ('pg_catalog', 'information_schema')
    LOOP
        -- Genera y ejecuta la instrucción para reiniciar cada secuencia
        EXECUTE format(
            'ALTER SEQUENCE %I.%I RESTART WITH 1',
            seq.sequence_schema,
            seq.sequence_name
        );
        RAISE NOTICE 'Secuencia reiniciada: %.%', seq.sequence_schema, seq.sequence_name;
    END LOOP;
END $$;