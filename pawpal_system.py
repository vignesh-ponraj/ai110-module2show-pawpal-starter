from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time
from typing import Literal


Priority = Literal["low", "medium", "high"]
TaskStatus = Literal["pending", "completed", "skipped"]


@dataclass
class Owner:
    owner_id: str
    name: str
    daily_available_minutes: int
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        pass

    def remove_pet(self, pet_id: str) -> None:
        pass

    def list_pets(self) -> list[Pet]:
        pass


@dataclass
class Pet:
	pet_id: str
	owner_id: str
	name: str
	species: str
	notes: str
	tasks: list[CareTask] = field(default_factory=list)

	def update_profile(self, name: str, species: str, notes: str) -> None:
		pass

	def add_task(self, task: CareTask) -> None:
		pass

	def remove_task(self, task_id: str) -> None:
		pass

	def list_tasks(self) -> list[CareTask]:
		pass


@dataclass
class CareTask:
	task_id: str
	owner_id: str
	pet_id: str
	title: str
	duration_minutes: int
	priority: Priority
	preferred_window_start: time | None
	preferred_window_end: time | None
	required_today: bool
	status: TaskStatus = "pending"
	completed_at: datetime | None = None
	skipped_reason: str | None = None

	def mark_complete(self) -> None:
		pass

	def mark_skipped(self, reason: str) -> None:
		pass


@dataclass
class ScheduledTask:
	scheduled_task_id: str
	plan_id: str
	task_id: str
	pet_id: str
	start_time: time
	end_time: time
	status: TaskStatus = "pending"
	completed_at: datetime | None = None
	skipped_reason: str | None = None

	def set_completed(self) -> None:
		pass

	def set_skipped(self, reason: str) -> None:
		pass


@dataclass
class DailyPlan:
	plan_id: str
	owner_id: str
	plan_date: date
	unscheduled_task_ids: list[str] = field(default_factory=list)
	scheduled_tasks: list[ScheduledTask] = field(default_factory=list)

	def add_scheduled_task(self, item: ScheduledTask) -> None:
		pass

	def mark_task_complete(self, scheduled_task_id: str) -> None:
		pass

	def calculate_total_minutes(self) -> int:
		pass

	def get_summary(self) -> str:
		pass


@dataclass
class Scheduler:
	def generate_plan(
		self,
		owner: Owner,
		pets: list[Pet],
		tasks: list[CareTask],
		plan_date: date,
		day_start: time,
	) -> DailyPlan:
		pass

	def validate_ownership(self, owner: Owner, pets: list[Pet], tasks: list[CareTask]) -> None:
		pass

	def select_tasks(self, tasks: list[CareTask], available_minutes: int) -> list[CareTask]:
		pass

	def order_tasks(self, tasks: list[CareTask]) -> list[CareTask]:
		pass

	def assign_times(
		self, tasks: list[CareTask], day_start: time, plan_id: str
	) -> list[ScheduledTask]:
		pass
