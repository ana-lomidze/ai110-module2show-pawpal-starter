from datetime import date, time

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

st.subheader("Owner & Pets")
owner_name = st.text_input("Owner name", value="Jordan")
pet_name = st.text_input("Pet name", value="Mochi")
species = st.selectbox("Species", ["dog", "cat", "other"])
age = st.number_input("Age", min_value=0, max_value=40, value=1)

# Session "vault": Streamlit re-runs this script on every interaction, so the
# PawPal and Owner are only created if they are not already stored.
if "pawpal" not in st.session_state:
    st.session_state.pawpal = PawPal()

if "owner" not in st.session_state:
    st.session_state.owner = st.session_state.pawpal.add_owner(owner_name)

owner = st.session_state.owner

if st.button("Add pet"):
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
        task_title = st.text_input("Task title", value="Morning walk")
        category = st.selectbox("Category", Task.CATEGORIES)
        task_date = st.date_input("Date", value=date.today())
    with col2:
        start_time = st.time_input("Start time", value=time(8, 0))
        end_time = st.time_input("End time", value=time(8, 30))
        priority = st.slider(
            "Priority (5 = most important)", Task.MIN_PRIORITY, Task.MAX_PRIORITY, 3
        )

    recurrence = st.selectbox("Repeats", Task.RECURRENCES)
    comment = st.text_input("Note (optional)")

    if st.button("Add task"):
        try:
            pets_by_name[task_pet_name].add_task(
                Task(
                    task_title,
                    category,
                    task_date,
                    start_time,
                    end_time,
                    priority,
                    comment,
                    recurrence,
                )
            )
        except ValueError as e:
            st.error(str(e))

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

if st.button("Generate schedule"):
    scheduler = Scheduler(owner)
    plan = scheduler.daily_plan(plan_date)

    if not plan:
        st.info(f"No tasks scheduled for {plan_date.strftime('%A, %B %d, %Y')}.")
    else:
        st.write(f"Schedule for {plan_date.strftime('%A, %B %d, %Y')}:")
        st.table(
            [
                {
                    "Status": "Done" if t.is_complete(plan_date) else "Not done",
                    "Time": f"{t.start_time:%I:%M %p} - {t.end_time:%I:%M %p}",
                    "Task": t.name,
                    "Pet": t.pet.name,
                    "Category": t.category,
                    "Priority": t.priority,
                    "Note": t.comment,
                }
                for t in plan
            ]
        )

        remaining = scheduler.remaining_minutes(plan_date)
        if remaining < 0:
            st.warning(f"Overbooked by {-remaining:.0f} minutes.")
        else:
            st.success(f"{remaining:.0f} of {owner.daily_available_minutes} minutes remaining.")

        for a, b in scheduler.find_conflicts(plan_date):
            st.warning(f"'{a.name}' ({a.pet.name}) overlaps '{b.name}' ({b.pet.name}).")
