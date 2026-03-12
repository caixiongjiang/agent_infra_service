// Disable "Have I Been Pwned" password check to avoid ETIMEDOUT errors
// when the container cannot reach api.pwnedpasswords.com
const { Pool } = require("pg");

const pool = new Pool({ connectionString: process.env.DB_URL });

const SQL = `
  UPDATE sign_in_experiences
  SET password_policy = jsonb_set(
    jsonb_set(
      COALESCE(password_policy, '{}')::jsonb,
      '{rejects}',
      COALESCE((COALESCE(password_policy, '{}')::jsonb) -> 'rejects', '{}')::jsonb
    ),
    '{rejects,pwned}',
    'false'::jsonb
  )
`;

pool
  .query(SQL)
  .then((r) => {
    console.log("[init] Disabled pwned password check, rows affected:", r.rowCount);
    return pool.end();
  })
  .catch((e) => {
    console.warn("[init] Could not disable pwned check:", e.message);
    return pool.end();
  });
