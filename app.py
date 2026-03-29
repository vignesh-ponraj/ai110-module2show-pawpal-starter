import streamlit as st
from datetime import date, time

from pawpal_system import CareTask, Owner, Pet, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

st.subheader("Owner and Pet Setup")
owner_name = st.text_input("Owner name", value="Jordan")
pet_name = st.text_input("Pet name", value="Mochi")
species = st.selectbox("Species", ["dog", "cat", "other"])

available_minutes = st.number_input(
    "Daily available minutes",
    min_value=10,
    max_value=480,
    value=120,
)

if "owner" not in st.session_state:
    st.session_state.owner = Owner(
        owner_id="owner-001",
        name=owner_name,
        daily_available_minutes=int(available_minutes),
    )

if "task_counter" not in st.session_state:
    st.session_state.task_counter = 1

if "tasks" not in st.session_state:
    st.session_state.tasks = []

owner = st.session_state.owner
owner.name = owner_name
owner.daily_available_minutes = int(available_minutes)

if st.button("Add or update pet"):
    existing_pet = next(
        (pet for pet in owner.pets if pet.name.lower() == pet_name.strip().lower()),
        None,
    )
    if existing_pet:
        existing_pet.update_profile(name=pet_name.strip(), species=species, notes="")
        st.success(f"Updated pet profile for {pet_name}.")
    else:
        new_pet = Pet(
            pet_id=f"pet-{len(owner.pets) + 1:03d}",
            owner_id=owner.owner_id,
            name=pet_name.strip(),
            species=species,
            notes="",
        )
        owner.add_pet(new_pet)
        st.success(f"Added pet {pet_name}.")

if owner.pets:
    st.write("Current pets:")
    st.table(
        [
            {
                "pet_id": pet.pet_id,
                "name": pet.name,
                "species": pet.species,
                "tasks": len(pet.tasks),
            }
            for pet in owner.pets
        ]
    )
else:
    st.info("No pets yet. Add one above.")

st.markdown("### Tasks")
st.caption("Add tasks and save them directly using your backend classes.")

pet_names = [pet.name for pet in owner.pets]
selected_pet_name = st.selectbox(
    "Assign task to pet",
    options=pet_names if pet_names else ["No pets available"],
    disabled=not bool(pet_names),
)

col1, col2, col3 = st.columns(3)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col3:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

required_today = st.checkbox("Required today", value=True)

if st.button("Add task"):
    if not owner.pets:
        st.error("Add a pet before adding tasks.")
    else:
        selected_pet = next(pet for pet in owner.pets if pet.name == selected_pet_name)
        task = CareTask(
            task_id=f"task-{st.session_state.task_counter:03d}",
            owner_id=owner.owner_id,
            pet_id=selected_pet.pet_id,
            title=task_title,
            duration_minutes=int(duration),
            priority=priority,
            preferred_window_start=None,
            preferred_window_end=None,
            required_today=required_today,
        )
        selected_pet.add_task(task)
        st.session_state.tasks.append(task)
        st.session_state.task_counter += 1
        st.success(f"Added task '{task_title}' for {selected_pet.name}.")

if st.session_state.tasks:
    st.write("Current tasks:")
    pet_lookup = {pet.pet_id: pet for pet in owner.pets}
    st.table(
        [
            {
                "task_id": task.task_id,
                "pet": pet_lookup[task.pet_id].name if task.pet_id in pet_lookup else "Unknown",
                "title": task.title,
                "duration_minutes": task.duration_minutes,
                "priority": task.priority,
                "required_today": task.required_today,
            }
            for task in st.session_state.tasks
        ]
    )
else:
    st.info("No tasks yet. Add one above.")

st.divider()

st.subheader("Build Schedule")
st.caption("Generate a schedule using your Scheduler class.")

if st.button("Generate schedule"):
    if not owner.pets:
        st.error("Please add at least one pet first.")
    elif not st.session_state.tasks:
        st.error("Please add at least one task first.")
    else:
        scheduler = Scheduler()
        plan = scheduler.generate_plan(
            owner=owner,
            pets=owner.list_pets(),
            tasks=st.session_state.tasks,
            plan_date=date.today(),
            day_start=time(7, 0),
        )

        task_lookup = {task.task_id: task for task in st.session_state.tasks}
        pet_lookup = {pet.pet_id: pet for pet in owner.pets}

        st.success("Schedule generated.")
        st.write(plan.get_summary())

        if plan.scheduled_tasks:
            st.markdown("### Today's Schedule")
            st.table(
                [
                    {
                        "start": item.start_time.strftime("%H:%M"),
                        "end": item.end_time.strftime("%H:%M"),
                        "pet": pet_lookup[item.pet_id].name if item.pet_id in pet_lookup else "Unknown",
                        "task": task_lookup[item.task_id].title if item.task_id in task_lookup else item.task_id,
                        "priority": task_lookup[item.task_id].priority if item.task_id in task_lookup else "n/a",
                    }
                    for item in plan.scheduled_tasks
                ]
            )

        if plan.unscheduled_task_ids:
            st.markdown("### Unscheduled Tasks")
            st.write(
                [
                    task_lookup[task_id].title if task_id in task_lookup else task_id
                    for task_id in plan.unscheduled_task_ids
                ]
            )
