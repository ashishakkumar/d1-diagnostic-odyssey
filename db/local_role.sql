-- Login used by local Postgres when Docker is not the process that creates it.
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'd1') THEN
    CREATE ROLE d1 LOGIN PASSWORD 'd1' SUPERUSER;
  ELSE
    ALTER ROLE d1 WITH LOGIN PASSWORD 'd1' SUPERUSER;
  END IF;
END
$$;

SELECT 'CREATE DATABASE d1 OWNER d1'
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'd1')\gexec
