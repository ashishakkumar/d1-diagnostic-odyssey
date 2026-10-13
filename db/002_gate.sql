CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE SCHEMA app AUTHORIZATION d1_owner;
REVOKE CREATE ON SCHEMA app FROM PUBLIC;
-- A grant to PUBLIC would still let the API role create objects in public.
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
REVOKE CREATE ON SCHEMA public FROM d1_api;
REVOKE CREATE ON SCHEMA app FROM d1_api;
GRANT USAGE ON SCHEMA app TO d1_api;

SET ROLE d1_owner;

-- ponytail: strings are hashed as stored. NFC is the contract package's job
-- before insert; this server has no unicode normalize. Upgrade: fold strings
-- here when Postgres grows normalize().
CREATE FUNCTION app.canonical_json(j jsonb)
RETURNS text
LANGUAGE plpgsql
IMMUTABLE
AS $$
DECLARE
  item jsonb;
  parts text[] := ARRAY[]::text[];
  pair record;
BEGIN
  CASE jsonb_typeof(j)
    WHEN 'object' THEN
      FOR pair IN
        SELECT key, value
        FROM jsonb_each(j)
        ORDER BY key COLLATE "C"
      LOOP
        parts := parts || (to_json(pair.key)::text || ':' || app.canonical_json(pair.value));
      END LOOP;
      RETURN '{' || array_to_string(parts, ',') || '}';
    WHEN 'array' THEN
      FOR item IN
        SELECT value FROM jsonb_array_elements(j)
      LOOP
        parts := parts || app.canonical_json(item);
      END LOOP;
      RETURN '[' || array_to_string(parts, ',') || ']';
    WHEN 'string' THEN
      RETURN to_json(j #>> '{}')::text;
    WHEN 'null' THEN
      RETURN 'null';
    ELSE
      RETURN j::text;
  END CASE;
END;
$$;

CREATE TABLE app.draft (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id uuid NOT NULL,
  kind text NOT NULL,
  body jsonb NOT NULL,
  body_text text NOT NULL,
  body_hash text NOT NULL,
  status text NOT NULL DEFAULT 'pending',
  created_at timestamptz NOT NULL DEFAULT pg_catalog.now(),
  CONSTRAINT draft_status_ck CHECK (
    status IN ('pending', 'approved', 'rejected', 'superseded')
  ),
  CONSTRAINT draft_hash_ck CHECK (body_hash ~ '^[0-9a-f]{64}$')
);

CREATE TABLE app.decision (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  draft_id uuid NOT NULL UNIQUE REFERENCES app.draft (id),
  reviewer text NOT NULL,
  decision text NOT NULL,
  body_hash text NOT NULL,
  decided_at timestamptz NOT NULL DEFAULT pg_catalog.now(),
  CONSTRAINT decision_kind_ck CHECK (decision IN ('approve', 'reject')),
  CONSTRAINT decision_hash_ck CHECK (body_hash ~ '^[0-9a-f]{64}$'),
  CONSTRAINT decision_reviewer_ck CHECK (btrim(reviewer) <> '')
);

CREATE TABLE app.observation (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id uuid NOT NULL,
  draft_id uuid NOT NULL UNIQUE REFERENCES app.draft (id),
  kind text NOT NULL,
  body jsonb NOT NULL,
  body_hash text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT pg_catalog.now()
);

CREATE TABLE app.snapshot (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  decision_id uuid NOT NULL UNIQUE REFERENCES app.decision (id),
  case_id uuid NOT NULL,
  created_at timestamptz NOT NULL DEFAULT pg_catalog.now()
);

CREATE FUNCTION app.draft_before_write()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  IF TG_OP = 'INSERT' THEN
    NEW.body_text := app.canonical_json(NEW.body);
    NEW.body_hash := encode(
      public.digest(convert_to(NEW.body_text, 'UTF8'), 'sha256'),
      'hex'
    );
    IF NEW.status IS NULL OR btrim(NEW.status) = '' THEN
      NEW.status := 'pending';
    END IF;
    IF NEW.status <> 'pending' THEN
      RAISE EXCEPTION 'new draft must be pending' USING ERRCODE = '23514';
    END IF;
    RETURN NEW;
  END IF;

  IF NEW.body IS DISTINCT FROM OLD.body
     OR NEW.body_text IS DISTINCT FROM OLD.body_text
     OR NEW.body_hash IS DISTINCT FROM OLD.body_hash
     OR NEW.case_id IS DISTINCT FROM OLD.case_id
     OR NEW.kind IS DISTINCT FROM OLD.kind
     OR NEW.id IS DISTINCT FROM OLD.id
     OR NEW.created_at IS DISTINCT FROM OLD.created_at
  THEN
    RAISE EXCEPTION 'draft body is frozen' USING ERRCODE = '55000';
  END IF;

  IF NEW.status = OLD.status THEN
    RETURN NEW;
  END IF;
  IF OLD.status <> 'pending' THEN
    RAISE EXCEPTION 'draft is not pending' USING ERRCODE = '55000';
  END IF;
  IF NEW.status = 'superseded' THEN
    RETURN NEW;
  END IF;
  IF NEW.status IN ('approved', 'rejected') THEN
    IF current_user <> 'd1_owner' THEN
      RAISE EXCEPTION 'approval requires apply_decision' USING ERRCODE = '42501';
    END IF;
    RETURN NEW;
  END IF;
  RAISE EXCEPTION 'invalid draft status' USING ERRCODE = '23514';
END;
$$;

CREATE TRIGGER draft_before_write
  BEFORE INSERT OR UPDATE ON app.draft
  FOR EACH ROW
  EXECUTE FUNCTION app.draft_before_write();

CREATE FUNCTION app.apply_decision(draft_id uuid, decision text, seen_hash text)
RETURNS uuid
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, app
AS $$
DECLARE
  v_reviewer text;
  v_txid text;
  v_draft app.draft%ROWTYPE;
  v_decision_id uuid;
BEGIN
  v_reviewer := pg_catalog.current_setting('app.reviewer', true);
  v_txid := pg_catalog.current_setting('app.reviewer_txid', true);
  IF v_reviewer IS NULL
     OR pg_catalog.btrim(v_reviewer) = ''
     OR v_txid IS DISTINCT FROM pg_catalog.txid_current()::text
  THEN
    RAISE EXCEPTION 'reviewer is not bound to this transaction' USING ERRCODE = '42501';
  END IF;
  IF decision NOT IN ('approve', 'reject') THEN
    RAISE EXCEPTION 'invalid decision' USING ERRCODE = '22023';
  END IF;

  SELECT * INTO v_draft FROM app.draft WHERE id = draft_id FOR UPDATE;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'draft not found' USING ERRCODE = '55000';
  END IF;
  IF v_draft.status <> 'pending' THEN
    RAISE EXCEPTION 'draft is not pending' USING ERRCODE = '55000';
  END IF;
  IF seen_hash IS DISTINCT FROM v_draft.body_hash THEN
    RAISE EXCEPTION 'seen hash does not match the draft' USING ERRCODE = '23514';
  END IF;

  INSERT INTO app.decision (draft_id, reviewer, decision, body_hash)
  VALUES (draft_id, v_reviewer, decision, v_draft.body_hash)
  RETURNING id INTO v_decision_id;

  IF decision = 'approve' THEN
    INSERT INTO app.observation (case_id, draft_id, kind, body, body_hash)
    VALUES (v_draft.case_id, v_draft.id, v_draft.kind, v_draft.body, v_draft.body_hash);
    UPDATE app.draft SET status = 'approved' WHERE id = draft_id;
    INSERT INTO app.snapshot (decision_id, case_id)
    VALUES (v_decision_id, v_draft.case_id);
  ELSE
    UPDATE app.draft SET status = 'rejected' WHERE id = draft_id;
  END IF;

  RETURN v_decision_id;
END;
$$;

REVOKE ALL ON FUNCTION app.apply_decision(uuid, text, text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION app.apply_decision(uuid, text, text) TO d1_api;

GRANT SELECT, INSERT ON app.draft TO d1_api;
GRANT UPDATE (status) ON app.draft TO d1_api;
GRANT SELECT ON app.decision, app.observation, app.snapshot TO d1_api;

RESET ROLE;
