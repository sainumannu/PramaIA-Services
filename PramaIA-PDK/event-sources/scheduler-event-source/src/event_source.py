"""
Minimal, single-copy scheduler event_source.py
"""

import asyncio
import logging
import json
import os
import sys
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional

try:
    from croniter import croniter
except Exception:
    croniter = None

# Adapter logger: prefer relative wrapper 'logger', then pramaialog client, otherwise std logging
try:
    from .logger import debug as _debug, info as _info, warning as _warning, error as _error  # type: ignore
    def _log_info(msg, **kwargs):
        _info(msg, **kwargs)
    def _log_debug(msg, **kwargs):
        _debug(msg, **kwargs)
    def _log_warning(msg, **kwargs):
        _warning(msg, **kwargs)
    def _log_error(msg, **kwargs):
        _error(msg, **kwargs)
except Exception:
    try:
        from pramaialog import PramaIALogger, LogProject  # type: ignore
        _pramaialogger = PramaIALogger(api_key=os.environ.get("PRAMAIALOG_API_KEY", "pdk_plugin_api_key"), project=LogProject.PDK, module="scheduler_event_source", host=os.environ.get("PRAMAIALOG_HOST", "http://localhost:8081"))
        def _log_info(msg, **kwargs):
            try:
                _pramaialogger.info(msg, **kwargs)
            except Exception:
                logging.getLogger(__name__).info(msg)
        def _log_debug(msg, **kwargs):
            try:
                _pramaialogger.debug(msg, **kwargs)
            except Exception:
                logging.getLogger(__name__).debug(msg)
        def _log_warning(msg, **kwargs):
            try:
                _pramaialogger.warning(msg, **kwargs)
            except Exception:
                logging.getLogger(__name__).warning(msg)
        def _log_error(msg, **kwargs):
            try:
                _pramaialogger.error(msg, **kwargs)
            except Exception:
                logging.getLogger(__name__).error(msg)
    except Exception:
        def _log_info(msg, **kwargs): logging.getLogger(__name__).info(msg)
        def _log_debug(msg, **kwargs): logging.getLogger(__name__).debug(msg)
        def _log_warning(msg, **kwargs): logging.getLogger(__name__).warning(msg)
        def _log_error(msg, **kwargs): logging.getLogger(__name__).error(msg)


class ScheduleManager:
    def __init__(self, config: Dict[str, Any], parent):
        self.config = config
        self.parent = parent
        self.name = config.get('name', 'unnamed')
        self.type = config.get('type', 'interval')
        self.enabled = config.get('enabled', True)
        self.execution_count = 0
        self.last_execution: Optional[datetime] = None
        self.next_execution: Optional[datetime] = None
        self._task: Optional[asyncio.Task] = None

        if self.type == 'cron' and croniter:
            self.cron_expression = config['cron']
            self._init_cron()
        elif self.type == 'interval':
            self.interval_seconds = int(config.get('interval_seconds', 60))
            self._init_interval()
        elif self.type == 'one_time':
            execute_at = config.get('execute_at')
            if execute_at:
                self.execute_at = datetime.fromisoformat(execute_at.replace('Z', '+00:00'))
            else:
                self.execute_at = datetime.now(timezone.utc)
            self._init_one_time()

    def _init_cron(self):
        now = datetime.now(timezone.utc)
        cron = croniter(self.cron_expression, now)
        self.next_execution = cron.get_next(datetime)
        _log_info(f"[{self.name}] cron next: {self.next_execution}")

    def _init_interval(self):
        self.next_execution = datetime.now(timezone.utc)
        _log_info(f"[{self.name}] interval: {self.interval_seconds}s")

    def _init_one_time(self):
        self.next_execution = self.execute_at
        _log_info(f"[{self.name}] one-time at {self.execute_at}")

    async def start(self):
        if not self.enabled:
            _log_info(f"[{self.name}] disabled")
            return
        if self._task and not self._task.done():
            _log_info(f"[{self.name}] already running")
            return
        self._task = asyncio.create_task(self._run())
        _log_info(f"[{self.name}] started")

    async def stop(self):
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        _log_info(f"[{self.name}] stopped")

    async def _run(self):
        try:
            while True:
                now = datetime.now(timezone.utc)
                if self.next_execution and now >= self.next_execution:
                    await self._execute()
                    await self._calculate_next()
                    if self.type == 'one_time' and self.execution_count > 0:
                        break
                await asyncio.sleep(0.5)
        except asyncio.CancelledError:
            _log_info(f"[{self.name}] cancelled")

    async def _execute(self):
        try:
            t = datetime.now(timezone.utc)
            self.last_execution = t
            payload = {'name': self.name, 'time': t.isoformat(), 'type': self.type}
            if self.type == 'cron':
                payload['cron'] = self.cron_expression
            elif self.type == 'interval':
                payload['interval'] = self.interval_seconds
            elif self.type == 'one_time':
                payload['scheduled_at'] = self.execute_at.isoformat()
            await self.parent._emit_event('schedule_trigger', payload)
            self.execution_count += 1
            _log_info(f"[{self.name}] executed")
        except Exception as e:
            _log_error(f"[{self.name}] exec error: {e}")
            await self.parent._emit_error_event(self.name, str(e), self.type)

    async def _calculate_next(self):
        if self.type == 'cron' and croniter:
            now = datetime.now(timezone.utc)
            cron = croniter(self.cron_expression, now)
            self.next_execution = cron.get_next(datetime)
        elif self.type == 'interval':
            now = datetime.now(timezone.utc)
            self.next_execution = now + timedelta(seconds=self.interval_seconds)
        else:
            self.next_execution = None


class EventSource:
    def __init__(self):
        self.config: Dict[str, Any] = {}
        self.schedules: Dict[str, ScheduleManager] = {}
        self.running = False
        self.events_emitted = 0
        self.last_activity: Optional[datetime] = None
        self.log_level = 'INFO'

    async def initialize(self, config: Dict[str, Any]):
        self.config = config
        for s in config.get('schedules', []):
            mgr = ScheduleManager(s, self)
            self.schedules[mgr.name] = mgr
        _log_info(f"EventSource initialized ({len(self.schedules)} schedules)")

    async def start(self) -> bool:
        if self.running:
            return True
        self.running = True
        for mgr in self.schedules.values():
            await mgr.start()
        _log_info("EventSource started")
        return True

    async def stop(self) -> bool:
        if not self.running:
            return True
        for mgr in self.schedules.values():
            await mgr.stop()
        self.running = False
        _log_info("EventSource stopped")
        return True

    async def _emit_event(self, event_type: str, data: Dict[str, Any]):
        # emit as JSON for PDK runtime
        event = {'eventType': event_type, 'data': data, 'timestamp': datetime.now(timezone.utc).isoformat(), 'sourceId': 'scheduler-event-source'}
        print(json.dumps(event))
        sys.stdout.flush()
        self.events_emitted += 1
        self.last_activity = datetime.now(timezone.utc)

    async def _emit_error_event(self, name: str, message: str, schedule_type: str):
        await self._emit_event('schedule_error', {'name': name, 'message': message, 'type': schedule_type})


async def main():
    cfg = {'schedules': [{'name': 'test', 'type': 'interval', 'interval_seconds': 5}]}
    es = EventSource()
    await es.initialize(cfg)
    await es.start()
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await es.stop()


if __name__ == '__main__':
    asyncio.run(main())
