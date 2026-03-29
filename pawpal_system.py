from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from typing import Literal


Priority = Literal["low", "medium", "high"]
TaskStatus = Literal["pending", "completed", "skipped"]
TaskFrequency = Literal["once", "daily", "weekly"]


def _priority_score(priority: Priority) -> int:
    """Return a numeric score so higher priority tasks sort first."""
    scores = {"high": 0, "medium": 1, "low": 2}
    return scores[priority]


def _minutes_since_midnight(value: time) -> int:
    """Convert a time value to minutes elapsed since midnight."""
    return value.hour * 60 + value.minute


def _add_minutes(value: time, minutes: int) -> time:
    """Return a new time created by adding minutes to a base time."""
    base = datetime.combine(date.today(), value)
    return (base.replace(second=0, microsecond=0) + timedelta(minutes=minutes)).time()


def _duration_minutes(start: time, end: time) -> int:
    """Return the minute duration between two times."""
    return _minutes_since_midnight(end) - _minutes_since_midnight(start)


def _time_sort_key(value: time | str | None) -> time:
    """Convert a time-like value into a sortable time, defaulting missing values to end-of-day."""
    if value is None:
        return time(23, 59)
    if isinstance(value, str):
        return datetime.strptime(value, "%H:%M").time()
    return value


@dataclass
class Owner:
    owner_id: str
    name: str
    daily_available_minutes: int
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner after validating ownership and uniqueness."""
        if pet.owner_id != self.owner_id:
            raise ValueError("Pet owner_id does not match Owner.owner_id.")
        if any(existing.pet_id == pet.pet_id for existing in self.pets):
            raise ValueError(f"Pet with id '{pet.pet_id}' already exists for this owner.")
        self.pets.append(pet)

    def remove_pet(self, pet_id: str) -> None:
        """Remove a pet from this owner by pet identifier."""
        for index, pet in enumerate(self.pets):
            if pet.pet_id == pet_id:
                del self.pets[index]
                return
        raise ValueError(f"Pet with id '{pet_id}' was not found.")

    def list_pets(self) -> list[Pet]:
        """Return a copy of the owner's current pet list."""
        return list(self.pets)


@dataclass
class Pet:
    pet_id: str
    owner_id: str
    name: str
    species: str
    notes: str
    tasks: list[CareTask] = field(default_factory=list)

    def update_profile(self, name: str, species: str, notes: str) -> None:
        """Update the pet's profile details."""
        self.name = name
        self.species = species
        self.notes = notes

    def add_task(self, task: CareTask) -> None:
        """Attach a care task to this pet after relationship checks."""
        if task.pet_id != self.pet_id:
            raise ValueError("Task pet_id does not match Pet.pet_id.")
        if task.owner_id != self.owner_id:
            raise ValueError("Task owner_id does not match Pet.owner_id.")
        if any(existing.task_id == task.task_id for existing in self.tasks):
            raise ValueError(f"Task with id '{task.task_id}' already exists for this pet.")
        self.tasks.append(task)

    def remove_task(self, task_id: str) -> None:
        """Remove a task from this pet by task identifier."""
        for index, task in enumerate(self.tasks):
            if task.task_id == task_id:
                del self.tasks[index]
                return
        raise ValueError(f"Task with id '{task_id}' was not found for this pet.")

    def list_tasks(self) -> list[CareTask]:
        """Return a copy of tasks currently assigned to this pet."""
        return list(self.tasks)


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
    frequency: TaskFrequency = "once"
    due_date: date | None = None
    status: TaskStatus = "pending"
    completed_at: datetime | None = None
    skipped_reason: str | None = None

    def mark_complete(self) -> CareTask | None:
        """Mark this care task complete and return its next occurrence when recurring."""
        self.status = "completed"
        self.completed_at = datetime.now()
        self.skipped_reason = None
        return self.create_next_occurrence()

    def mark_skipped(self, reason: str) -> None:
        """Mark this care task as skipped with a reason."""
        self.status = "skipped"
        self.skipped_reason = reason
        self.completed_at = None

    def create_next_occurrence(self) -> CareTask | None:
        """Create the next task instance when frequency is daily or weekly."""
        if self.frequency == "once":
            return None

        base_due_date = self.due_date or date.today()
        if self.frequency == "daily":
            next_due_date = base_due_date + timedelta(days=1)
        else:
            next_due_date = base_due_date + timedelta(days=7)

        next_task_id = f"{self.task_id}-next-{next_due_date.isoformat()}"
        return CareTask(
            task_id=next_task_id,
            owner_id=self.owner_id,
            pet_id=self.pet_id,
            title=self.title,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            preferred_window_start=self.preferred_window_start,
            preferred_window_end=self.preferred_window_end,
            required_today=False,
            frequency=self.frequency,
            due_date=next_due_date,
        )


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
        """Set this scheduled task status to completed."""
        self.status = "completed"
        self.completed_at = datetime.now()
        self.skipped_reason = None

    def set_skipped(self, reason: str) -> None:
        """Set this scheduled task status to skipped with a reason."""
        self.status = "skipped"
        self.skipped_reason = reason
        self.completed_at = None


