import sqlite3
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from pathlib import Path

from app.config import Settings
from app.demo import create_demo_case, observe_bill, resolve, verify_credit
from app.store import SQLiteCaseStore


def initialize_store(path: str) -> int:
    return len(SQLiteCaseStore(Path(path)).list())


def test_atomic_mutations_survive_concurrent_workers(tmp_path):
    path = tmp_path / "concurrent.sqlite3"
    stores = [SQLiteCaseStore(path), SQLiteCaseStore(path)]
    case_id = "concurrent_case"
    stores[0].put(create_demo_case(case_id))

    def mutate_many(operation):
        with ThreadPoolExecutor(max_workers=16) as pool:
            list(
                pool.map(
                    lambda index: stores[index % 2].mutate(
                        case_id, lambda: create_demo_case(case_id), operation
                    ),
                    range(64),
                )
            )

    mutate_many(observe_bill)
    mutate_many(lambda case: resolve(case, approved=True))
    mutate_many(lambda case: verify_credit(case, demo_time_jump=True))

    final = stores[0].get(case_id)
    assert final is not None
    assert final.status == "recovered"
    assert final.recovered_amount == 350
    assert len(final.observations) == 1
    assert len(final.obligations) == 1
    assert final.audit_chain_valid()


def test_store_factory_defaults_to_local(tmp_path):
    settings = Settings(local_db_path=tmp_path / "factory.sqlite3")
    store = SQLiteCaseStore(settings.local_db_path)
    assert store.list() == []


def test_corrupt_state_is_quarantined_and_does_not_take_down_runtime(tmp_path):
    path = tmp_path / "corrupt.sqlite3"
    store = SQLiteCaseStore(path)
    with sqlite3.connect(path) as connection:
        connection.execute(
            "INSERT INTO cases(id, updated_at, body) VALUES(?, ?, ?)",
            ("broken", "2026-08-20T00:00:00Z", "{not-json"),
        )

    assert store.get("broken") is None
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM cases WHERE id='broken'").fetchone()[0] == 0
        assert (
            connection.execute("SELECT COUNT(*) FROM case_quarantine WHERE id='broken'").fetchone()[
                0
            ]
            == 1
        )


def test_multiple_worker_processes_can_boot_against_one_database(tmp_path):
    path = str(tmp_path / "multiworker.sqlite3")
    with ProcessPoolExecutor(max_workers=6) as pool:
        assert list(pool.map(initialize_store, [path] * 12)) == [0] * 12
