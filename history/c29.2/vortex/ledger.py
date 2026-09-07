import sqlite3, json, hashlib, datetime as dt
from pathlib import Path

class ImmutableLedger:
    def __init__(self, path):
        self.path=Path(path)
        self.con=sqlite3.connect(self.path)
        self.con.execute("""CREATE TABLE IF NOT EXISTS receipts(
          receipt_id TEXT PRIMARY KEY, kind TEXT NOT NULL, payload_json TEXT NOT NULL,
          sha256 TEXT NOT NULL UNIQUE, created_at TEXT NOT NULL)""")
        self.con.execute("""CREATE TABLE IF NOT EXISTS evaluations(
          eval_id TEXT PRIMARY KEY, receipt_id TEXT NOT NULL, outcome_json TEXT NOT NULL,
          score_json TEXT NOT NULL, verdict TEXT NOT NULL, created_at TEXT NOT NULL)""")
        self.con.commit()

    @staticmethod
    def canonical(payload):
        return json.dumps(payload,sort_keys=True,separators=(",",":"))

    def freeze(self, kind, payload):
        body=self.canonical(payload)
        sha=hashlib.sha256(body.encode()).hexdigest()
        rid=sha[:24]
        self.con.execute("INSERT INTO receipts VALUES (?,?,?,?,?)",
            (rid,kind,body,sha,dt.datetime.now(dt.timezone.utc).isoformat()))
        self.con.commit()
        return {"receipt_id":rid,"sha256":sha}

    def evaluate_once(self, receipt_id, outcome, score, verdict):
        if self.con.execute("SELECT 1 FROM evaluations WHERE receipt_id=?",(receipt_id,)).fetchone():
            raise ValueError("receipt already evaluated; historical result is immutable")
        payload=f"{receipt_id}|{self.canonical(outcome)}|{self.canonical(score)}|{verdict}"
        eid=hashlib.sha256(payload.encode()).hexdigest()[:24]
        self.con.execute("INSERT INTO evaluations VALUES (?,?,?,?,?,?)",
            (eid,receipt_id,self.canonical(outcome),self.canonical(score),verdict,
             dt.datetime.now(dt.timezone.utc).isoformat()))
        self.con.commit()
        return eid
