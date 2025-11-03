"""Service layer for launching AutoAD sessions and streaming pipeline events."""
from __future__ import annotations

import json
import logging
import os
import shutil
import threading
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from uuid import uuid4

from aider.coders import Coder
from aider.io import InputOutput
from aider.models import Model

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import PyMongoError

from dolphin_utils.experiments_utils import perform_experiments
from dolphin_utils.generate_ideas import check_idea_novelty, generate_ideas
from dolphin_utils.rag_tools.lit_review import collect_papers

from app.models.session import (
    PipelineStage,
    SessionCreateRequest,
    SessionEvent,
    SessionListItem,
    SessionStatus,
)
from app.services import project_service
from app.services.project_service import ProjectNotFoundError


NUM_REFLECTIONS = 3


class SessionNotFoundError(RuntimeError):
    """Raised when attempting to access a session that is not registered."""


@dataclass
class SessionState:
    """Mutable state tracked for each running or completed session."""

    session_id: str
    request: SessionCreateRequest
    project_slug: str
    stage: PipelineStage = PipelineStage.QUEUED
    started_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    completed: bool = False
    failed: bool = False
    error: Optional[str] = None
    events: List[SessionEvent] = field(default_factory=list)
    result_paths: List[str] = field(default_factory=list)


_sessions: Dict[str, SessionState] = {}
_sessions_lock = threading.Lock()


logger = logging.getLogger("uvicorn.error").getChild("session_service")
logger.setLevel(logging.INFO)

MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://127.0.0.1:27017")
MONGODB_DB = os.environ.get("MONGODB_DB", "autoad")
MONGODB_COLLECTION = os.environ.get("MONGODB_SESSION_COLLECTION", "sessions")

_mongo_client: Optional[MongoClient] = None
_sessions_collection: Optional[Collection] = None

try:  # pragma: no cover - connection handled at runtime
    _mongo_client = MongoClient(MONGODB_URI)
    _sessions_collection = _mongo_client[MONGODB_DB][MONGODB_COLLECTION]
    _sessions_collection.create_index("session_id", unique=True)
except Exception as exc:  # pragma: no cover - best-effort logging
    logger.warning("MongoDB session persistence disabled: %s", exc)
    _sessions_collection = None


def _state_to_document(state: SessionState) -> dict:
    """Serialize the in-memory session state to a MongoDB-friendly document."""

    return {
        "session_id": state.session_id,
        "project_slug": state.project_slug,
        "request": state.request.model_dump(),
        "stage": state.stage.value,
        "started_at": state.started_at.isoformat(),
        "updated_at": state.updated_at.isoformat(),
        "completed": state.completed,
        "failed": state.failed,
        "error": state.error,
        "events": [
            {
                "timestamp": event.timestamp.isoformat(),
                "stage": event.stage.value,
                "message": event.message,
                "metadata": event.metadata,
            }
            for event in state.events
        ],
        "result_paths": list(state.result_paths),
    }


def _persist_state(state: SessionState) -> None:
    """Write the latest session snapshot to MongoDB (best-effort)."""

    if _sessions_collection is None:
        return
    try:
        _sessions_collection.update_one(
            {"session_id": state.session_id},
            {"$set": _state_to_document(state)},
            upsert=True,
        )
    except PyMongoError as exc:  # pragma: no cover - best-effort logging
        logger.warning("Failed to persist session %s: %s", state.session_id, exc)


def _document_to_status(document: dict) -> SessionStatus:
    """Hydrate a SessionStatus model from a MongoDB document."""

    events = [
        SessionEvent(
            timestamp=datetime.fromisoformat(event_doc["timestamp"]),
            stage=PipelineStage(event_doc["stage"]),
            message=event_doc["message"],
            metadata=event_doc.get("metadata", {}),
        )
        for event_doc in document.get("events", [])
    ]

    return SessionStatus(
        session_id=document["session_id"],
        project_slug=document["project_slug"],
        stage=PipelineStage(document["stage"]),
        started_at=datetime.fromisoformat(document["started_at"]),
        updated_at=datetime.fromisoformat(document["updated_at"]),
        completed=document.get("completed", False),
        failed=document.get("failed", False),
        error=document.get("error"),
        events=events,
        result_paths=document.get("result_paths", []),
    )


def _document_to_list_item(document: dict) -> SessionListItem:
    """Convert storage document into a lightweight listing payload."""

    return SessionListItem(
        session_id=document["session_id"],
        project_slug=document["project_slug"],
        stage=PipelineStage(document["stage"]),
        started_at=datetime.fromisoformat(document["started_at"]),
        updated_at=datetime.fromisoformat(document["updated_at"]),
        completed=document.get("completed", False),
        failed=document.get("failed", False),
    )


