from typing import Protocol

from app.domain import PipelineTask


class SourceAdapter(Protocol):
    def poll(self) -> list[PipelineTask]: ...

    def retry_failed_task(self, task: PipelineTask) -> bool: ...

