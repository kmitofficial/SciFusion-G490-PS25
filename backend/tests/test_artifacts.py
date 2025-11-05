import os
from pathlib import Path

import pytest

fastapi = pytest.importorskip("fastapi")  # noqa: F401 - ensures FastAPI is available before importing router

from server.api.routers import jobs  # type: ignore
from server.core.config import settings


@pytest.fixture()
def temp_results_dirs(tmp_path, monkeypatch):
    """Create isolated results directories and point settings at them."""
    results_dir = tmp_path / "results"
    sample_dir = tmp_path / "resultsSample"
    results_dir.mkdir()
    sample_dir.mkdir()

    monkeypatch.setattr(settings, "RESULTS_DIR", str(results_dir))
    monkeypatch.setattr(settings, "RESULTS_SAMPLE_DIR", str(sample_dir))

    return results_dir, sample_dir


def _seed_job_folder(results_dir: Path, job_id: str, folder_name: str) -> Path:
    job_root = results_dir / f"api_job_{job_id}"
    target = job_root / folder_name
    target.mkdir(parents=True)

    (target / "experiment.py").write_text("print('hello world')\n", encoding="utf-8")
    (target / "notes.txt").write_text("notes", encoding="utf-8")

    logs_dir = target / "run_0"
    logs_dir.mkdir(parents=True)
    (logs_dir / "final_info.json").write_text("{}", encoding="utf-8")

    return target


def test_resolve_folder_path_prefers_results_path(temp_results_dirs):
    results_dir, _ = temp_results_dirs
    job_id = "job123"
    folder_name = "20251105_140026_adaptive_stylistic_embedding"
    folder = _seed_job_folder(results_dir, job_id, folder_name)

    job_doc = {
        "request": {},
        "experiment_results": [
            {
                "folder_name": folder_name,
                "results_path": f"api_job_{job_id}/{folder_name}",
            }
        ],
    }

    resolved = jobs._resolve_folder_path(job_doc, job_id, job_doc["experiment_results"][0]["results_path"])

    assert resolved == folder.resolve()


def test_build_tree_lists_files(temp_results_dirs):
    results_dir, _ = temp_results_dirs
    job_id = "job456"
    folder_name = "idea_folder"
    folder = _seed_job_folder(results_dir, job_id, folder_name)

    tree_nodes = jobs._build_tree(folder, folder)
    names = {(node.name, node.type) for node in tree_nodes}

    assert ("experiment.py", "file") in names
    assert ("run_0", "directory") in names


def test_safe_resolve_prevents_escape(temp_results_dirs):
    results_dir, _ = temp_results_dirs
    base = results_dir / "api_job_test" / "example"
    base.mkdir(parents=True)

    with pytest.raises(jobs.HTTPException):
        jobs._safe_resolve_path(base, base.parent.parent / "evil.txt")
