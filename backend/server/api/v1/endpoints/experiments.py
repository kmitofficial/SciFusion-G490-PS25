"""
Experiment management endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Optional
from pydantic import BaseModel
import os
import json
from datetime import datetime
import uuid

from schemas.experiment import (
    ExperimentCreate, ExperimentResponse, ExperimentUpdate, 
    ExperimentStatus, ExperimentResults
)
from core.experiment_manager import ExperimentManager
from services.file_service import FileService

router = APIRouter()

# Dependency injection
def get_experiment_manager() -> ExperimentManager:
    return ExperimentManager()

def get_file_service() -> FileService:
    return FileService()


@router.get("/", response_model=List[ExperimentResponse])
async def list_experiments(
    skip: int = 0,
    limit: int = 10,
    status: Optional[str] = None,
    exp_manager: ExperimentManager = Depends(get_experiment_manager)
):
    """List all experiments with optional filtering"""
    experiments = exp_manager.list_experiments(skip=skip, limit=limit, status=status)
    return experiments


@router.post("/", response_model=ExperimentResponse)
async def create_experiment(
    experiment: ExperimentCreate,
    exp_manager: ExperimentManager = Depends(get_experiment_manager)
):
    """Create a new experiment"""
    try:
        new_experiment = exp_manager.create_experiment(experiment)
        return new_experiment
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{experiment_id}", response_model=ExperimentResponse)
async def get_experiment(
    experiment_id: str,
    exp_manager: ExperimentManager = Depends(get_experiment_manager)
):
    """Get experiment details by ID"""
    experiment = exp_manager.get_experiment(experiment_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return experiment


@router.put("/{experiment_id}", response_model=ExperimentResponse)
async def update_experiment(
    experiment_id: str,
    updates: ExperimentUpdate,
    exp_manager: ExperimentManager = Depends(get_experiment_manager)
):
    """Update experiment configuration"""
    try:
        updated_experiment = exp_manager.update_experiment(experiment_id, updates)
        if not updated_experiment:
            raise HTTPException(status_code=404, detail="Experiment not found")
        return updated_experiment
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{experiment_id}")
async def delete_experiment(
    experiment_id: str,
    exp_manager: ExperimentManager = Depends(get_experiment_manager)
):
    """Delete an experiment"""
    success = exp_manager.delete_experiment(experiment_id)
    if not success:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return {"message": "Experiment deleted successfully"}


@router.post("/{experiment_id}/start")
async def start_experiment(
    experiment_id: str,
    background_tasks: BackgroundTasks,
    exp_manager: ExperimentManager = Depends(get_experiment_manager)
):
    """Start running an experiment"""
    experiment = exp_manager.get_experiment(experiment_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    if experiment.status == "running":
        raise HTTPException(status_code=400, detail="Experiment is already running")
    
    # Start experiment in background
    background_tasks.add_task(exp_manager.run_experiment, experiment_id)
    
    # Update status to running
    exp_manager.update_experiment_status(experiment_id, "running")
    
    return {"message": "Experiment started", "experiment_id": experiment_id}


@router.post("/{experiment_id}/stop")
async def stop_experiment(
    experiment_id: str,
    exp_manager: ExperimentManager = Depends(get_experiment_manager)
):
    """Stop a running experiment"""
    experiment = exp_manager.get_experiment(experiment_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    if experiment.status != "running":
        raise HTTPException(status_code=400, detail="Experiment is not running")
    
    success = exp_manager.stop_experiment(experiment_id)
    if success:
        return {"message": "Experiment stopped", "experiment_id": experiment_id}
    else:
        raise HTTPException(status_code=500, detail="Failed to stop experiment")


@router.get("/{experiment_id}/status", response_model=ExperimentStatus)
async def get_experiment_status(
    experiment_id: str,
    exp_manager: ExperimentManager = Depends(get_experiment_manager)
):
    """Get real-time experiment status"""
    status = exp_manager.get_experiment_status(experiment_id)
    if not status:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return status


@router.get("/{experiment_id}/results", response_model=ExperimentResults)
async def get_experiment_results(
    experiment_id: str,
    exp_manager: ExperimentManager = Depends(get_experiment_manager)
):
    """Get experiment results"""
    results = exp_manager.get_experiment_results(experiment_id)
    if not results:
        raise HTTPException(status_code=404, detail="Results not found")
    return results


@router.get("/{experiment_id}/logs")
async def get_experiment_logs(
    experiment_id: str,
    lines: int = 100,
    exp_manager: ExperimentManager = Depends(get_experiment_manager),
    file_service: FileService = Depends(get_file_service)
):
    """Get experiment logs"""
    try:
        logs = file_service.get_experiment_logs(experiment_id, lines)
        return {"logs": logs}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{experiment_id}/download")
async def download_results(
    experiment_id: str,
    file_service: FileService = Depends(get_file_service)
):
    """Download experiment results as zip file"""
    try:
        zip_path = file_service.create_results_zip(experiment_id)
        return {"download_url": f"/api/v1/files/download/{os.path.basename(zip_path)}"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))