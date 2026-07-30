import json
from pathlib import Path

from app.domain import PipelineTask, TaskState


class FixtureAdapter:
    def __init__(self, fixture_path: str | Path):
        self.fixture_path = Path(fixture_path)
        self.retry_calls = 0
        self._recovered = False

    def poll(self) -> list[PipelineTask]:
        if self._recovered:
            return [PipelineTask(source="fixture", run_id="run-1", task_id="extract", state=TaskState.SUCCESS)]
        data = json.loads(self.fixture_path.read_text())
        return [PipelineTask.model_validate(data)]

    def retry_failed_task(self, task: PipelineTask) -> bool:
        self.retry_calls += 1
        self._recovered = True
        return True

