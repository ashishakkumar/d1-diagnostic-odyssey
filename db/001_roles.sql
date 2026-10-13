-- Migrations run as a superuser, then as d1_owner. The API role is not a member of the owner.
CREATE ROLE d1_owner NOLOGIN;
CREATE ROLE d1_api NOLOGIN NOINHERIT;
GRANT d1_owner TO CURRENT_USER;
