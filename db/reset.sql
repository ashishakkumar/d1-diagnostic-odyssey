DROP SCHEMA IF EXISTS app CASCADE;

DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'd1_api') THEN
    EXECUTE 'DROP OWNED BY d1_api';
    EXECUTE 'DROP ROLE d1_api';
  END IF;
  IF EXISTS (
    SELECT 1
    FROM pg_auth_members m
    JOIN pg_roles granted ON granted.oid = m.roleid
    JOIN pg_roles member ON member.oid = m.member
    WHERE granted.rolname = 'd1_owner' AND member.rolname = 'd1'
  ) THEN
    EXECUTE 'REVOKE d1_owner FROM d1';
  END IF;
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'd1_owner') THEN
    EXECUTE 'DROP OWNED BY d1_owner';
    EXECUTE 'DROP ROLE d1_owner';
  END IF;
END
$$;
