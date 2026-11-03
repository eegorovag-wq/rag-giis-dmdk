// Shows the status of the latest n8n executions.
const { DatabaseSync } = require('node:sqlite');
const db = new DatabaseSync('/home/node/.n8n/database.sqlite', { readOnly: true });
for (const r of db.prepare('SELECT id, status, mode, startedAt, stoppedAt FROM execution_entity ORDER BY id DESC LIMIT 3').all()) {
  console.log(r.id, r.status, r.mode, r.startedAt, r.stoppedAt);
}
