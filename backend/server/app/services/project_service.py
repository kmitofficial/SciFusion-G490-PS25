"""Domain logic for provisioning AutoAD experiment workspaces."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List

from app.models.project import (
    ProjectCreateRequest,
    ProjectDetail,
    ProjectSummary,
)

CONFIG_FILENAME = "project_config.json"
SEED_IDEAS_FILENAME = "seed_ideas.json"
PROMPT_FILENAME = "prompt.json"
EXPERIMENT_FILENAME = "experiment.py"
RUN_DIRNAME = "run_0"
RUN_BASELINE_FILENAME = "final_info.json"
RUN_SCRIPT_FILENAME = "experiment.py"
NOTES_FILENAME = "notes.txt"

DEFAULT_EXPERIMENT_CODE = """# Auto-generated baseline experiment.\n# The AutoAD system will iterate on this scaffold.\nimport torch\n\n\ndef main():\n    print("Baseline experiment placeholder.")\n\n\nif __name__ == "__main__":\n    main()\n"""

DEFAULT_NOTES_CONTENT = """# Auto-generated notes\n## Run 0\nResults: {'baseline_metric': {'means': [0.0], 'stds': [0.0]}}\nDescription: Default baseline stub.\n"""


@dataclass(frozen=True)
class Paths:
    """Convenience wrapper for frequently used directories."""

    backend_root: Path

    @property
    def examples_root(self) -> Path:
        return self.backend_root / "examples"

    @property
    def results_root(self) -> Path:
        return self.backend_root / "results"


class ProjectExistsError(RuntimeError):
    """Raised when attempting to provision a project that already exists."""


class ProjectNotFoundError(RuntimeError):
    """Raised when reading a project that cannot be found on disk."""


PATHS = Paths(backend_root=Path(__file__).resolve().parents[3])


def _legacy_project_exists(slug: str) -> bool:
    """Return True if a baked-in example directory exists without config."""

    base_dir = PATHS.examples_root / slug
    return base_dir.exists() and not (base_dir / CONFIG_FILENAME).exists()


def _bootstrap_legacy_project(slug: str) -> ProjectDetail:
    """Generate a minimal config for repo-provided examples missing metadata."""

    base_dir = PATHS.examples_root / slug
    if not base_dir.exists():
        raise ProjectNotFoundError(f"Project '{slug}' does not exist")

    results_dir = PATHS.results_root / slug
    results_dir.mkdir(parents=True, exist_ok=True)

    created_at = datetime.utcnow()
    display_name = slug.replace("-", " ").title()
    topic = display_name
    objective = (
        "Run AutoAD experiments using the pre-seeded example shipped with the repository."
    )
    success_metric = "Refer to run_0/final_info.json for baseline metrics."

    config_payload = {
        "name": display_name,
        "slug": slug,
        "topic": topic,
        "objective": objective,
        "success_metric": success_metric,
        "user_persona": None,
        "data_sources": [],
        "constraints": [],
        "preferred_modalities": [],
        "enable_rag": False,
        "seed": 2025,
        "rag_max_papers": 20,
        "rag_memory_papers": 10,
        "notes": "Auto-generated legacy project config.",
        "created_at": created_at.isoformat(),
    }
    write_json(base_dir / CONFIG_FILENAME, config_payload)

    return ProjectDetail(
        name=display_name,
        slug=slug,
        topic=topic,
        objective=objective,
        success_metric=success_metric,
        user_persona=None,
        data_sources=[],
        constraints=[],
        preferred_modalities=[],
        enable_rag=False,
        seed=2025,
        rag_max_papers=20,
        rag_memory_papers=10,
        notes="Auto-generated legacy project config.",
        created_at=created_at,
        base_dir=str(base_dir),
        results_dir=str(results_dir),
    )


def slugify(name: str) -> str:
    """Create a filesystem-friendly slug from a project name."""
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "project"


def ensure_parent(path: Path) -> None:
    """Create parent directories for the given path."""
    path.parent.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, payload: dict) -> None:
    ensure_parent(path)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=4)


def write_text(path: Path, content: str) -> None:
    ensure_parent(path)
    path.write_text(content, encoding="utf-8")


