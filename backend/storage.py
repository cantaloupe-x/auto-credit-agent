import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


SCHEMA = """
CREATE TABLE IF NOT EXISTS applications (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    id_number TEXT,
    city TEXT,
    occupation TEXT,
    vehicle_model TEXT,
    vehicle_source TEXT,
    income REAL NOT NULL,
    monthly_debt REAL NOT NULL,
    vehicle_price REAL NOT NULL,
    down_payment REAL NOT NULL,
    loan_amount REAL NOT NULL,
    loan_term INTEGER NOT NULL,
    work_years REAL NOT NULL,
    recent_overdue INTEGER NOT NULL,
    authorized INTEGER NOT NULL,
    status TEXT NOT NULL,
    score INTEGER NOT NULL,
    risk_level TEXT NOT NULL,
    recommendation TEXT NOT NULL,
    reasons TEXT NOT NULL,
    model_version TEXT NOT NULL,
    review_decision TEXT,
    review_comment TEXT,
    reviewer TEXT,
    reviewed_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    actor TEXT NOT NULL,
    details TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (application_id) REFERENCES applications(id)
);
"""


class ApplicationStore:
    def __init__(self, database_path):
        self.database_path = Path(database_path)

    def _connect(self):
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def initialize(self):
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(SCHEMA)

    def is_empty(self):
        with self._connect() as connection:
            count = connection.execute("SELECT COUNT(*) FROM applications").fetchone()[0]
        return count == 0

    def create_application(self, application, assessment, application_id=None, actor="申请人"):
        now = _now()
        application_id = application_id or _new_application_id()
        status = "needs_more_info" if assessment["score"] == 0 else "pending_review"
        values = {
            **application,
            "id": application_id,
            "recent_overdue": int(application.get("recent_overdue", False)),
            "authorized": int(application.get("authorized", True)),
            "status": status,
            "score": assessment["score"],
            "risk_level": assessment["level"],
            "recommendation": assessment["recommendation"],
            "reasons": json.dumps(assessment["reasons"], ensure_ascii=False),
            "model_version": assessment["model_version"],
            "created_at": now,
            "updated_at": now,
        }
        columns = (
            "id", "name", "id_number", "city", "occupation", "vehicle_model",
            "vehicle_source", "income", "monthly_debt", "vehicle_price",
            "down_payment", "loan_amount", "loan_term", "work_years",
            "recent_overdue", "authorized", "status", "score", "risk_level",
            "recommendation", "reasons", "model_version", "created_at", "updated_at",
        )
        placeholders = ", ".join(f":{column}" for column in columns)
        with self._connect() as connection:
            connection.execute(
                f"INSERT INTO applications ({', '.join(columns)}) VALUES ({placeholders})",
                values,
            )
            self._add_event(
                connection,
                application_id,
                "application_submitted",
                actor,
                {"status": status},
                now,
            )
            self._add_event(
                connection,
                application_id,
                "risk_assessed",
                "rule-v1.0",
                {
                    "score": assessment["score"],
                    "risk_level": assessment["level"],
                    "recommendation": assessment["recommendation"],
                    "reasons": assessment["reasons"],
                },
                now,
            )
        return self.get_application(application_id)

    def list_applications(self):
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM applications ORDER BY created_at DESC, id DESC"
            ).fetchall()
        return [_application_from_row(row) for row in rows]

    def get_application(self, application_id):
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM applications WHERE id = ?", (application_id,)
            ).fetchone()
        return _application_from_row(row) if row else None

    def review_application(self, application_id, decision, comment, reviewer):
        status_by_decision = {
            "approved": "approved",
            "needs_more_info": "needs_more_info",
            "rejected": "rejected",
        }
        now = _now()
        with self._connect() as connection:
            current = connection.execute(
                "SELECT status FROM applications WHERE id = ?", (application_id,)
            ).fetchone()
            if current is None:
                return None
            new_status = status_by_decision[decision]
            connection.execute(
                """
                UPDATE applications
                SET status = ?, review_decision = ?, review_comment = ?, reviewer = ?,
                    reviewed_at = ?, updated_at = ?
                WHERE id = ?
                """,
                (new_status, decision, comment, reviewer, now, now, application_id),
            )
            self._add_event(
                connection,
                application_id,
                "manual_reviewed",
                reviewer,
                {
                    "previous_status": current["status"],
                    "decision": decision,
                    "comment": comment,
                },
                now,
            )
        return self.get_application(application_id)

    def list_audit_events(self, application_id):
        with self._connect() as connection:
            exists = connection.execute(
                "SELECT 1 FROM applications WHERE id = ?", (application_id,)
            ).fetchone()
            if exists is None:
                return None
            rows = connection.execute(
                """
                SELECT id, application_id, event_type, actor, details, created_at
                FROM audit_events
                WHERE application_id = ?
                ORDER BY id
                """,
                (application_id,),
            ).fetchall()
        return [
            {**dict(row), "details": json.loads(row["details"])}
            for row in rows
        ]

    @staticmethod
    def _add_event(connection, application_id, event_type, actor, details, created_at):
        connection.execute(
            """
            INSERT INTO audit_events (application_id, event_type, actor, details, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                application_id,
                event_type,
                actor,
                json.dumps(details, ensure_ascii=False),
                created_at,
            ),
        )


def _application_from_row(row):
    application = dict(row)
    application["recent_overdue"] = bool(application["recent_overdue"])
    application["authorized"] = bool(application["authorized"])
    application["reasons"] = json.loads(application["reasons"])
    return application


def _new_application_id():
    date = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"CL-{date}-{uuid4().hex[:6].upper()}"


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
