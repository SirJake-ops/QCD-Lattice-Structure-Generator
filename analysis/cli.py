from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from .artifacts import checksum, verify, write_json
from .contracts import AnalysisSettings, SimulationRequest
from .jobs import JobManager, ROOT


def wait(manager, job):
    while True:
        current = manager.get(job.id)
        if current.state in ("completed", "failed", "cancelled"):
            print(current.model_dump_json(indent=2))
            if current.state != "completed": raise RuntimeError(current.error)
            return manager.data / "runs" / current.id
        time.sleep(.2)


def main():
    parser = argparse.ArgumentParser(description="Local pure-gauge lattice explorer")
    parser.add_argument("--data", type=Path, default=ROOT / "results")
    parser.add_argument("--simulator", type=Path, default=ROOT / "build/local-release/qcd_simulate")
    sub = parser.add_subparsers(dest="command", required=True)
    serve = sub.add_parser("serve"); serve.add_argument("--port", type=int, default=8000)
    run = sub.add_parser("run"); run.add_argument("request", type=Path)
    pilot = sub.add_parser("pilot"); pilot.add_argument("--group", choices=["u1", "su3"], default="u1")
    corpus = sub.add_parser("corpus"); corpus.add_argument("grid", type=Path)
    dataset = sub.add_parser("dataset"); dataset.add_argument("--group", choices=["u1", "su3"], required=True)
    train = sub.add_parser("train"); train.add_argument("dataset", type=Path)
    inspect = sub.add_parser("verify"); inspect.add_argument("run", type=Path)
    fields = sub.add_parser("compare-fields"); fields.add_argument("runs", type=Path, nargs="+")
    reanalyze = sub.add_parser("reanalyze"); reanalyze.add_argument("run", type=Path); reanalyze.add_argument("--fit-min", type=int, required=True); reanalyze.add_argument("--fit-max", type=int, required=True)
    args = parser.parse_args()
    if args.command == "serve":
        import uvicorn
        from .service import create_app
        uvicorn.run(create_app(args.data, args.simulator), host="127.0.0.1", port=args.port)
        return
    if args.command == "verify":
        print(json.dumps(verify(args.run), indent=2)); return
    if args.command == "compare-fields":
        from .field_validation import compare_fields
        result = compare_fields(args.runs)
        out = args.data / "field-validation" / str(time.time_ns())
        out.mkdir(parents=True)
        write_json(out / "report.json", result)
        print(json.dumps(result, indent=2)); print(out); return
    if args.command == "reanalyze":
        from .analyze import analyze_run
        verify(args.run)
        settings = AnalysisSettings(fit_min=args.fit_min, fit_max=args.fit_max)
        result, field = analyze_run(args.run, settings)
        # Derived revisions never alter the sealed source bundle.
        out = args.data / "reanalyses" / f"{args.run.name}-{time.time_ns()}"
        out.mkdir(parents=True)
        write_json(out / "analysis.json", result.model_dump(mode="json"))
        write_json(out / "field.json", field.model_dump(mode="json"))
        write_json(out / "source.json", {"manifest_sha256": checksum(args.run / "manifest.json")})
        print(out); return
    if args.command == "dataset":
        from .learning import build_dataset
        print(build_dataset(args.data, args.group)); return
    if args.command == "train":
        from .learning import train_model
        print(train_model(args.data, args.dataset)); return
    manager = JobManager(args.data, args.simulator)
    manager.start()
    try:
        if args.command == "run":
            wait(manager, manager.submit(SimulationRequest.model_validate_json(args.request.read_text())))
        elif args.command == "pilot":
            req = SimulationRequest(gauge_group=args.group, beta=1.2 if args.group == "u1" else 5.7,
                warmup_sweeps=40, measurements=64, max_r=2)
            directory = wait(manager, manager.submit(req))
            print((directory / "timing.json").read_text())
            print((directory / "analysis.json").read_text())
        else:
            grid = json.loads(args.grid.read_text())
            requests = [SimulationRequest.model_validate(r) for r in grid["requests"]]
            if len(requests) > 64: raise ValueError("At most 64 jobs per bounded corpus")
            if any(r.chains < 4 for r in requests): raise ValueError("Corpus needs at least four chains per point")
            for req in requests:
                wait(manager, manager.submit(req))
    except KeyboardInterrupt:
        for job in manager.list():
            if job.state in ("running", "queued"): manager.cancel(job.id)
        raise
    finally:
        manager.close()


if __name__ == "__main__": main()
