-- cleanup.sql: delete the 50 seeded accounts listed in fake_users_credentials.csv, then list
-- every admin. The CSV was committed to discipline-back in c8dc7af and removed in a0f8f4d
-- (F-19); every version holds the same 50 emails, all with role "user". Only the emails are
-- reproduced here, lowercased.
--
-- Run AFTER the migrations (00002 adds ON DELETE CASCADE, so their tasks and vocabulary words
-- go too). DB_URL is the database's public URL with ?sslmode=require; never paste it anywhere:
--   docker run --rm -i -e DB_URL postgres:16-alpine sh -c 'exec psql "$DB_URL" -X' < cleanup.sql
--
-- By default the transaction ends with ROLLBACK: a dry run that shows the counts and changes
-- nothing. See the marked line at the end of the transaction to make it permanent.

\set ON_ERROR_STOP on

BEGIN;

CREATE TEMP TABLE seeded_emails (email text PRIMARY KEY) ON COMMIT DROP;
INSERT INTO seeded_emails (email) VALUES
    ('adolphusdietrich@toy.io'),
    ('alexandrineschimmel@douglas.net'),
    ('anastacioheidenreich@damore.org'),
    ('arlenepadberg@mayert.name'),
    ('bellagleason@leannon.biz'),
    ('bradfordziemann@jakubowski.io'),
    ('braedenprosacco@hoppe.info'),
    ('brandynkassulke@mcglynn.net'),
    ('catherinekunze@kiehn.name'),
    ('ceceliawehner@padberg.biz'),
    ('darlenebashirian@wolf.info'),
    ('davinosinski@botsford.info'),
    ('dockbernier@mcclure.org'),
    ('doriswatsica@schoen.name'),
    ('ednaswift@rutherford.com'),
    ('einartowne@abbott.name'),
    ('elissaparisian@marks.net'),
    ('elverabartell@trantow.name'),
    ('feliciaprohaska@feest.net'),
    ('francokiehn@vandervort.name'),
    ('garrickdoyle@prosacco.io'),
    ('godfreyschinner@wisozk.net'),
    ('guywill@ebert.com'),
    ('hailieullrich@heller.net'),
    ('hayliepagac@okuneva.com'),
    ('herminaledner@nicolas.io'),
    ('jamesonkohler@donnelly.org'),
    ('jaydebode@bauch.biz'),
    ('jaymehauck@collier.info'),
    ('jeffereynikolaus@feil.io'),
    ('jereljacobs@schinner.info'),
    ('joannehamill@trantow.biz'),
    ('kareemledner@bailey.io'),
    ('khalidhoppe@stoltenberg.name'),
    ('kieranheathcote@barrows.biz'),
    ('kileythompson@ratke.biz'),
    ('koberohan@greenfelder.com'),
    ('lemuelmclaughlin@lindgren.org'),
    ('lisettekrajcik@fay.net'),
    ('margebaumbach@konopelski.com'),
    ('milohansen@mcglynn.net'),
    ('neldareynolds@kirlin.io'),
    ('nickdaniel@kuhlman.org'),
    ('nikkolabadie@watsica.com'),
    ('pascalewest@cremin.info'),
    ('raleighchristiansen@hoppe.com'),
    ('ritafritsch@murphy.io'),
    ('shadwunsch@mosciski.io'),
    ('shayleekoss@sauer.io'),
    ('tristianfarrell@hartmann.info');

-- Seeded accounts present now (expect at most 50; role should be "user" for all of them).
SELECT u.role, count(*) AS seeded_users_found
  FROM users u JOIN seeded_emails s ON lower(u.email) = s.email
 GROUP BY u.role;

DELETE FROM users u USING seeded_emails s WHERE lower(u.email) = s.email;

-- Expect 0 inside the transaction.
SELECT count(*) AS seeded_users_left
  FROM users u JOIN seeded_emails s ON lower(u.email) = s.email;

-- >>> DRY RUN. To delete for real: after a dry run shows the counts you expect, change
-- >>> the next line from ROLLBACK; to COMMIT; and run the file once more.
ROLLBACK;

-- Every admin account (read-only). Check each one's password hash with:
--   docker run --rm -e DB_URL postgres:16-alpine sh -c 'exec psql "$DB_URL" -X -At -c "SELECT password FROM users WHERE id = <id>"' \
--     | python3 check_admin_password.py
SELECT id, email, name, created_at FROM users WHERE role = 'admin' ORDER BY id;