def _state_to_status(state: SessionState) -> SessionStatus:
    """Convert an in-memory SessionState to the API response model."""

    return SessionStatus(
        session_id=state.session_id,
        project_slug=state.project_slug,
        stage=state.stage,
        started_at=state.started_at,
        updated_at=state.updated_at,
        completed=state.completed,
        failed=state.failed,
        error=state.error,
        events=list(state.events),
        result_paths=list(state.result_paths),
    )


def _load_status_from_store(session_id: str) -> Optional[SessionStatus]:
    """Fetch a persisted session snapshot from MongoDB."""

    if _sessions_collection is None:
        return None
    document = _sessions_collection.find_one({"session_id": session_id})
    if not document:
        return None
    document.pop("_id", None)
    return _document_to_status(document)


def _now() -> datetime:
    """Return a timezone-naive UTC timestamp."""

    return datetime.utcnow()


def _record_event(
    state: SessionState,
    stage: PipelineStage,
    message: str,
    metadata: Optional[dict] = None,
) -> None:
    """Append a status event to the session and update its headline stage."""

    event = SessionEvent(
        timestamp=_now(),
        stage=stage,
        message=message,
        metadata=metadata or {},
    )
    state.events.append(event)
    state.stage = stage
    state.updated_at = event.timestamp
    if logger.isEnabledFor(logging.INFO):
        meta_suffix = ""
        if event.metadata:
            meta_suffix = f" | metadata={json.dumps(event.metadata, default=str)}"
        logger.info(
            "session=%s stage=%s %s%s",
            state.session_id,
            event.stage.value,
            event.message,
            meta_suffix,
        )
    _persist_state(state)


def _mark_failure(state: SessionState, error: str) -> None:
    """Update the session to reflect a terminal failure."""

    state.failed = True
    state.completed = True
    state.error = error
    _record_event(state, PipelineStage.FAILED, error)


def _mark_complete(state: SessionState, message: str) -> None:
    """Update the session to reflect a successful completion."""

    state.completed = True
    _record_event(state, PipelineStage.COMPLETE, message)


def _build_llm_client(model_name: str):
    """Instantiate the appropriate API client for the requested LLM."""

    if "claude" in model_name:
        import anthropic

        client = anthropic.Anthropic()
        client_model = model_name
    elif model_name in {"openai/gpt-oss-120b", "openai/gpt-oss-20b"} or "groq" in model_name.lower() or model_name.startswith("openai/"):
        import groq

        client = groq.Groq(api_key=os.environ.get("GROQ_API_KEY"))
        client_model = model_name
    elif "gpt" in model_name and not model_name.startswith("openai/"):
        import openai

        client = openai.OpenAI()
        client_model = model_name
    elif "deepseek" in model_name:
        import openai

        client = openai.OpenAI(
            api_key=os.environ["DEEPSEEK_API_KEY"],
            base_url="https://api.deepseek.com",
        )
        client_model = model_name
    elif model_name == "Intern-S1":
        import openai

        client = openai.OpenAI(
            api_key=os.environ["INS1_API_KEY"],
            base_url="https://chat.intern-ai.org.cn/api/v1/",
        )
        client_model = model_name
    elif model_name.startswith("localhost"):
        import openai

        client = openai.OpenAI(base_url="http://localhost:11434/v1", api_key="na")
        client_model = model_name
    elif model_name.startswith("gemini"):
        import google.generativeai as genai

        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("GOOGLE_API_KEY must be set to use Gemini models.")
        genai.configure(api_key=api_key)
        client = genai.GenerativeModel(model_name)
        client_model = model_name
    else:
        raise ValueError(f"Unsupported model '{model_name}'. Please extend session_service to handle it.")

    return client, client_model


def _build_coder_model(model_name: str) -> Model:
    """Create an aider Model wrapper honoring provider-specific prefixes."""

    if model_name.startswith("deepseek"):
        return Model("deepseek/deepseek-coder")
    if model_name.startswith("localhost"):
        ollama_model = "ollama/" + "-".join(model_name.split("-")[1:])
        return Model(ollama_model)
    return Model(model_name)


def _ensure_directories(base_dir: Path, results_dir: Path) -> None:
    """Make sure the working directories exist before the session runs."""

    base_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)


def _load_baseline_results(base_dir: Path) -> Dict[str, List[float]]:
    """Load the baseline metrics recorded in run_0/final_info.json."""

    info_path = base_dir / "run_0" / "final_info.json"
    if not info_path.exists():
        raise FileNotFoundError(f"Baseline metrics not found at {info_path}")
    with info_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return {key: value["means"] for key, value in data.items()}


