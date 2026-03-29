from datetime import time

from pawpal_system import CareTask, Pet


def test_task_completion_changes_status() -> None:
	task = CareTask(
		task_id="task-001",
		owner_id="owner-001",
		pet_id="pet-001",
		title="Morning Walk",
		duration_minutes=30,
		priority="high",
		preferred_window_start=time(7, 0),
		preferred_window_end=time(9, 0),
		required_today=True,
	)

	task.mark_complete()

	assert task.status == "completed"


def test_adding_task_increases_pet_task_count() -> None:
	pet = Pet(
		pet_id="pet-001",
		owner_id="owner-001",
		name="Mochi",
		species="dog",
		notes="Loves long walks",
	)
	task = CareTask(
		task_id="task-002",
		owner_id="owner-001",
		pet_id="pet-001",
		title="Breakfast",
		duration_minutes=15,
		priority="medium",
		preferred_window_start=time(8, 0),
		preferred_window_end=time(9, 0),
		required_today=True,
	)

	initial_count = len(pet.tasks)
	pet.add_task(task)

	assert len(pet.tasks) == initial_count + 1
