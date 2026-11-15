-- Ejecutar UNA VEZ desde DBeaver como gestion_admin en gestion_personas.
-- La contraseña se asigna después en psql mediante \password gestion_api (no por GitHub).
BEGIN;
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'gestion_api') THEN
        CREATE ROLE gestion_api LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION;
    END IF;
END $$;
GRANT CONNECT ON DATABASE gestion_personas TO gestion_api;
GRANT USAGE ON SCHEMA public TO gestion_api;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.persona TO gestion_api;
GRANT INSERT ON TABLE public.auditoria TO gestion_api;
-- No concedemos SELECT, UPDATE ni DELETE en auditoria, ni privilegios de DDL.
COMMIT;
-- Verificar sin modificar nada:
SELECT grantee, table_name, privilege_type
FROM information_schema.role_table_grants
WHERE grantee = 'gestion_api'
  AND table_schema = 'public'
ORDER BY table_name, privilege_type;
