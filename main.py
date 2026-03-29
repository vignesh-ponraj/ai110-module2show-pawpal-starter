from datetime import date, time

from pawpal_system import CareTask, Owner, Pet, Scheduler


def build_demo_data() -> tuple[Owner, list[Pet], list[CareTask]]:
	owner = Owner(owner_id="owner-001", name="Jordan", daily_available_minutes=120)

	dog = Pet(
		pet_id="pet-001",
		owner_id=owner.owner_id,
		name="Mochi",
		species="dog",
		notes="High energy in the morning.",
	)
	cat = Pet(
		pet_id="pet-002",
		owner_id=owner.owner_id,
		name="Luna",
		species="cat",
		notes="Prefers quiet play in the evening.",
	)

	owner.add_pet(dog)
	owner.add_pet(cat)

	tasks = [
		CareTask(
			task_id="task-001",
			owner_id=owner.owner_id,
			pet_id=dog.pet_id,
			title="Morning Walk",
			duration_minutes=30,
			priority="high",
			preferred_window_start=time(7, 0),
			preferred_window_end=time(9, 0),
			required_today=True,
		),
		CareTask(
			task_id="task-002",
			owner_id=owner.owner_id,
			pet_id=cat.pet_id,
			title="Breakfast Feeding",
			duration_minutes=15,
			priority="high",
			preferred_window_start=time(8, 0),
			preferred_window_end=time(10, 0),
			required_today=True,
		),
		CareTask(
			task_id="task-003",
			owner_id=owner.owner_id,
			pet_id=dog.pet_id,
			title="Evening Play Session",
			duration_minutes=25,
			priority="medium",
			preferred_window_start=time(17, 0),
			preferred_window_end=time(19, 0),
			required_today=False,
		),
	]

	dog.add_task(tasks[0])
	cat.add_task(tasks[1])
	dog.add_task(tasks[2])

	return owner, [dog, cat], tasks


def print_schedule(owner: Owner, pets: list[Pet], tasks: list[CareTask]) -> None:
	scheduler = Scheduler()
	plan = scheduler.generate_plan(
		owner=owner,
		pets=pets,
		tasks=tasks,
		plan_date=date.today(),
		day_start=time(7, 0),
	)

	task_by_id = {task.task_id: task for task in tasks}
	pet_by_id = {pet.pet_id: pet for pet in pets}

	print("\n=== Today's Schedule ===")
	print(f"Owner: {owner.name}")
	print(f"Date: {plan.plan_date.isoformat()}")
	print()

	if not plan.scheduled_tasks:
		print("No tasks were scheduled today.")
	else:
		for item in plan.scheduled_tasks:
			task = task_by_id[item.task_id]
			pet = pet_by_id[item.pet_id]
			start_label = item.start_time.strftime("%H:%M")
			end_label = item.end_time.strftime("%H:%M")
			print(
				f"{start_label}-{end_label} | {pet.name} ({pet.species}) | "
				f"{task.title} [{task.priority}]"
			)

	if plan.unscheduled_task_ids:
		print("\nUnscheduled Tasks:")
		for task_id in plan.unscheduled_task_ids:
			task = task_by_id[task_id]
			print(f"- {task.title} ({task.duration_minutes} min)")

	print("\n" + plan.get_summary())


if __name__ == "__main__":
	demo_owner, demo_pets, demo_tasks = build_demo_data()
	print_schedule(demo_owner, demo_pets, demo_tasks)
