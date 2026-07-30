from typing import Any

from app.domain import PipelineTask, TaskState


def normalize_airflow_response(payload: dict[str, Any]) -> list[PipelineTask]:
    tasks = payload.get("tasks", [])
    return [PipelineTask(source="airflow", run_id=str(payload["run_id"]), task_id=str(item["task_id"]),
                         state=TaskState(item.get("state", "unknown")),
                         evidence={"dag_id": str(payload.get("dag_id", "")), "log": str(item.get("log", ""))[:4000]})
            for item in tasks]


class AirflowAdapter:
    def __init__(self, response: dict[str, Any]):
        self.response = response
        self.mutation_calls = 0

    def poll(self) -> list[PipelineTask]:
        return normalize_airflow_response(self.response)

    def retry_failed_task(self, task: PipelineTask) -> bool:
        self.mutation_calls += 1
        raise RuntimeError("live Airflow mutation is not enabled in monitoring")

