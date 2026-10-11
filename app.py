from datetime import date

import streamlit as st
from pawpal_system import PawPal, Owner, Pet, Task, Schedule, Scheduler

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

# Session "vault": Streamlit re-runs this script on every interaction, so the
# PawPal and Owner are only created if they are not already stored.
if "pawpal" not in st.session_state:
    st.session_state.pawpal = PawPal()

st.subheader("Owner & Pets")

if "owner" not in st.session_state:
    owner_name = st.text_input("Owner name", key="owner_name_input")
    if st.button("Create owner"):
        try:
            st.session_state.owner = st.session_state.pawpal.add_owner(owner_name)
            st.rerun()
        except ValueError as e:
            st.error(str(e))
    st.info("Create an owner to start adding pets and tasks.")
    st.stop()

owner = st.session_state.owner
st.write(f"Owner: **{owner.name}**")

pet_name = st.text_input("Pet name", key="pet_name_input")
species = st.selectbox("Species", ["dog", "cat", "other"])
age = st.number_input("Age", min_value=0, max_value=40, value=None, step=1)

if st.button("Add pet"):
    if age is None:
        st.error("Enter the pet's age.")
    else:
        try:
            owner.add_pet(pet_name, species, int(age))
        except ValueError as e:
            st.error(str(e))

if owner.get_pets():
    st.write(f"{owner.name}'s pets:")
    st.table(
        [
            {"Name": p.name, "Type": p.pet_type.title(), "Age": p.age}
            for p in owner.get_pets()
        ]
    )
else:
    st.info("No pets yet. Add one above.")

st.markdown("### Tasks")

pets_by_name = {p.name: p for p in owner.get_pets()}

if not pets_by_name:
    st.info("Add a pet first, then you can add tasks for it.")
else:
    task_pet_name = st.selectbox("Pet", list(pets_by_name))

    col1, col2 = st.columns(2)
    with col1:
        task_title = st.text_input("Task title")
        category = st.selectbox("Category", Task.CATEGORIES)
        task_date = st.date_input("Date", value=date.today())
    with col2:
        start_time = st.time_input("Start time", value=None)
        end_time = st.time_input("End time", value=None)
        priority = st.slider(
            "Priority (5 = most important)", Task.MIN_PRIORITY, Task.MAX_PRIORITY, 3
        )

    recurrence = st.selectbox("Repeats", Task.RECURRENCES)
    comment = st.text_input("Note (optional)")

    if st.button("Add task"):
        if start_time is None or end_time is None:
            st.error("Enter a start time and an end time.")
        else:
            try:
                new_task = Task(
                    task_title,
                    category,
                    task_date,
                    start_time,
                    end_time,
                    priority,
                    comment,
                    recurrence,
                )
                pets_by_name[task_pet_name].add_task(new_task)
            except ValueError as e:
                st.error(str(e))
            else:
                for message in Scheduler(owner).warnings_for(new_task):
                    st.warning(message)

all_tasks = sorted(owner.get_all_tasks(), key=lambda t: (t.date, t.start_time))
if all_tasks:
    st.write("Current tasks:")
    st.table(
        [
            {
                "Pet": t.pet.name,
                "Task": t.name,
                "Category": t.category,
                "Date": t.date.strftime("%b %d, %Y"),
                "Time": f"{t.start_time:%I:%M %p} - {t.end_time:%I:%M %p}",
                "Priority": t.priority,
                "Repeats": t.recurrence,
            }
            for t in all_tasks
        ]
    )
elif pets_by_name:
    st.info("No tasks yet. Add one above.")

st.divider()

st.subheader("Build Schedule")
plan_date = st.date_input("Schedule for", value=date.today(), key="plan_date")

filter_col1, filter_col2 = st.columns(2)
with filter_col1:
    pet_choice = st.selectbox("Show pet", ["All pets"] + list(pets_by_name), key="pet_filter")
with filter_col2:
    status_choice = st.selectbox("Show status", ["All", "Pending", "Done"], key="status_filter")


def complete_task(task: Task, on: date) -> None:
    """Button callback: mark the task done and note any follow-up that was created."""
    follow_up = task.mark_complete(on)
    if follow_up:
        st.session_state.notice = (
            f"Next '{follow_up.name}' ({follow_up.pet.name}) created for "
            f"{follow_up.date.strftime('%a, %b %d')}."
        )


if "notice" in st.session_state:
    st.toast(st.session_state.pop("notice"))

scheduler = Scheduler(owner)
day_plan = scheduler.daily_plan(plan_date)
plan = scheduler.filter_tasks(
    plan_date,
    pet_name=None if pet_choice == "All pets" else pet_choice,
    status=None if status_choice == "All" else status_choice.lower(),
)

if not day_plan:
    st.info(f"No tasks scheduled for {plan_date.strftime('%A, %B %d, %Y')}.")
else:
    st.write(f"Schedule for {plan_date.strftime('%A, %B %d, %Y')}:")
    if plan:
        widths = [1.6, 2.3, 2.3, 1.6, 1.6, 0.9]
        for col, label in zip(st.columns(widths), ["Status", "Time", "Task", "Pet", "Category", "Priority"]):
            col.markdown(f"**{label}**")
        for t in plan:
            status_col, time_col, task_col, pet_col, category_col, priority_col = st.columns(widths)
            if t.is_complete(plan_date):
                status_col.write("Done ✓")
            else:
                status_col.button(
                    "Mark done",
                    key=f"done_{t.id}",
                    on_click=complete_task,
                    args=(t, plan_date),
                )
            time_col.write(f"{t.start_time:%I:%M %p} - {t.end_time:%I:%M %p}")
            task_col.write(t.name)
            if t.comment:
                task_col.caption(t.comment)
            pet_col.write(t.pet.name)
            category_col.write(t.category)
            priority_col.write(t.priority)
    else:
        st.info("No tasks match the selected filters.")

    # Time left and conflicts always describe the whole day, not the filtered view.
    remaining = scheduler.remaining_minutes(plan_date)
    if remaining < 0:
        st.warning(f"Overbooked by {-remaining:.0f} minutes.")
    else:
        st.success(f"{remaining:.0f} of {owner.daily_available_minutes} minutes remaining.")

    for a, b in scheduler.find_conflicts(plan_date):
        message = scheduler.describe_conflict(a, b)
        if scheduler.is_shared_time(a, b):
            st.info(message)
        else:
            st.warning(message)
