"""
Experiment Manager - Core business logic for managing InternAgent experiments
"""

import asyncio
import os
import json
import uuid
import shutil
from datetime import datetime
from typing import List, Optional, Dict, Any
import subprocess
import threading
import time
import signal

from schemas.experiment import (
    ExperimentCreate, ExperimentResponse, ExperimentUpdate, 
    ExperimentStatus, ExperimentResults, ExperimentStatusResponse
)
from app.config import get_settings
import sys

# Add parent directory to path to import InternAgent modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

class ExperimentManager:
    """Manages InternAgent experiments lifecycle"""
    
    def __init__(self):
        self.settings = get_settings()
        self.experiments_db = {}  # In-memory storage (replace with real DB)
        self.running_processes = {}  # Track running experiment processes
        
        # Ensure results directory exists
        os.makedirs(self.settings.RESULTS_DIR, exist_ok=True)
    
    def create_experiment(self, experiment_data: ExperimentCreate) -> ExperimentResponse:
        """Create a new experiment"""
        experiment_id = str(uuid.uuid4())
        
        experiment = ExperimentResponse(
            id=experiment_id,
            name=experiment_data.name,
            description=experiment_data.description,
            experiment_type=experiment_data.experiment_type,
            status=ExperimentStatus.CREATED,
            
            # Configuration
            model=experiment_data.model,
            code_model=experiment_data.code_model,
            num_ideas=experiment_data.num_ideas,
            max_papers=experiment_data.max_papers,
            parallel=experiment_data.parallel,
            use_rag=experiment_data.use_rag,
            topic=experiment_data.topic,
            
            # Timestamps
            created_at=datetime.utcnow(),
            updated_at=None,
            started_at=None,
            completed_at=None,
            
            # Initial progress
            progress=0.0,
            current_step="Created",
            ideas_generated=0,
            ideas_tested=0,
            successful_ideas=0
        )
        
        self.experiments_db[experiment_id] = experiment
        return experiment
    
    def list_experiments(self, skip: int = 0, limit: int = 10, status: Optional[str] = None) -> List[ExperimentResponse]:
        """List experiments with optional filtering"""
        experiments = list(self.experiments_db.values())
        
        # Filter by status if provided
        if status:
            experiments = [exp for exp in experiments if exp.status == status]
        
        # Sort by creation date (newest first)
        experiments.sort(key=lambda x: x.created_at, reverse=True)
        
        # Apply pagination
        return experiments[skip:skip + limit]
    
    def get_experiment(self, experiment_id: str) -> Optional[ExperimentResponse]:
        """Get experiment by ID"""
        return self.experiments_db.get(experiment_id)
    
    def update_experiment(self, experiment_id: str, updates: ExperimentUpdate) -> Optional[ExperimentResponse]:
        """Update experiment configuration"""
        experiment = self.experiments_db.get(experiment_id)
        if not experiment:
            return None
        
        # Update fields
        update_data = updates.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(experiment, field, value)
        
        experiment.updated_at = datetime.utcnow()
        return experiment
    
    def delete_experiment(self, experiment_id: str) -> bool:
        """Delete an experiment"""
        if experiment_id not in self.experiments_db:
            return False
        
        # Stop if running
        if experiment_id in self.running_processes:
            self.stop_experiment(experiment_id)
        
        # Remove from storage
        del self.experiments_db[experiment_id]
        
        # Clean up result files
        result_dir = os.path.join(self.settings.RESULTS_DIR, experiment_id)
        if os.path.exists(result_dir):
            shutil.rmtree(result_dir)
        
        return True
    
    def run_experiment(self, experiment_id: str):
        """Run an experiment (called as background task)"""
        experiment = self.experiments_db.get(experiment_id)
        if not experiment:
            return
        
        try:
            # Update status and timing
            experiment.status = ExperimentStatus.RUNNING
            experiment.started_at = datetime.utcnow()
            experiment.current_step = "Initializing"
            
            # Build command to execute launch_dolphin.py
            cmd = self._build_experiment_command(experiment)
            
            # Create results directory for this experiment
            result_dir = os.path.join(self.settings.RESULTS_DIR, experiment_id)
            os.makedirs(result_dir, exist_ok=True)
            
            # Start the process
            process = subprocess.Popen(
                cmd,
                cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),  # InternAgent root
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            self.running_processes[experiment_id] = process
            
            # Monitor progress in separate thread
            monitor_thread = threading.Thread(
                target=self._monitor_experiment_progress,
                args=(experiment_id, process)
            )
            monitor_thread.start()
            
        except Exception as e:
            experiment.status = ExperimentStatus.FAILED
            experiment.current_step = f"Failed: {str(e)}"
            experiment.completed_at = datetime.utcnow()
    
    def stop_experiment(self, experiment_id: str) -> bool:
        """Stop a running experiment"""
        if experiment_id not in self.running_processes:
            return False
        
        process = self.running_processes[experiment_id]
        experiment = self.experiments_db[experiment_id]
        
        try:
            # Terminate the process
            process.terminate()
            
            # Wait for graceful shutdown
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
            
            # Update status
            experiment.status = ExperimentStatus.STOPPED
            experiment.current_step = "Stopped by user"
            experiment.completed_at = datetime.utcnow()
            
            # Remove from running processes
            del self.running_processes[experiment_id]
            
            return True
        except Exception:
            return False
    
    def get_experiment_status(self, experiment_id: str) -> Optional[ExperimentStatusResponse]:
        """Get real-time experiment status"""
        experiment = self.experiments_db.get(experiment_id)
        if not experiment:
            return None
        
        # Calculate elapsed time
        elapsed_time = None
        if experiment.started_at:
            if experiment.completed_at:
                elapsed_time = (experiment.completed_at - experiment.started_at).total_seconds()
            else:
                elapsed_time = (datetime.utcnow() - experiment.started_at).total_seconds()
        
        return ExperimentStatusResponse(
            id=experiment_id,
            status=experiment.status,
            progress=experiment.progress,
            current_step=experiment.current_step,
            message=None,  # Could add more detailed messages
            
            ideas_generated=experiment.ideas_generated,
            ideas_tested=experiment.ideas_tested,
            successful_ideas=experiment.successful_ideas,
            failed_ideas=experiment.ideas_tested - experiment.successful_ideas,
            
            elapsed_time=elapsed_time,
            estimated_remaining=self._estimate_remaining_time(experiment),
            
            memory_usage=None,  # Could add system monitoring
            gpu_usage=None
        )
    
    def get_experiment_results(self, experiment_id: str) -> Optional[ExperimentResults]:
        """Get experiment results"""
        experiment = self.experiments_db.get(experiment_id)
        if not experiment:
            return None
        
        # Load results from filesystem if available
        result_dir = os.path.join(self.settings.RESULTS_DIR, experiment_id)
        
        # This would parse actual result files
        # For now, return basic structure
        return ExperimentResults(
            experiment_id=experiment_id,
            status=experiment.status,
            total_ideas=experiment.num_ideas,
            successful_ideas=experiment.successful_ideas,
            failed_ideas=experiment.ideas_tested - experiment.successful_ideas,
            
            total_execution_time=None,
            start_time=experiment.started_at,
            end_time=experiment.completed_at,
            
            ideas=[],  # Would parse from actual results
            result_files=[],
            log_files=[]
        )
    
    def update_experiment_status(self, experiment_id: str, status: str):
        """Update experiment status"""
        experiment = self.experiments_db.get(experiment_id)
        if experiment:
            experiment.status = status
            experiment.updated_at = datetime.utcnow()
    
    def _build_experiment_command(self, experiment: ExperimentResponse) -> List[str]:
        """Build command to run the experiment"""
        cmd = [
            "python", "launch_dolphin.py",
            "--model", experiment.model,
            "--code_model", experiment.code_model,
            "--experiment", experiment.experiment_type.value,
            "--num-ideas", str(experiment.num_ideas),
            "--seed", "2025"
        ]
        
        if experiment.parallel > 0:
            cmd.extend(["--parallel", str(experiment.parallel)])
        
        if experiment.use_rag and experiment.topic:
            cmd.extend(["--rag", "--topic", experiment.topic])
            cmd.extend(["--max_papers", str(experiment.max_papers)])
        
        return cmd
    
    def _monitor_experiment_progress(self, experiment_id: str, process: subprocess.Popen):
        """Monitor experiment progress by parsing output"""
        experiment = self.experiments_db[experiment_id]
        
        try:
            while process.poll() is None:
                # Read output line by line
                if process.stdout:
                    line = process.stdout.readline()
                    if line:
                        self._parse_progress_line(experiment, line.strip())
                
                time.sleep(1)
            
            # Process finished
            return_code = process.returncode
            
            if return_code == 0:
                experiment.status = ExperimentStatus.COMPLETED
                experiment.current_step = "Completed successfully"
                experiment.progress = 1.0
            else:
                experiment.status = ExperimentStatus.FAILED
                experiment.current_step = f"Failed with code {return_code}"
            
            experiment.completed_at = datetime.utcnow()
            
            # Remove from running processes
            if experiment_id in self.running_processes:
                del self.running_processes[experiment_id]
                
        except Exception as e:
            experiment.status = ExperimentStatus.FAILED
            experiment.current_step = f"Monitoring error: {str(e)}"
            experiment.completed_at = datetime.utcnow()
    
    def _parse_progress_line(self, experiment: ExperimentResponse, line: str):
        """Parse output line to update progress"""
        # This would implement parsing of actual InternAgent output
        # For now, just update current step based on keywords
        
        if "Generating ideas" in line:
            experiment.current_step = "Generating ideas"
            experiment.progress = 0.2
        elif "Checking novelty" in line:
            experiment.current_step = "Checking idea novelty"
            experiment.progress = 0.4
        elif "Running experiments" in line:
            experiment.current_step = "Running experiments"
            experiment.progress = 0.6
        elif "Completed idea" in line:
            experiment.ideas_tested += 1
            if "Success: True" in line:
                experiment.successful_ideas += 1
            experiment.progress = min(0.6 + (experiment.ideas_tested / experiment.num_ideas) * 0.4, 1.0)
        elif "All ideas evaluated" in line:
            experiment.current_step = "All ideas evaluated"
            experiment.progress = 1.0
    
    def _estimate_remaining_time(self, experiment: ExperimentResponse) -> Optional[float]:
        """Estimate remaining time based on progress"""
        if not experiment.started_at or experiment.progress <= 0:
            return None
        
        elapsed = (datetime.utcnow() - experiment.started_at).total_seconds()
        if experiment.progress > 0:
            total_estimated = elapsed / experiment.progress
            remaining = total_estimated - elapsed
            return max(0, remaining)
        
        return None