def create_project(request: ProjectCreateRequest) -> ProjectDetail:
    """Provision a brand-new experiment scaffold for AutoAD."""
    slug = slugify(request.name)
    base_dir = PATHS.examples_root / slug
    results_dir = PATHS.results_root / slug

    if base_dir.exists():
        if _legacy_project_exists(slug):
            return _bootstrap_legacy_project(slug)
        raise ProjectExistsError(f"A project with slug '{slug}' already exists.")

    created_at = datetime.utcnow()

    # Build directory skeleton
    (base_dir / RUN_DIRNAME).mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    # Persist project config for later retrieval
    config_path = base_dir / CONFIG_FILENAME
    config_payload = {
        "name": request.name,
        "slug": slug,
        "topic": request.topic,
        "objective": request.objective,
        "success_metric": request.success_metric,
        "user_persona": request.user_persona,
        "data_sources": request.data_sources,
        "constraints": request.constraints,
        "preferred_modalities": request.preferred_modalities,
        "enable_rag": request.enable_rag,
        "seed": request.seed,
        "rag_max_papers": request.rag_max_papers,
        "rag_memory_papers": request.rag_memory_papers,
        "notes": request.notes,
        "created_at": created_at.isoformat(),
    }
    write_json(config_path, config_payload)

    # Seed idea scaffold
    seed_ideas_path = base_dir / SEED_IDEAS_FILENAME
    seed_ideas_payload = [
        {
            "Name": "Baseline",
            "Title": f"Baseline for {request.name}",
            "Summary": request.objective,
            "Experiment": "Establish a baseline metric before applying AutoAD iterations.",
            "Method": "Baseline implementation placeholder.",
            "Data": request.data_sources,
            "Constraints": request.constraints,
        }
    ]
    write_json(seed_ideas_path, seed_ideas_payload)

    # Prompt scaffold
    prompt_path = base_dir / PROMPT_FILENAME
    prompt_payload = {
        "system": (
            "You are an AI research assistant tasked with designing novel algorithms "
            "for scientific discovery. Respond with detailed, implementable ideas."
        ),
        "task_description": request.objective,
        "success_metric": request.success_metric,
        "context": {
            "topic": request.topic,
            "user_persona": request.user_persona,
            "data_sources": request.data_sources,
            "constraints": request.constraints,
            "preferred_modalities": request.preferred_modalities,
        },
        "enable_rag": request.enable_rag,
        "rag_params": {
            "max_papers": request.rag_max_papers,
            "memory_papers": request.rag_memory_papers,
        },
        "seed": request.seed,
        "notes": request.notes,
    }
    write_json(prompt_path, prompt_payload)

    # Experiment scaffold
    write_text(base_dir / EXPERIMENT_FILENAME, DEFAULT_EXPERIMENT_CODE)
    run_dir = base_dir / RUN_DIRNAME
    write_text(run_dir / RUN_SCRIPT_FILENAME, DEFAULT_EXPERIMENT_CODE)

    run_info_payload = {
        "baseline_metric": {
            "means": [0.0],
            "stds": [0.0],
        }
    }
    write_json(run_dir / RUN_BASELINE_FILENAME, run_info_payload)
    write_text(base_dir / NOTES_FILENAME, DEFAULT_NOTES_CONTENT)

    project_detail = ProjectDetail(
        name=request.name,
        slug=slug,
        topic=request.topic,
        objective=request.objective,
        success_metric=request.success_metric,
        user_persona=request.user_persona,
        data_sources=request.data_sources,
        constraints=request.constraints,
        preferred_modalities=request.preferred_modalities,
        enable_rag=request.enable_rag,
    seed=request.seed,
        rag_max_papers=request.rag_max_papers,
        rag_memory_papers=request.rag_memory_papers,
        notes=request.notes,
        created_at=created_at,
        base_dir=str(base_dir),
        results_dir=str(results_dir),
    )
    return project_detail


def list_projects() -> List[ProjectSummary]:
    """Return a summary of all scaffolded projects."""
    summaries: List[ProjectSummary] = []
    if not PATHS.examples_root.exists():
        return summaries

    for config_path in PATHS.examples_root.glob("*/" + CONFIG_FILENAME):
        with config_path.open(encoding="utf-8") as handle:
            config = json.load(handle)
        summaries.append(
            ProjectSummary(
                name=config["name"],
                slug=config["slug"],
                topic=config["topic"],
                created_at=datetime.fromisoformat(config["created_at"]),
                enable_rag=config.get("enable_rag", False),
            )
        )

    summaries.sort(key=lambda item: item.created_at, reverse=True)
    return summaries


def get_project(slug: str) -> ProjectDetail:
    """Load a previously scaffolded project configuration."""
    config_path = PATHS.examples_root / slug / CONFIG_FILENAME
    if not config_path.exists():
        return _bootstrap_legacy_project(slug)

    with config_path.open(encoding="utf-8") as handle:
        config = json.load(handle)

    return ProjectDetail(
        name=config["name"],
        slug=config["slug"],
        topic=config["topic"],
        objective=config["objective"],
        success_metric=config["success_metric"],
        user_persona=config.get("user_persona"),
        data_sources=config.get("data_sources", []),
        constraints=config.get("constraints", []),
        preferred_modalities=config.get("preferred_modalities", []),
        enable_rag=config.get("enable_rag", False),
    seed=config.get("seed", 2025),
        rag_max_papers=config.get("rag_max_papers", 20),
        rag_memory_papers=config.get("rag_memory_papers", 10),
        notes=config.get("notes"),
        created_at=datetime.fromisoformat(config["created_at"]),
        base_dir=str(PATHS.examples_root / slug),
        results_dir=str(PATHS.results_root / slug),
    )