@dataclass
class DailyPlan:
    plan_id: str
    owner_id: str
    plan_date: date
    unscheduled_task_ids: list[str] = field(default_factory=list)
    scheduled_tasks: list[ScheduledTask] = field(default_factory=list)
    conflict_warnings: list[str] = field(default_factory=list)

    def add_scheduled_task(self, item: ScheduledTask) -> None:
        """Add a scheduled task to this plan after basic integrity checks."""
        if item.plan_id != self.plan_id:
            raise ValueError("ScheduledTask.plan_id does not match DailyPlan.plan_id.")
        if any(existing.scheduled_task_id == item.scheduled_task_id for existing in self.scheduled_tasks):
            raise ValueError(
                f"Scheduled task id '{item.scheduled_task_id}' already exists in this plan."
            )
        if _duration_minutes(item.start_time, item.end_time) <= 0:
            raise ValueError("ScheduledTask end_time must be after start_time.")
        self.scheduled_tasks.append(item)

    def mark_task_complete(self, scheduled_task_id: str) -> None:
        """Mark one scheduled task complete using its scheduled task identifier."""
        for item in self.scheduled_tasks:
            if item.scheduled_task_id == scheduled_task_id:
                item.set_completed()
                return
        raise ValueError(f"Scheduled task with id '{scheduled_task_id}' was not found.")

    def calculate_total_minutes(self) -> int:
        """Compute total scheduled minutes across all scheduled tasks."""
        return sum(_duration_minutes(item.start_time, item.end_time) for item in self.scheduled_tasks)

    def get_summary(self) -> str:
        """Build a one-line summary of schedule status and totals."""
        total = len(self.scheduled_tasks)
        completed = sum(1 for item in self.scheduled_tasks if item.status == "completed")
        skipped = sum(1 for item in self.scheduled_tasks if item.status == "skipped")
        pending = total - completed - skipped
        total_minutes = self.calculate_total_minutes()
        return (
            f"Plan {self.plan_id} on {self.plan_date}: "
            f"{total} scheduled ({completed} completed, {pending} pending, {skipped} skipped), "
            f"{len(self.unscheduled_task_ids)} unscheduled, {total_minutes} total minutes."
        )


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
        """Generate a daily plan from owner, pets, tasks, and start time."""
        self.validate_ownership(owner, pets, tasks)
        selected_tasks = self.select_tasks(tasks, owner.daily_available_minutes)
        ordered_tasks = self.order_tasks(selected_tasks)
        plan_id = f"{owner.owner_id}-{plan_date.isoformat()}"
        scheduled_tasks = self.assign_times(ordered_tasks, day_start, plan_id)

        selected_ids = {task.task_id for task in selected_tasks}
        unscheduled_ids = [task.task_id for task in tasks if task.task_id not in selected_ids]

        plan = DailyPlan(
            plan_id=plan_id,
            owner_id=owner.owner_id,
            plan_date=plan_date,
            unscheduled_task_ids=unscheduled_ids,
        )
        for item in scheduled_tasks:
            plan.add_scheduled_task(item)
        plan.conflict_warnings = self.detect_conflicts(plan.scheduled_tasks, tasks, pets)
        return plan

    def validate_ownership(self, owner: Owner, pets: list[Pet], tasks: list[CareTask]) -> None:
        """Validate that all pets and tasks belong to the provided owner."""
        pet_ids = {pet.pet_id for pet in pets}
        for pet in pets:
            if pet.owner_id != owner.owner_id:
                raise ValueError(
                    f"Pet '{pet.pet_id}' does not belong to owner '{owner.owner_id}'."
                )
        for task in tasks:
            if task.owner_id != owner.owner_id:
                raise ValueError(
                    f"Task '{task.task_id}' does not belong to owner '{owner.owner_id}'."
                )
            if task.pet_id not in pet_ids:
                raise ValueError(
                    f"Task '{task.task_id}' references unknown pet '{task.pet_id}'."
                )

    def mark_task_complete(
        self,
        plan: DailyPlan,
        scheduled_task_id: str,
        tasks: list[CareTask],
    ) -> CareTask | None:
        """Complete a scheduled task and append the next recurring occurrence when applicable."""
        matched_item = next(
            (item for item in plan.scheduled_tasks if item.scheduled_task_id == scheduled_task_id),
            None,
        )
        if matched_item is None:
            raise ValueError(f"Scheduled task with id '{scheduled_task_id}' was not found.")

        plan.mark_task_complete(scheduled_task_id)

        matched_task = next((task for task in tasks if task.task_id == matched_item.task_id), None)
        if matched_task is None:
            return None

        next_task = matched_task.mark_complete()
        if next_task is not None:
            tasks.append(next_task)
        return next_task

    def filter_tasks(
        self,
        tasks: list[CareTask],
        pets: list[Pet],
        status: TaskStatus | None = None,
        pet_name: str | None = None,
    ) -> list[CareTask]:
        """Filter tasks by optional status and/or pet name."""
        filtered = list(tasks)

        if status is not None:
            filtered = [task for task in filtered if task.status == status]

        if pet_name is not None:
            normalized_name = pet_name.strip().lower()
            matching_pet_ids = {
                pet.pet_id for pet in pets if pet.name.strip().lower() == normalized_name
            }
            filtered = [task for task in filtered if task.pet_id in matching_pet_ids]

        return filtered

    def detect_conflicts(
        self,
        scheduled_tasks: list[ScheduledTask],
        tasks: list[CareTask],
        pets: list[Pet],
    ) -> list[str]:
        """Return warning messages for overlapping scheduled tasks."""
        warnings: list[str] = []
        task_lookup = {task.task_id: task for task in tasks}
        pet_lookup = {pet.pet_id: pet for pet in pets}

        for index, first in enumerate(scheduled_tasks):
            for second in scheduled_tasks[index + 1 :]:
                if not self._tasks_overlap(first, second):
                    continue

                first_task = task_lookup.get(first.task_id)
                second_task = task_lookup.get(second.task_id)
                first_title = first_task.title if first_task else first.task_id
                second_title = second_task.title if second_task else second.task_id
                first_pet = pet_lookup.get(first.pet_id)
                second_pet = pet_lookup.get(second.pet_id)
                first_pet_name = first_pet.name if first_pet else first.pet_id
                second_pet_name = second_pet.name if second_pet else second.pet_id
                relation = "same pet" if first.pet_id == second.pet_id else "different pets"

                warnings.append(
                    "Conflict warning: "
                    f"{first.start_time.strftime('%H:%M')}-{first.end_time.strftime('%H:%M')} "
                    f"({first_title} for {first_pet_name}) overlaps with "
                    f"{second.start_time.strftime('%H:%M')}-{second.end_time.strftime('%H:%M')} "
                    f"({second_title} for {second_pet_name}) [{relation}]."
                )

        return warnings

    def _tasks_overlap(self, first: ScheduledTask, second: ScheduledTask) -> bool:
        """Return True when two scheduled tasks overlap in time."""
        first_start = _minutes_since_midnight(first.start_time)
        first_end = _minutes_since_midnight(first.end_time)
        second_start = _minutes_since_midnight(second.start_time)
        second_end = _minutes_since_midnight(second.end_time)
        return first_start < second_end and second_start < first_end

    def select_tasks(self, tasks: list[CareTask], available_minutes: int) -> list[CareTask]:
        """Select tasks that fit available minutes using required and priority order."""
        if available_minutes <= 0:
            return []

        ordered = sorted(
            tasks,
            key=lambda task: (
                0 if task.required_today else 1,
                _priority_score(task.priority),
                task.duration_minutes,
            ),
        )

        selected: list[CareTask] = []
        remaining = available_minutes
        for task in ordered:
            if task.duration_minutes <= remaining:
                selected.append(task)
                remaining -= task.duration_minutes
        return selected

    def order_tasks(self, tasks: list[CareTask]) -> list[CareTask]:
        """Return tasks sorted by start time, then required flag, priority, and duration."""
        return sorted(
            tasks,
            key=lambda task: (
                _time_sort_key(task.preferred_window_start),
                0 if task.required_today else 1,
                _priority_score(task.priority),
                task.duration_minutes,
            ),
        )

    def assign_times(
        self, tasks: list[CareTask], day_start: time, plan_id: str
    ) -> list[ScheduledTask]:
        """Assign sequential time slots to tasks starting from the given time."""
        scheduled: list[ScheduledTask] = []
        current_time = day_start
        for index, task in enumerate(tasks, start=1):
            end_time = _add_minutes(current_time, task.duration_minutes)
            scheduled.append(
                ScheduledTask(
                    scheduled_task_id=f"{plan_id}-{index}",
                    plan_id=plan_id,
                    task_id=task.task_id,
                    pet_id=task.pet_id,
                    start_time=current_time,
                    end_time=end_time,
                )
            )
            current_time = end_time
        return scheduled
