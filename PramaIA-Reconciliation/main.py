#!/usr/bin/env python3
"""
PramaIA-Reconciliation - Servizio di riconciliazione vectorstore
"""

import os
import sys
import asyncio
import logging
import schedule
import time
from datetime import datetime, timedelta
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import uvicorn
import threading
from pathlib import Path
import json

# Get current directory and setup logging paths
BASE_DIR = Path(__file__).parent.absolute()
LOGS_DIR = BASE_DIR / "logs"
LOG_FILE = LOGS_DIR / "reconciliation.log"

# Ensure logs directory exists
LOGS_DIR.mkdir(exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_FILE)
    ]
)

logger = logging.getLogger("PramaIA-Reconciliation")

class ReconciliationRequest(BaseModel):
    delete_missing: bool = False

class ReconciliationSettings(BaseModel):
    schedule_enabled: bool = True
    schedule_time: str = "03:00"
    max_worker_threads: int = 4
    batch_size: int = 100

class ReconciliationService:
    def __init__(self):
        self.current_job = None
        self.job_history = []
        self.settings = ReconciliationSettings()
        self.scheduler_thread = None
        self.is_running = False
        
        # Load settings if they exist
        self.load_settings()
        
        # Start scheduler
        self.start_scheduler()
    
    def load_settings(self):
        """Load settings from file"""
        settings_file = Path("data/settings.json")
        if settings_file.exists():
            try:
                with open(settings_file, 'r') as f:
                    data = json.load(f)
                    self.settings = ReconciliationSettings(**data)
                logger.info("Settings loaded from file")
            except Exception as e:
                logger.error(f"Error loading settings: {e}")
    
    def save_settings(self):
        """Save settings to file"""
        os.makedirs("data", exist_ok=True)
        settings_file = Path("data/settings.json")
        try:
            with open(settings_file, 'w') as f:
                json.dump(self.settings.dict(), f, indent=2)
            logger.info("Settings saved to file")
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
    
    def start_scheduler(self):
        """Start the reconciliation scheduler"""
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            return
            
        def scheduler_loop():
            while self.is_running:
                try:
                    schedule.run_pending()
                    time.sleep(60)  # Check every minute
                except Exception as e:
                    logger.error(f"Scheduler error: {e}")
        
        self.is_running = True
        self.update_schedule()
        
        self.scheduler_thread = threading.Thread(target=scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        logger.info("Reconciliation scheduler started")
    
    def update_schedule(self):
        """Update the scheduled reconciliation"""
        schedule.clear()
        
        if self.settings.schedule_enabled:
            schedule.every().day.at(self.settings.schedule_time).do(self.run_scheduled_reconciliation)
            logger.info(f"Scheduled reconciliation at {self.settings.schedule_time}")
    
    def run_scheduled_reconciliation(self):
        """Run scheduled reconciliation"""
        logger.info("Running scheduled reconciliation")
        asyncio.create_task(self.start_reconciliation(False))
    
    async def start_reconciliation(self, delete_missing: bool = False) -> Dict[str, Any]:
        """Start a reconciliation job"""
        if self.current_job and self.current_job['status'] == 'running':
            raise HTTPException(status_code=400, detail="Reconciliation already running")
        
        job_id = f"reconciliation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.current_job = {
            'job_id': job_id,
            'status': 'running',
            'start_time': datetime.now().isoformat(),
            'delete_missing': delete_missing,
            'progress': 0,
            'messages': []
        }
        
        logger.info(f"Starting reconciliation job: {job_id}")
        
        # Run reconciliation in background
        asyncio.create_task(self._run_reconciliation_process(job_id, delete_missing))
        
        return {
            'success': True,
            'job_id': job_id,
            'message': 'Reconciliation started successfully'
        }
    
    async def _run_reconciliation_process(self, job_id: str, delete_missing: bool):
        """Run the actual reconciliation process"""
        try:
            if self.current_job is None:
                logger.warning(f"No current job found for {job_id}")
                return
                
            # Simulate reconciliation process
            await asyncio.sleep(1)
            self.current_job['progress'] = 25
            self.current_job['messages'].append("Scanning filesystem...")
            
            await asyncio.sleep(1)
            self.current_job['progress'] = 50
            self.current_job['messages'].append("Comparing with vectorstore...")
            
            await asyncio.sleep(1)
            self.current_job['progress'] = 75
            self.current_job['messages'].append("Updating missing entries...")
            
            if delete_missing:
                await asyncio.sleep(1)
                self.current_job['messages'].append("Removing obsolete entries...")
            
            await asyncio.sleep(1)
            self.current_job['progress'] = 100
            self.current_job['status'] = 'completed'
            self.current_job['end_time'] = datetime.now().isoformat()
            self.current_job['messages'].append("Reconciliation completed successfully")
            
            # Add to history
            self.job_history.insert(0, self.current_job.copy())
            if len(self.job_history) > 10:  # Keep only last 10 jobs
                self.job_history = self.job_history[:10]
            
            logger.info(f"Reconciliation job {job_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Reconciliation job {job_id} failed: {e}")
            if self.current_job is not None:
                self.current_job['status'] = 'failed'
                self.current_job['error'] = str(e)
                self.current_job['end_time'] = datetime.now().isoformat()
                self.current_job['messages'].append(f"Reconciliation failed: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get reconciliation status"""
        next_scheduled = None
        if self.settings.schedule_enabled:
            # Calculate next scheduled run
            now = datetime.now()
            schedule_time = datetime.strptime(self.settings.schedule_time, "%H:%M").time()
            next_run = datetime.combine(now.date(), schedule_time)
            if next_run <= now:
                next_run += timedelta(days=1)
            next_scheduled = next_run.isoformat()
        
        return {
            'scheduler_enabled': self.settings.schedule_enabled,
            'schedule_time': self.settings.schedule_time,
            'next_scheduled': next_scheduled,
            'current_job': self.current_job,
            'recent_jobs': self.job_history[:5],
            'settings': self.settings.dict()
        }
    
    def update_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Update reconciliation settings"""
        try:
            self.settings = ReconciliationSettings(**settings)
            self.save_settings()
            self.update_schedule()
            logger.info("Settings updated successfully")
            return {'success': True, 'settings': self.settings.dict()}
        except Exception as e:
            logger.error(f"Error updating settings: {e}")
            raise HTTPException(status_code=400, detail=f"Invalid settings: {e}")
    
    def stop(self):
        """Stop the reconciliation service"""
        self.is_running = False
        schedule.clear()
        logger.info("Reconciliation service stopped")

# Global service instance
reconciliation_service = ReconciliationService()

# FastAPI app
app = FastAPI(
    title="PramaIA-Reconciliation",
    description="Servizio di riconciliazione vectorstore per PramaIA",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "PramaIA-Reconciliation",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/reconciliation/status")
@app.get("/status")  # Alias
async def get_reconciliation_status():
    """Get reconciliation status"""
    return reconciliation_service.get_status()

@app.post("/reconciliation/start")
@app.post("/start")  # Alias
async def start_reconciliation(request: ReconciliationRequest = ReconciliationRequest()):
    """Start reconciliation process"""
    return await reconciliation_service.start_reconciliation(request.delete_missing)

@app.get("/settings")
async def get_settings():
    """Get reconciliation settings"""
    return reconciliation_service.settings.dict()

@app.post("/settings")
async def update_settings(settings: Dict[str, Any]):
    """Update reconciliation settings"""
    return reconciliation_service.update_settings(settings)

@app.on_event("startup")
async def startup_event():
    """Startup event"""
    logger.info("PramaIA-Reconciliation service started")

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event"""
    reconciliation_service.stop()
    logger.info("PramaIA-Reconciliation service stopped")

if __name__ == "__main__":
    port = int(os.getenv("RECONCILIATION_PORT", "8091"))
    host = os.getenv("HOST", "0.0.0.0")
    
    logger.info(f"Starting PramaIA-Reconciliation on http://{host}:{port}")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=False,
        log_level="info"
    )