def _write_idea_notes(folder: Path, idea: dict, baseline_results: Dict[str, List[float]]) -> None:
    """Persist a notes.txt file summarizing the run history for the idea."""

    notes_path = folder / "notes.txt"
    with notes_path.open("w", encoding="utf-8") as handle:
        handle.write(f"# Title: {idea.get('Title', 'Unnamed Idea')}\n")
        handle.write(f"# Experiment description: {idea.get('Experiment', '')}\n")
        handle.write("## Run 0: Baseline\n")
        handle.write(f"Results: {baseline_results}\n")
        handle.write("Description: Baseline results.\n")


def _run_single_idea(
    idea: dict,
    base_dir: Path,
    results_dir: Path,
    code_model: str,
) -> Optional[str]:
    """Execute AutoAD for a single idea and return the result directory path."""

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    idea_slug = idea.get("Name", "idea").replace(" ", "_")
    folder = results_dir / f"{timestamp}_{idea_slug}"
    if folder.exists():
        raise FileExistsError(f"Result directory {folder} already exists.")

    shutil.copytree(base_dir, folder, dirs_exist_ok=True)

    baseline_results = _load_baseline_results(base_dir)
    _write_idea_notes(folder, idea, baseline_results)

    exp_file = folder / "experiment.py"
    notes_file = folder / "notes.txt"

    io = InputOutput(yes=True, chat_history_file=str(folder / f"{folder.name}_aider.txt"))
    main_model = _build_coder_model(code_model)
    coder = Coder.create(
        main_model=main_model,
        fnames=[str(exp_file), str(notes_file)],
        io=io,
        stream=False,
        use_git=False,
        edit_format="diff",
    )

    success = perform_experiments(idea, str(folder), coder, baseline_results)
    if success:
        return str(folder)
    return None


def create_session(payload: SessionCreateRequest) -> str:
    """Register a new session and return its tracking identifier."""

    session_id = str(uuid4())
    state = SessionState(session_id=session_id, request=payload, project_slug=payload.project_slug)
    with _sessions_lock:
        _record_event(
            state,
            PipelineStage.QUEUED,
            f"Session queued for project '{payload.project_slug}'.",
            metadata={"model": payload.model, "code_model": payload.code_model},
        )
        _sessions[session_id] = state
        _persist_state(state)
    return session_id


# Backwards compatibility alias: prior builds exposed a misspelled helper that some
# long-running worker processes may still reference during hot reloads. Keeping the
# alias avoids transient AttributeError crashes while the new name propagates.
wcreate_session = create_session


def list_sessions() -> List[SessionListItem]:
    """Return a lightweight list of all known sessions."""

    if _sessions_collection is not None:
        documents = list(_sessions_collection.find().sort("started_at", -1))
        return [_document_to_list_item(doc) for doc in documents]

    with _sessions_lock:
        return [
            SessionListItem(
                session_id=s.session_id,
                project_slug=s.project_slug,
                stage=s.stage,
                started_at=s.started_at,
                updated_at=s.updated_at,
                completed=s.completed,
                failed=s.failed,
            )
            for s in _sessions.values()
        ]


def get_status(session_id: str) -> SessionStatus:
    """Return the full status snapshot for a specific session."""

    with _sessions_lock:
        state = _sessions.get(session_id)
        if state is not None:
            return _state_to_status(state)

    status = _load_status_from_store(session_id)
    if status is None:
        raise SessionNotFoundError(f"Session '{session_id}' not found.")
    return status


