from __future__ import annotations

import sqlite3
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from threading import RLock

from app.config import Settings
from app.domain import ReconciliationCase


class CaseStore(ABC):
    @abstractmethod
    def get(self, case_id: str) -> ReconciliationCase | None: ...

    @abstractmethod
    def put(self, case: ReconciliationCase) -> None: ...

    @abstractmethod
    def list(self) -> list[ReconciliationCase]: ...

    @abstractmethod
    def delete(self, case_id: str) -> None: ...

    @abstractmethod
    def mutate(
        self,
        case_id: str,
        default_factory: Callable[[], ReconciliationCase],
        mutation: Callable[[ReconciliationCase], ReconciliationCase],
    ) -> ReconciliationCase: ...


class SQLiteCaseStore(CaseStore):
    """Thread-safe local persistence with atomic SQLite transactions."""

    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()
        for attempt in range(20):
            try:
                with self._connect() as conn:
                    conn.execute("PRAGMA journal_mode=WAL")
                    conn.execute(
                        "CREATE TABLE IF NOT EXISTS cases "
                        "(id TEXT PRIMARY KEY, updated_at TEXT NOT NULL, body TEXT NOT NULL)"
                    )
                    conn.execute(
                        "CREATE TABLE IF NOT EXISTS case_quarantine "
                        "(id TEXT NOT NULL, quarantined_at TEXT NOT NULL, "
                        "body TEXT NOT NULL, error TEXT NOT NULL)"
                    )
                break
            except sqlite3.OperationalError as error:
                if "locked" not in str(error).lower() or attempt == 19:
                    raise
                time.sleep(0.1 * (attempt + 1))

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, timeout=10)
        conn.execute("PRAGMA busy_timeout=10000")
        return conn

    def get(self, case_id: str) -> ReconciliationCase | None:
        with self._lock, self._connect() as conn:
            row = conn.execute("SELECT body FROM cases WHERE id = ?", (case_id,)).fetchone()
            if not row:
                return None
            try:
                return ReconciliationCase.model_validate_json(row[0])
            except ValueError as error:
                self._quarantine(conn, case_id, row[0], error)
                return None

    def put(self, case: ReconciliationCase) -> None:
        body = case.model_dump_json()
        with self._lock, self._connect() as conn:
            conn.execute(
                "INSERT INTO cases(id, updated_at, body) VALUES(?, ?, ?) "
                "ON CONFLICT(id) DO UPDATE SET updated_at=excluded.updated_at, body=excluded.body",
                (case.id, case.updated_at.isoformat(), body),
            )

    def list(self) -> list[ReconciliationCase]:
        with self._lock, self._connect() as conn:
            rows = conn.execute("SELECT id, body FROM cases ORDER BY updated_at DESC").fetchall()
            cases = []
            for case_id, body in rows:
                try:
                    cases.append(ReconciliationCase.model_validate_json(body))
                except ValueError as error:
                    self._quarantine(conn, case_id, body, error)
            return cases

    @staticmethod
    def _quarantine(conn: sqlite3.Connection, case_id: str, body: str, error: ValueError) -> None:
        conn.execute(
            "INSERT INTO case_quarantine(id, quarantined_at, body, error) VALUES(?, ?, ?, ?)",
            (case_id, datetime.now(UTC).isoformat(), body, str(error)[:1000]),
        )
        conn.execute("DELETE FROM cases WHERE id = ?", (case_id,))

    def delete(self, case_id: str) -> None:
        with self._lock, self._connect() as conn:
            conn.execute("DELETE FROM cases WHERE id = ?", (case_id,))

    def mutate(
        self,
        case_id: str,
        default_factory: Callable[[], ReconciliationCase],
        mutation: Callable[[ReconciliationCase], ReconciliationCase],
    ) -> ReconciliationCase:
        """Serialize a read-modify-write transition across threads and processes."""
        with self._lock, self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                row = conn.execute("SELECT body FROM cases WHERE id = ?", (case_id,)).fetchone()
                case = ReconciliationCase.model_validate_json(row[0]) if row else default_factory()
                updated = mutation(case)
                conn.execute(
                    "INSERT INTO cases(id, updated_at, body) VALUES(?, ?, ?) "
                    "ON CONFLICT(id) DO UPDATE SET updated_at=excluded.updated_at, body=excluded.body",
                    (updated.id, updated.updated_at.isoformat(), updated.model_dump_json()),
                )
                conn.execute("COMMIT")
                return updated
            except Exception:
                conn.execute("ROLLBACK")
                raise


class FirestoreCaseStore(CaseStore):
    """Production persistence using Cloud Firestore and Application Default Credentials."""

    def __init__(self, settings: Settings):
        from google.cloud import firestore

        self.firestore = firestore
        self.client = firestore.Client(
            project=settings.google_cloud_project,
            database=settings.firestore_database,
        )
        self.collection = self.client.collection("realitycheck_cases")

    def get(self, case_id: str) -> ReconciliationCase | None:
        snapshot = self.collection.document(case_id).get()
        return ReconciliationCase.model_validate(snapshot.to_dict()) if snapshot.exists else None

    def put(self, case: ReconciliationCase) -> None:
        self.collection.document(case.id).set(case.model_dump(mode="json"))

    def list(self) -> list[ReconciliationCase]:
        query = self.collection.order_by("updated_at", direction="DESCENDING").limit(100)
        return [ReconciliationCase.model_validate(doc.to_dict()) for doc in query.stream()]

    def delete(self, case_id: str) -> None:
        self.collection.document(case_id).delete()

    def mutate(
        self,
        case_id: str,
        default_factory: Callable[[], ReconciliationCase],
        mutation: Callable[[ReconciliationCase], ReconciliationCase],
    ) -> ReconciliationCase:
        transaction = self.client.transaction()
        document = self.collection.document(case_id)

        @self.firestore.transactional
        def update_in_transaction(txn):
            snapshot = document.get(transaction=txn)
            case = (
                ReconciliationCase.model_validate(snapshot.to_dict())
                if snapshot.exists
                else default_factory()
            )
            updated = mutation(case)
            txn.set(document, updated.model_dump(mode="json"))
            return updated

        return update_in_transaction(transaction)


def create_store(settings: Settings) -> CaseStore:
    if settings.realitycheck_store.lower() == "firestore":
        return FirestoreCaseStore(settings)
    return SQLiteCaseStore(settings.local_db_path)
