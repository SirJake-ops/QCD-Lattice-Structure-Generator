"""SQLite catalogue with a single process-owning worker and cancellable subprocesses."""
from __future__ import annotations

import fcntl
import json
import sqlite3
import shutil
import subprocess
import threading
import time
import uuid
import h5py
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from .analyze import analyze_run
from .artifacts import pack_stream, provenance, seal, write_json
from .contracts import Job, SimulationRequest

ROOT = Path(__file__).resolve().parents[1]


def now():
    return datetime.now(timezone.utc).isoformat()


class JobManager:
    def __init__(self, data: Path, simulator: Path):
        self.data = data.resolve()
        self.simulator = simulator.resolve()
        self.data.mkdir(parents=True, exist_ok=True)
        (self.data / "runs").mkdir(exist_ok=True)
        (self.data / "models").mkdir(exist_ok=True)
        self.dbpath = self.data / "jobs.sqlite3"
        with self.connection() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY, state TEXT NOT NULL, request TEXT NOT NULL,
                created TEXT NOT NULL, updated TEXT NOT NULL, progress REAL NOT NULL DEFAULT 0,
                error TEXT)""")
        self.mutex = threading.RLock()
        self.stop_event = threading.Event()
        self.process = None
        self.active = None
        self.thread = None
        self.worker_lock = None

    @contextmanager
    def connection(self):
        db = sqlite3.connect(self.dbpath, timeout=15)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def start(self):
        self.worker_lock = (self.data / "worker.lock").open("a+")
        try:
            fcntl.flock(self.worker_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            self.worker_lock.close()
            raise RuntimeError("Another worker owns this catalogue; use one uvicorn process")
        # A previous process may have died while owning a child. Its session cannot
        # be adopted safely: mark the run failed and retain its incomplete stream.
        with self.connection() as db:
            db.execute("UPDATE jobs SET state='failed', error=?, updated=? WHERE state='running'",
                       ("Worker interrupted; partial outputs retained, submit a new run", now()))
        self.thread = threading.Thread(target=self._loop, daemon=True, name="lattice-worker")
        self.thread.start()

    def close(self):
        self.stop_event.set()
        with self.mutex:
            if self.process and self.process.poll() is None:
                self.process.terminate()
        if self.thread:
            self.thread.join(timeout=30)
        if self.worker_lock:
            self.worker_lock.close()

    def submit(self, request: SimulationRequest) -> Job:
        if not self.simulator.is_file():
            raise ValueError(f"Simulator missing: build {self.simulator}")
        # Bound memory/disk for workstation execution; don't create enormous maps accidentally.
        cells = request.extents[0] * request.extents[1] if request.measure_field else 0
        estimate = request.chains * request.measurements * (8 * (8 + request.max_r * request.max_t + 2 * cells))
        if estimate > 512 * 1024 * 1024:
            raise ValueError("Requested measurement arrays exceed the 512 MiB local job budget")
        run_id = uuid.uuid4().hex
        directory = self.data / "runs" / run_id
        directory.mkdir()
        write_json(directory / "request.json", request.model_dump(mode="json"))
        (directory / "resolved.toml").write_text(request.toml())
        # A queued run must keep the exact executable even if the workspace is rebuilt.
        snapshot = directory / "simulator.bin"
        shutil.copy2(self.simulator, snapshot)
        write_json(directory / "provenance.json", provenance(ROOT, snapshot))
        seal(directory, run_id, False)
        stamp = now()
        with self.connection() as db:
            db.execute("INSERT INTO jobs(id,state,request,created,updated) VALUES(?,?,?,?,?)",
                       (run_id, "queued", request.model_dump_json(), stamp, stamp))
        return self.get(run_id)

    @staticmethod
    def _job(row):
        if row is None: raise KeyError("Unknown job")
        row = dict(row)
        row["request"] = json.loads(row["request"])
        return Job.model_validate(row)

    def get(self, run_id: str) -> Job:
        with self.connection() as db:
            return self._job(db.execute("SELECT * FROM jobs WHERE id=?", (run_id,)).fetchone())

    def list(self) -> list[Job]:
        with self.connection() as db:
            return [self._job(row) for row in db.execute("SELECT * FROM jobs ORDER BY created DESC LIMIT 100")]

    def cancel(self, run_id: str) -> Job:
        with self.mutex:
            job = self.get(run_id)
            if job.state in ("queued", "running"):
                self._update(run_id, state="cancelled", error="Cancelled by user; partial output is incomplete")
                if self.active == run_id and self.process and self.process.poll() is None:
                    self.process.terminate()
        return self.get(run_id)

    def _update(self, run_id: str, **values):
        values["updated"] = now()
        with self.connection() as db:
            db.execute("UPDATE jobs SET " + ",".join(k + "=?" for k in values) + " WHERE id=?",
                       [*values.values(), run_id])

    def _loop(self):
        while not self.stop_event.is_set():
            with self.mutex, self.connection() as db:
                row = db.execute("SELECT id FROM jobs WHERE state='queued' ORDER BY created LIMIT 1").fetchone()
                if row:
                    db.execute("UPDATE jobs SET state='running', updated=? WHERE id=?", (now(), row[0]))
                    self.active = row[0]
            if row is None:
                self.stop_event.wait(.15)
                continue
            self._run(row[0])
            with self.mutex:
                self.active = None
                self.process = None

    def _run(self, run_id):
        job = self.get(run_id)
        request = job.request
        directory = self.data / "runs" / run_id
        started = time.monotonic()
        try:
            args = [str(directory / "simulator.bin"), str(directory / "resolved.toml"), str(request.separation),
                    str(request.field_t), *(str(p) for p in request.probe),
                    "1" if request.start == "hot" else "0", "1" if request.measure_field else "0", "0"]
            with (directory / "simulator.log").open("w") as errors, (directory / "measurements.jsonl").open("w") as raw:
                with self.mutex:
                    if self.get(run_id).state == "cancelled": return
                    self.process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=errors, text=True, bufsize=1)
                count = 0
                for line in self.process.stdout:
                    raw.write(line)
                    if '"type":"measurement"' in line:
                        count += 1
                        if count % 8 == 0:
                            raw.flush()
                            self._update(run_id, progress=.9 * count / (request.chains * request.measurements))
                code = self.process.wait(timeout=10)
            cancelled = self.get(run_id).state == "cancelled" or self.stop_event.is_set()
            pack_stream(directory, request, complete=code == 0 and not cancelled)
            if cancelled:
                if self.get(run_id).state != "cancelled":
                    self._update(run_id, state="failed", error="Worker shut down; submit a new run")
                seal(directory, run_id, False)
                return
            if code:
                raise ValueError(f"Simulator exited {code}: " + (directory / "simulator.log").read_text()[-2000:])
            result, field = analyze_run(directory)
            with self.mutex:
                if self.get(run_id).state == "cancelled":
                    with h5py.File(directory / "measurements.h5", "r+") as h: h.attrs["complete"] = False
                    seal(directory, run_id, False)
                    return
                write_json(directory / "analysis.json", result.model_dump(mode="json"))
                write_json(directory / "field.json", field.model_dump(mode="json"))
                write_json(directory / "timing.json", {"elapsed_seconds": time.monotonic() - started,
                           "measurements": count, "seconds_per_measurement": (time.monotonic() - started) / count})
                seal(directory, run_id, True)
                self._update(run_id, state="completed", progress=1.)
        except Exception as e:
            if self.process and self.process.poll() is None:
                self.process.terminate()
                self.process.wait(timeout=10)
            if (directory / "measurements.jsonl").exists():
                try: pack_stream(directory, request, False)
                except Exception: pass
            if self.get(run_id).state != "cancelled": self._update(run_id, state="failed", error=str(e))
            seal(directory, run_id, False)
