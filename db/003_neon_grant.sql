-- Hosted demo only (Neon). The app does SET ROLE d1_api. On Postgres 16+ a plain
-- CREATE ROLE grant does not give the creator SET, so grant it without INHERIT.
GRANT d1_api TO CURRENT_USER WITH SET TRUE, INHERIT FALSE;