def execute_session(session_id: str) -> None:
    """Run the AutoAD pipeline end-to-end for the specified session."""

    with _sessions_lock:
        state = _sessions.get(session_id)
        if state is None:
            raise SessionNotFoundError(f"Session '{session_id}' not found.")

    try:
        project = project_service.get_project(state.project_slug)
    except ProjectNotFoundError as exc:
        with _sessions_lock:
            _mark_failure(state, str(exc))
        return

    payload = state.request
    base_dir = Path(project.base_dir)
    results_dir = Path(project.results_dir)

    with _sessions_lock:
        _record_event(state, PipelineStage.PREPARING, "Preparing project directories.")
    _ensure_directories(base_dir, results_dir)

    topic = payload.topic_override or project.topic
    use_rag = payload.use_rag if payload.use_rag is not None else project.enable_rag

    try:
        client, client_model = _build_llm_client(payload.model)
    except Exception as exc:  # pragma: no cover - defensive logging
        with _sessions_lock:
            _mark_failure(state, f"Failed to build LLM client: {exc}")
        return

    if use_rag:
        if not topic:
            with _sessions_lock:
                _mark_failure(state, "RAG enabled but no topic was provided.")
            return
        rag_path = base_dir / f"{project.slug}_rag_papers.json"
        with _sessions_lock:
            _record_event(state, PipelineStage.RETRIEVAL, f"Collecting literature for topic '{topic}'.")
        try:
            paper_bank, total_cost, all_queries = collect_papers(
                topic,
                client,
                client_model,
                getattr(project, "seed", 2025),
                project.rag_memory_papers,
                project.rag_max_papers,
            )
            payload_dict = {
                "topic_description": topic,
                "all_queries": all_queries,
                "paper_bank": paper_bank,
            }
            with rag_path.open("w", encoding="utf-8") as handle:
                json.dump(payload_dict, handle, indent=4)
        except Exception as exc:
            with _sessions_lock:
                _mark_failure(state, f"RAG collection failed: {exc}")
            return
    else:
        rag_path = base_dir / f"{project.slug}_rag_papers.json"

    exp_base_file_list = None
    if payload.round > 0:
        prev_round = payload.round - 1
        prev_ideas_file = base_dir / f"ideas_round_{prev_round}_with_pos.json"
        if not prev_ideas_file.exists():
            with _sessions_lock:
                _mark_failure(
                    state,
                    f"Previous ideas file '{prev_ideas_file}' not found for round {payload.round}.",
                )
            return
        exp_base_file_list = ([str(results_dir)], [str(prev_ideas_file)])

    with _sessions_lock:
        _record_event(state, PipelineStage.IDEA_GENERATION, "Generating candidate ideas.")
    try:
        ideas = generate_ideas(
            str(base_dir),
            client=client,
            model=client_model,
            skip_generation=payload.skip_idea_generation,
            max_num_generations=payload.num_ideas,
            num_reflections=NUM_REFLECTIONS,
            rag=use_rag,
            rag_path=str(rag_path),
            check_independence=payload.check_similarity,
            embedding_model=payload.embedding_model,
            round=payload.round,
            exp_base_file_list=exp_base_file_list,
        )
    except Exception as exc:
        with _sessions_lock:
            _mark_failure(state, f"Idea generation failed: {exc}")
        return

    with _sessions_lock:
        _record_event(state, PipelineStage.IDEA_GENERATION, f"Generated {len(ideas)} ideas.")

    if payload.skip_novelty_check:
        for idea in ideas:
            idea["novel"] = True
            idea["independence"] = True
    else:
        with _sessions_lock:
            _record_event(state, PipelineStage.NOVELTY_CHECK, "Running novelty checks.")
        try:
            ideas = check_idea_novelty(
                ideas,
                base_dir=str(base_dir),
                client=client,
                model=client_model,
                round=payload.round,
            )
        except Exception as exc:
            with _sessions_lock:
                _mark_failure(state, f"Novelty check failed: {exc}")
            return

    filtered_ideas = [idea for idea in ideas if idea.get("independence", True)]
    novel_ideas = [idea for idea in filtered_ideas if idea.get("novel", False)]

    with _sessions_lock:
        _record_event(
            state,
            PipelineStage.EXECUTION,
            f"Running experiments for {len(novel_ideas)} novel ideas (sequential).",
            metadata={"total_ideas": len(novel_ideas)},
        )

    for index, idea in enumerate(novel_ideas, start=1):
        idea_name = idea.get("Name", f"Idea {index}")
        with _sessions_lock:
            _record_event(
                state,
                PipelineStage.EXECUTION,
                f"[{index}/{len(novel_ideas)}] Executing idea '{idea_name}'.",
            )
        try:
            result_path = _run_single_idea(idea, base_dir, results_dir, payload.code_model)
        except Exception as exc:  # pragma: no cover - defensive logging
            with _sessions_lock:
                _record_event(
                    state,
                    PipelineStage.EXECUTION,
                    f"Idea '{idea_name}' failed with error: {exc}",
                    metadata={"idea": idea},
                )
            continue

        if result_path:
            with _sessions_lock:
                state.result_paths.append(result_path)
                _record_event(
                    state,
                    PipelineStage.EXECUTION,
                    f"Idea '{idea_name}' completed successfully.",
                    metadata={"result_path": result_path},
                )
        else:
            with _sessions_lock:
                _record_event(
                    state,
                    PipelineStage.EXECUTION,
                    f"Idea '{idea_name}' reported failure during experiments.",
                    metadata={"idea": idea},
                )

    with _sessions_lock:
        if state.result_paths:
            _mark_complete(state, "Session finished. Check result paths for artifacts.")
        else:
            _mark_failure(state, "Session finished without any successful ideas.")