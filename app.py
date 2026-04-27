import streamlit as st
from datetime import date, datetime, time, timedelta

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

if "current_plan" not in st.session_state:
    st.session_state.current_plan = None

owner = st.session_state.owner
owner.name = owner_name
owner.daily_available_minutes = int(available_minutes)
scheduler = Scheduler()

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

preferred_start = st.time_input("Preferred start time", value=time(7, 0), step=900)

frequency = st.selectbox("Frequency", ["once", "daily", "weekly"], index=0)
due_date_input = st.date_input("Due date", value=date.today())

required_today = st.checkbox("Required today", value=True)

if st.button("Add task"):
    if not owner.pets:
        st.error("Add a pet before adding tasks.")
    else:
        selected_pet = next(pet for pet in owner.pets if pet.name == selected_pet_name)
        preferred_end = (
            datetime.combine(date.today(), preferred_start) + timedelta(minutes=int(duration))
        ).time()
        task = CareTask(
            task_id=f"task-{st.session_state.task_counter:03d}",
            owner_id=owner.owner_id,
            pet_id=selected_pet.pet_id,
            title=task_title,
            duration_minutes=int(duration),
            priority=priority,
            preferred_window_start=preferred_start,
            preferred_window_end=preferred_end,
            required_today=required_today,
            frequency=frequency,
            due_date=due_date_input if frequency in {"daily", "weekly"} else None,
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
                "preferred_start": task.preferred_window_start.strftime("%H:%M")
                if task.preferred_window_start
                else "",
            }
            for task in st.session_state.tasks
        ]
    )

    st.markdown("### Sorted Tasks")
    sorted_tasks = scheduler.order_tasks(st.session_state.tasks)
    st.table(
        [
            {
                "task_id": task.task_id,
                "pet": pet_lookup[task.pet_id].name if task.pet_id in pet_lookup else "Unknown",
                "title": task.title,
                "preferred_start": task.preferred_window_start.strftime("%H:%M")
                if task.preferred_window_start
                else "",
                "priority": task.priority,
                "required_today": task.required_today,
            }
            for task in sorted_tasks
        ]
    )

    st.markdown("### Filter Tasks")
    filter_col1, filter_col2 = st.columns(2)
    with filter_col1:
        status_filter = st.selectbox(
            "Filter by status",
            ["all", "pending", "completed", "skipped"],
            index=0,
        )
    with filter_col2:
        pet_filter = st.selectbox("Filter by pet", ["all"] + pet_names, index=0)

    filtered_tasks = scheduler.filter_tasks(
        tasks=st.session_state.tasks,
        pets=owner.pets,
        status=None if status_filter == "all" else status_filter,
        pet_name=None if pet_filter == "all" else pet_filter,
    )
    st.table(
        [
            {
                "task_id": task.task_id,
                "pet": pet_lookup[task.pet_id].name if task.pet_id in pet_lookup else "Unknown",
                "title": task.title,
                "status": task.status,
                "priority": task.priority,
                "frequency": task.frequency,
                "due_date": task.due_date.isoformat() if task.due_date else "",
            }
            for task in filtered_tasks
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
        plan = scheduler.generate_plan(
            owner=owner,
            pets=owner.list_pets(),
            tasks=st.session_state.tasks,
            plan_date=date.today(),
            day_start=time(7, 0),
        )
        st.session_state.current_plan = plan
        st.success("Schedule generated.")

if st.session_state.current_plan is not None:
    plan = st.session_state.current_plan
    task_lookup = {task.task_id: task for task in st.session_state.tasks}
    pet_lookup = {pet.pet_id: pet for pet in owner.pets}

    st.write(plan.get_summary())

    if plan.conflict_warnings:
        st.markdown("### Schedule Warnings")
        for warning in plan.conflict_warnings:
            st.warning(warning)
    else:
        st.success("No schedule conflicts detected.")

    if plan.scheduled_tasks:
        st.markdown("### Today's Schedule")
        st.table(
            [
                {
                    "scheduled_task_id": item.scheduled_task_id,
                    "start": item.start_time.strftime("%H:%M"),
                    "end": item.end_time.strftime("%H:%M"),
                    "pet": pet_lookup[item.pet_id].name if item.pet_id in pet_lookup else "Unknown",
                    "task": task_lookup[item.task_id].title if item.task_id in task_lookup else item.task_id,
                    "priority": task_lookup[item.task_id].priority if item.task_id in task_lookup else "n/a",
                    "status": item.status,
                }
                for item in plan.scheduled_tasks
            ]
        )

        pending_items = [item for item in plan.scheduled_tasks if item.status == "pending"]
        if pending_items:
            pending_label_map = {
                f"{item.scheduled_task_id} | "
                f"{task_lookup[item.task_id].title if item.task_id in task_lookup else item.task_id}": item.scheduled_task_id
                for item in pending_items
            }
            selected_label = st.selectbox(
                "Mark a scheduled task complete",
                options=list(pending_label_map.keys()),
            )
            if st.button("Complete selected task"):
                selected_scheduled_task_id = pending_label_map[selected_label]
                next_task = scheduler.mark_task_complete(
                    plan=plan,
                    scheduled_task_id=selected_scheduled_task_id,
                    tasks=st.session_state.tasks,
                )
                if next_task is not None:
                    owner_pet = next(
                        (pet for pet in owner.pets if pet.pet_id == next_task.pet_id),
                        None,
                    )
                    if owner_pet and not any(t.task_id == next_task.task_id for t in owner_pet.tasks):
                        owner_pet.add_task(next_task)
                    st.success(
                        f"Completed task and created next {next_task.frequency} occurrence due {next_task.due_date}."
                    )
                else:
                    st.success("Scheduled task marked complete.")
                st.rerun()
        else:
            st.info("All scheduled tasks are completed or skipped.")

    if plan.unscheduled_task_ids:
        st.markdown("### Unscheduled Tasks")
        st.write(
            [
                task_lookup[task_id].title if task_id in task_lookup else task_id
                for task_id in plan.unscheduled_task_ids
            ]
        )

st.divider()

st.subheader("Ask PawPal")
st.caption("Free-text Q&A grounded in a small local pet-care knowledge base.")

st.markdown(
    """
    <style>
    [data-testid="stSpinner"] {
        position: fixed;
        inset: 0;
        background: rgba(255, 255, 255, 0.55);
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        display: flex !important;
        align-items: center;
        justify-content: center;
        z-index: 9999;
    }
    [data-testid="stSpinner"] > div {
        background: white;
        padding: 22px 30px;
        border-radius: 12px;
        box-shadow: 0 12px 48px rgba(0, 0, 0, 0.18);
        font-size: 1.05rem;
        font-weight: 500;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource(show_spinner="Loading knowledge base...")
def get_index():
    from pathlib import Path

    from rag.care_kb import build_index, load_index

    corpus_dir = Path("data/care_tips")
    index_path = Path("rag/index.npz")
    if not index_path.exists():
        build_index(corpus_dir, index_path)
    return load_index(index_path)


question = st.text_input(
    "Ask a pet-care question",
    placeholder="How long should I walk a 3-year-old labrador?",
)

if st.button("Ask"):
    if not question.strip():
        st.info("Type a question first.")
    else:
        from rag.care_kb import query

        try:
            with st.spinner("Thinking..."):
                index = get_index()
                result = query(index, question.strip())
        except ValueError as exc:
            st.error(f"Knowledge base error: {exc}")
        else:
            if result.confident:
                st.markdown(result.answer)
            else:
                st.warning(result.answer)

            with st.expander("Retrieved snippets"):
                st.dataframe(
                    [
                        {
                            "filename": match.filename,
                            "score": round(match.score, 3),
                            "preview": match.text.strip().lstrip("#").strip().replace("\n", " ")[:120],
                        }
                        for match in result.matches
                    ],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "filename": st.column_config.TextColumn("filename", width="medium"),
                        "score": st.column_config.NumberColumn("score", width="small", format="%.3f"),
                        "preview": st.column_config.TextColumn("preview", width="large"),
                    },
                )
