"""Round-trip parity checks for canonical JSON <-> XML conversion."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from app.x_to_demo.renderers import _dict_to_xml, _xml_to_dict

_PHASE_KEYS = ("feature_spec", "demo_spec", "code_spec")
_ARTIFACTS_ROOT = Path(__file__).resolve().parents[1] / "artifacts" / "x-to-demo"


def _latest_complete_run_dir() -> Path:
    if not _ARTIFACTS_ROOT.exists():
        pytest.skip(f"No local artifact directory at {_ARTIFACTS_ROOT}")

    run_dirs = sorted((path for path in _ARTIFACTS_ROOT.iterdir() if path.is_dir()), reverse=True)
    for run_dir in run_dirs:
        required_files = [run_dir / f"{phase}.json" for phase in _PHASE_KEYS]
        if all(path.exists() for path in required_files):
            return run_dir

    pytest.skip("No complete local run directory with JSON artifacts found")


def _load_json_payload(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise AssertionError(f"Expected object payload in {path}, got {type(payload).__name__}")
    return payload


def test_latest_canonical_json_roundtrips_through_xml_losslessly() -> None:
    run_dir = _latest_complete_run_dir()

    for phase in _PHASE_KEYS:
        json_payload = _load_json_payload(run_dir / f"{phase}.json")
        xml_text = _dict_to_xml(json_payload)
        round_tripped = _xml_to_dict(xml_text)

        assert round_tripped == json_payload, f"Round-trip mismatch for {phase} in {run_dir.name}"
