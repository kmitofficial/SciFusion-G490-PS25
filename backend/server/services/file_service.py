"""
File service for handling file operations
"""

import os
import zipfile
import shutil
from typing import List
from app.config import get_settings

class FileService:
    """Service for file operations related to experiments"""
    
    def __init__(self):
        self.settings = get_settings()
    
    def get_experiment_logs(self, experiment_id: str, lines: int = 100) -> List[str]:
        """Get experiment log lines"""
        log_path = os.path.join(self.settings.RESULTS_DIR, experiment_id, "log.txt")
        
        if not os.path.exists(log_path):
            raise FileNotFoundError(f"Log file not found for experiment {experiment_id}")
        
        with open(log_path, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
            return all_lines[-lines:] if len(all_lines) > lines else all_lines
    
    def create_results_zip(self, experiment_id: str) -> str:
        """Create a zip file of experiment results"""
        result_dir = os.path.join(self.settings.RESULTS_DIR, experiment_id)
        
        if not os.path.exists(result_dir):
            raise FileNotFoundError(f"Results not found for experiment {experiment_id}")
        
        zip_path = os.path.join(self.settings.RESULTS_DIR, f"{experiment_id}_results.zip")
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(result_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, result_dir)
                    zipf.write(file_path, arcname)
        
        return zip_path