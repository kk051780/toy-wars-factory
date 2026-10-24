'use strict';
const fs = require('node:fs');
const crypto = require('node:crypto');
const {DatabaseSync} = require('node:sqlite');
const {CreditLedger, GuardError} = require('./gemini_budget_guard.cjs');

class PersistentCreditLedger extends CreditLedger {
  #db;
  constructor(file, cap, maxRequests, runId) {
    super(cap, maxRequests);
    if (cap > 10000000000n || typeof runId !== 'string' || !runId || runId.length > 100) {
      throw new GuardError('INVALID_PERSISTENT_CONFIG');
    }
    const fd = fs.openSync(file, 'a', 0o600); fs.closeSync(fd);
    this.#db = new DatabaseSync(file);
    this.#db.exec('PRAGMA busy_timeout=5000; PRAGMA journal_mode=WAL; PRAGMA synchronous=FULL;');
    this.#db.exec('CREATE TABLE IF NOT EXISTS budget(id INTEGER PRIMARY KEY CHECK(id=1), run TEXT, cap INTEGER, max_requests INTEGER, used INTEGER, requests INTEGER, halted INTEGER); CREATE TABLE IF NOT EXISTS leases(id TEXT PRIMARY KEY, amount INTEGER);');
    try {
      this.#tx(() => {
        this.#db.prepare('INSERT OR IGNORE INTO budget VALUES (1,?,?,?,0,0,0)').run(runId, cap, maxRequests);
        const row = this.#read();
        if (row.run !== runId || row.cap !== cap || row.max_requests !== BigInt(maxRequests)) {
          throw new GuardError('PERSISTENT_CONFIG_MISMATCH');
        }
      });
    } catch (error) {this.#db.close(); throw error;}
  }
  #tx(fn) {
    this.#db.exec('BEGIN IMMEDIATE');
    try {const result = fn(); this.#db.exec('COMMIT'); return result;}
    catch (error) {this.#db.exec('ROLLBACK'); throw error;}
  }
  #read() {
    const statement = this.#db.prepare('SELECT *, (SELECT COALESCE(SUM(amount),0) FROM leases) AS reserved FROM budget WHERE id=1');
    statement.setReadBigInts(true); return statement.get();
  }
  #check(row) {
    if (row.halted) throw new GuardError('LEDGER_HALTED');
    if (row.requests >= row.max_requests) throw new GuardError('REQUEST_CAP_EXHAUSTED');
    if (row.used + row.reserved >= row.cap) throw new GuardError('CREDIT_CAP_EXHAUSTED');
  }
  assertOpen() {this.#check(this.#read());}
  reserve(amount) {
    if (typeof amount !== 'bigint' || amount <= 0n) throw new GuardError('INVALID_RESERVATION');
    return this.#tx(() => {
      const row = this.#read(); this.#check(row);
      if (row.used + row.reserved + amount > row.cap) throw new GuardError('CREDIT_CAP_EXHAUSTED');
      const id = crypto.randomUUID();
      this.#db.prepare('INSERT INTO leases VALUES (?,?)').run(id, amount);
      this.#db.prepare('UPDATE budget SET requests=requests+1 WHERE id=1').run();
      return id;
    });
  }
  settle(id, actual) {
    const invalid = this.#tx(() => {
      const statement = this.#db.prepare('SELECT amount FROM leases WHERE id=?'); statement.setReadBigInts(true);
      const lease = statement.get(id);
      if (!lease) throw new GuardError('INVALID_OR_CLOSED_LEASE');
      if (typeof actual !== 'bigint' || actual < 0n || actual > lease.amount) {
        this.#db.prepare('UPDATE budget SET halted=1 WHERE id=1').run(); return true;
      }
      this.#db.prepare('DELETE FROM leases WHERE id=?').run(id);
      this.#db.prepare('UPDATE budget SET used=used+? WHERE id=1').run(actual);
      return false;
    });
    if (invalid) throw new GuardError('USAGE_EXCEEDS_RESERVATION');
  }
  halt() {this.#tx(() => this.#db.prepare('UPDATE budget SET halted=1 WHERE id=1').run());}
  snapshot() {
    const row = this.#read();
    return {cap: String(row.cap), used: String(row.used), reserved: String(row.reserved),
      requests: Number(row.requests), halted: Boolean(row.halted), runId: row.run};
  }
  close() {this.#db.close();}
}
module.exports = {PersistentCreditLedger};
