DO $$ 
DECLARE 
    r RECORD;
BEGIN
    -- Eliminar todos los TRIGGERS
    FOR r IN (SELECT event_object_table, trigger_name FROM information_schema.triggers) LOOP
        EXECUTE 'DROP TRIGGER IF EXISTS ' || r.trigger_name || ' ON ' || r.event_object_table || ' CASCADE';
    END LOOP;

    -- Eliminar todas las TABLAS
    FOR r IN (SELECT schemaname, tablename FROM pg_tables WHERE schemaname NOT IN ('pg_catalog', 'information_schema')) LOOP
        EXECUTE 'DROP TABLE IF EXISTS ' || r.schemaname || '.' || r.tablename || ' CASCADE';
    END LOOP;


    -- Eliminar todas las VISTAS
    FOR r IN (SELECT schemaname, viewname FROM pg_views WHERE schemaname NOT IN ('pg_catalog', 'information_schema')) LOOP
        EXECUTE 'DROP VIEW IF EXISTS ' || r.schemaname || '.' || r.viewname || ' CASCADE';
    END LOOP;

    -- Eliminar todas las SECUENCIAS
    FOR r IN (SELECT schemaname, sequencename FROM pg_sequences WHERE schemaname NOT IN ('pg_catalog', 'information_schema')) LOOP
        EXECUTE 'DROP SEQUENCE IF EXISTS ' || r.schemaname || '.' || r.sequencename || ' CASCADE';
    END LOOP;

    -- Eliminar todas las FUNCIONES
    FOR r IN (SELECT routine_schema, routine_name FROM information_schema.routines WHERE routine_schema NOT IN ('pg_catalog', 'information_schema')) LOOP
        EXECUTE 'DROP FUNCTION IF EXISTS ' || r.routine_schema || '.' || r.routine_name || ' CASCADE';
    END LOOP;

    -- Eliminar todos los TIPOS de datos definidos por el usuario
    FOR r IN (SELECT n.nspname as schema_name, t.typname as type_name FROM pg_type t JOIN pg_namespace n ON n.oid = t.typnamespace WHERE n.nspname NOT IN ('pg_catalog', 'information_schema')) LOOP
        EXECUTE 'DROP TYPE IF EXISTS ' || r.schema_name || '.' || r.type_name || ' CASCADE';
    END LOOP;

    -- Eliminar todos los DOMINIOS
    FOR r IN (SELECT n.nspname as schema_name, d.typname as domain_name FROM pg_type d JOIN pg_namespace n ON n.oid = d.typnamespace WHERE d.typtype = 'd' AND n.nspname NOT IN ('pg_catalog', 'information_schema')) LOOP
        EXECUTE 'DROP DOMAIN IF EXISTS ' || r.schema_name || '.' || r.domain_name || ' CASCADE';
    END LOOP;

    -- Eliminar todos los ESQUEMAS (excepto los del sistema)
    FOR r IN (SELECT schema_name FROM information_schema.schemata 
            WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'public', 'pg_toast')) LOOP
        EXECUTE 'DROP SCHEMA IF EXISTS ' || r.schema_name || ' CASCADE';
    END LOOP;
END $$;
