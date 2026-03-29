from datetime import date, time

from pawpal_system import CareTask, DailyPlan, Pet, ScheduledTask, Scheduler


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


def test_filter_tasks_by_status_and_pet_name() -> None:
	dog = Pet(
		pet_id="pet-001",
		owner_id="owner-001",
		name="Mochi",
		species="dog",
		notes="",
	)
	cat = Pet(
		pet_id="pet-002",
		owner_id="owner-001",
		name="Luna",
		species="cat",
		notes="",
	)

	tasks = [
		CareTask(
			task_id="task-001",
			owner_id="owner-001",
			pet_id=dog.pet_id,
			title="Walk",
			duration_minutes=20,
			priority="high",
			preferred_window_start=time(7, 0),
			preferred_window_end=time(8, 0),
			required_today=True,
		),
		CareTask(
			task_id="task-002",
			owner_id="owner-001",
			pet_id=cat.pet_id,
			title="Feed",
			duration_minutes=10,
			priority="medium",
			preferred_window_start=time(8, 0),
			preferred_window_end=time(9, 0),
			required_today=True,
		),
	]
	tasks[0].mark_complete()

	scheduler = Scheduler()
	completed = scheduler.filter_tasks(tasks=tasks, pets=[dog, cat], status="completed")
	for_luna = scheduler.filter_tasks(tasks=tasks, pets=[dog, cat], pet_name="Luna")

	assert len(completed) == 1
	assert completed[0].task_id == "task-001"
	assert len(for_luna) == 1
	assert for_luna[0].task_id == "task-002"


def test_marking_daily_task_complete_creates_next_occurrence() -> None:
	dog = Pet(
		pet_id="pet-001",
		owner_id="owner-001",
		name="Mochi",
		species="dog",
		notes="",
	)
	task = CareTask(
		task_id="task-010",
		owner_id="owner-001",
		pet_id=dog.pet_id,
		title="Daily Walk",
		duration_minutes=20,
		priority="high",
		preferred_window_start=time(7, 0),
		preferred_window_end=time(8, 0),
		required_today=True,
		frequency="daily",
		due_date=date(2026, 3, 29),
	)

	plan = DailyPlan(
		plan_id="owner-001-2026-03-29",
		owner_id="owner-001",
		plan_date=date(2026, 3, 29),
	)
	plan.add_scheduled_task(
		item=ScheduledTask(
			scheduled_task_id="owner-001-2026-03-29-1",
			plan_id=plan.plan_id,
			task_id=task.task_id,
			pet_id=dog.pet_id,
			start_time=time(7, 0),
			end_time=time(7, 20),
		)
	)

	tasks = [task]
	scheduler = Scheduler()
	next_task = scheduler.mark_task_complete(
		plan=plan,
		scheduled_task_id="owner-001-2026-03-29-1",
		tasks=tasks,
	)

	assert task.status == "completed"
	assert next_task is not None
	assert next_task.due_date == date(2026, 3, 30)
	assert len(tasks) == 2


def test_order_tasks_returns_chronological_order() -> None:
	tasks = [
		CareTask(
			task_id="task-early",
			owner_id="owner-001",
			pet_id="pet-001",
			title="Early Task",
			duration_minutes=15,
			priority="medium",
			preferred_window_start=time(7, 0),
			preferred_window_end=time(7, 30),
			required_today=False,
		),
		CareTask(
			task_id="task-late",
			owner_id="owner-001",
			pet_id="pet-001",
			title="Late Task",
			duration_minutes=15,
			priority="high",
			preferred_window_start=time(10, 0),
			preferred_window_end=time(10, 30),
			required_today=True,
		),
		CareTask(
			task_id="task-mid",
			owner_id="owner-001",
			pet_id="pet-001",
			title="Mid Task",
			duration_minutes=15,
			priority="low",
			preferred_window_start=time(8, 30),
			preferred_window_end=time(9, 0),
			required_today=False,
		),
	]

	scheduler = Scheduler()
	ordered = scheduler.order_tasks(tasks)

	assert [task.task_id for task in ordered] == ["task-early", "task-mid", "task-late"]


def test_detect_conflicts_returns_warning_message() -> None:
	dog = Pet(
		pet_id="pet-001",
		owner_id="owner-001",
		name="Mochi",
		species="dog",
		notes="",
	)
	cat = Pet(
		pet_id="pet-002",
		owner_id="owner-001",
		name="Luna",
		species="cat",
		notes="",
	)
	tasks = [
		CareTask(
			task_id="task-101",
			owner_id="owner-001",
			pet_id=dog.pet_id,
			title="Dog Walk",
			duration_minutes=30,
			priority="high",
			preferred_window_start=time(7, 0),
			preferred_window_end=time(8, 0),
			required_today=True,
		),
		CareTask(
			task_id="task-102",
			owner_id="owner-001",
			pet_id=cat.pet_id,
			title="Cat Feed",
			duration_minutes=20,
			priority="medium",
			preferred_window_start=time(7, 15),
			preferred_window_end=time(8, 0),
			required_today=True,
		),
	]

	scheduled_tasks = [
		ScheduledTask(
			scheduled_task_id="plan-1",
			plan_id="plan-a",
			task_id="task-101",
			pet_id=dog.pet_id,
			start_time=time(7, 0),
			end_time=time(7, 30),
		),
		ScheduledTask(
			scheduled_task_id="plan-2",
			plan_id="plan-a",
			task_id="task-102",
			pet_id=cat.pet_id,
			start_time=time(7, 15),
			end_time=time(7, 35),
		),
	]

	scheduler = Scheduler()
	warnings = scheduler.detect_conflicts(scheduled_tasks=scheduled_tasks, tasks=tasks, pets=[dog, cat])

	assert len(warnings) == 1
	assert "overlaps" in warnings[0]


def test_detect_conflicts_flags_duplicate_times() -> None:
	dog = Pet(
		pet_id="pet-001",
		owner_id="owner-001",
		name="Mochi",
		species="dog",
		notes="",
	)
	tasks = [
		CareTask(
			task_id="task-201",
			owner_id="owner-001",
			pet_id=dog.pet_id,
			title="Breakfast",
			duration_minutes=20,
			priority="high",
			preferred_window_start=time(8, 0),
			preferred_window_end=time(8, 30),
			required_today=True,
		),
		CareTask(
			task_id="task-202",
			owner_id="owner-001",
			pet_id=dog.pet_id,
			title="Medication",
			duration_minutes=20,
			priority="high",
			preferred_window_start=time(8, 0),
			preferred_window_end=time(8, 30),
			required_today=True,
		),
	]

	scheduled_tasks = [
		ScheduledTask(
			scheduled_task_id="plan-dup-1",
			plan_id="plan-dup",
			task_id="task-201",
			pet_id=dog.pet_id,
			start_time=time(8, 0),
			end_time=time(8, 30),
		),
		ScheduledTask(
			scheduled_task_id="plan-dup-2",
			plan_id="plan-dup",
			task_id="task-202",
			pet_id=dog.pet_id,
			start_time=time(8, 0),
			end_time=time(8, 30),
		),
	]

	scheduler = Scheduler()
	warnings = scheduler.detect_conflicts(scheduled_tasks=scheduled_tasks, tasks=tasks, pets=[dog])

	assert len(warnings) == 1
	assert "08:00-08:30" in warnings[0]
	assert "same pet" in warnings[0]
