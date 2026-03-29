from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


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

	def update_profile(self, name: str, species: str, notes: str) -> None:
		pass


@dataclass
class CareTask:
	task_id: str
	pet_id: str
	title: str
	duration_minutes: int
	priority: str
	preferred_window_start: str
	preferred_window_end: str
	required_today: bool

	def mark_complete(self) -> None:
		pass

	def mark_skipped(self, reason: str) -> None:
		pass


@dataclass
class ScheduledTask:
	scheduled_task_id: str
	task_id: str
	start_time: str
	end_time: str
	status: str

	def set_completed(self) -> None:
		pass

	def set_skipped(self, reason: str) -> None:
		pass


@dataclass
class DailyPlan:
	plan_id: str
	owner_id: str
	plan_date: date
	total_minutes: int
	unscheduled_task_ids: list[str] = field(default_factory=list)
	scheduled_tasks: list[ScheduledTask] = field(default_factory=list)

	def add_scheduled_task(self, item: ScheduledTask) -> None:
		pass

	def mark_task_complete(self, task_id: str) -> None:
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
	) -> DailyPlan:
		pass

	def select_tasks(self, tasks: list[CareTask], available_minutes: int) -> list[CareTask]:
		pass

	def order_tasks(self, tasks: list[CareTask]) -> list[CareTask]:
		pass

	def assign_times(self, tasks: list[CareTask], day_start: str) -> list[ScheduledTask]:
		pass
