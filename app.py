from datetime import date

import streamlit as st
from pawpal_system import PawPal, Owner, Pet, Task, Schedule, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="wide")

# Wide layout fits the schedule columns, but on a big screen it stretches them too far apart.
st.markdown(
    "<style>[data-testid='stMainBlockContainer'] {max-width: 1200px;}</style>",
    unsafe_allow_html=True,
)


def table_header(widths: list, labels: list) -> None:
    """Draw a header row for a table made of columns (blank labels leave the cell empty)."""
    for col, label in zip(st.columns(widths), labels):
        if label:
            col.markdown(f"**{label}**")


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
SPECIES = ["dog", "cat", "other"]
species = st.selectbox("Species", SPECIES)
age = st.number_input("Age", min_value=0, max_value=40, value=None, step=1)

if st.button("Add pet"):
    if age is None:
        st.error("Enter the pet's age.")
    else:
        try:
            owner.add_pet(pet_name, species, int(age))
        except ValueError as e:
            st.error(str(e))

def open_pet_panel(index: int, pet: Pet) -> None:
    """Button callback: open the edit form for one pet, loaded with its current values."""
    st.session_state.pet_panel = index
    st.session_state[f"pet_edit_name_{index}"] = pet.name
    st.session_state[f"pet_edit_type_{index}"] = pet.pet_type
    st.session_state[f"pet_edit_age_{index}"] = pet.age


def pet_edit_panel(index: int, pet: Pet) -> None:
    """Show the edit form for a pet, directly under its row."""
    types = SPECIES if pet.pet_type in SPECIES else SPECIES + [pet.pet_type]
    with st.form(f"pet_edit_form_{index}"):
        new_name = st.text_input("Pet name", key=f"pet_edit_name_{index}")
        new_type = st.selectbox("Species", types, key=f"pet_edit_type_{index}")
        new_age = st.number_input("Age", min_value=0, max_value=40, step=1, key=f"pet_edit_age_{index}")
        save_col, cancel_col = st.columns(2)
        save = save_col.form_submit_button("Save")
        cancel = cancel_col.form_submit_button("Cancel")

    if cancel:
        st.session_state.pop("pet_panel", None)
        st.rerun()
    if save:
        old_name = pet.name
        try:
            pet.edit_info(new_name, new_type, int(new_age))
        except ValueError as e:
            st.error(str(e))
            return
        if st.session_state.get("pet_filter") == old_name:  # keep the schedule filter on this pet
            st.session_state.pet_filter = pet.name
        st.session_state.notice = f"Saved {pet.name}'s info."
        st.session_state.pop("pet_panel", None)
        st.rerun()


if owner.get_pets():
    st.write(f"{owner.name}'s pets:")
    pet_widths = [3, 2, 1, 1]
    table_header(pet_widths, ["Name", "Type", "Age", ""])
    for index, p in enumerate(owner.get_pets()):
        with st.container(border=True):
            name_col, type_col, age_col, edit_col = st.columns(pet_widths, vertical_alignment="center")
            name_col.write(p.name)
            type_col.write(p.pet_type.title())
            age_col.write(str(p.age))
            edit_col.button(
                "✏️", key=f"edit_pet_{index}", help="Edit pet", on_click=open_pet_panel, args=(index, p)
            )
            if st.session_state.get("pet_panel") == index:
                pet_edit_panel(index, p)
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
                "Status": "Done ✓" if t.is_complete() else "Pending",
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

pet_options = ["All pets"] + list(pets_by_name)
if st.session_state.get("pet_filter", "All pets") not in pet_options:
    st.session_state.pet_filter = "All pets"  # the filtered pet no longer exists under that name

filter_col1, filter_col2 = st.columns(2)
with filter_col1:
    pet_choice = st.selectbox("Show pet", pet_options, key="pet_filter")
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


def open_panel(kind: str, task: Task) -> None:
    """Button callback: open the edit or delete panel for one task (closing any other).

    For edit, the form fields are loaded from the task each time the panel opens, so
    they always start from the task's current values.
    """
    st.session_state.panel = (kind, task.id)
    if kind == "edit":
        starting_values = {
            "name": task.name, "category": task.category, "date": task.date,
            "start": task.start_time, "end": task.end_time, "priority": task.priority,
            "repeats": task.recurrence, "comment": task.comment,
            "scope": "This occurrence only",
        }
        for field, value in starting_values.items():
            st.session_state[f"edit_{field}_{task.id}"] = value


def close_panel() -> None:
    """Close the open edit or delete panel."""
    st.session_state.pop("panel", None)


def edit_panel(t: Task) -> None:
    """Show the edit form for a task, directly under its row."""
    recurring = t.recurrence != "none"
    with st.form(f"edit_form_{t.id}"):
        left, right = st.columns(2)
        name = left.text_input("Task title", key=f"edit_name_{t.id}")
        category = left.selectbox("Category", Task.CATEGORIES, key=f"edit_category_{t.id}")
        new_date = left.date_input("Date", key=f"edit_date_{t.id}")
        start = right.time_input("Start time", key=f"edit_start_{t.id}")
        end = right.time_input("End time", key=f"edit_end_{t.id}")
        priority = right.slider(
            "Priority (5 = most important)", Task.MIN_PRIORITY, Task.MAX_PRIORITY,
            key=f"edit_priority_{t.id}",
        )
        recurrence = st.selectbox("Repeats", Task.RECURRENCES, key=f"edit_repeats_{t.id}")
        comment = st.text_input("Note (optional)", key=f"edit_comment_{t.id}")
        scope = None
        if recurring:
            scope = st.radio(
                "Apply to",
                ["This occurrence only", "This and all future occurrences"],
                key=f"edit_scope_{t.id}",
            )
        save_col, cancel_col = st.columns(2)
        save = save_col.form_submit_button("Save")
        cancel = cancel_col.form_submit_button("Cancel")

    if cancel:
        close_panel()
        st.rerun()
    if save:
        updates = {
            "name": name, "category": category, "date": new_date, "start_time": start,
            "end_time": end, "priority": priority, "comment": comment, "recurrence": recurrence,
        }
        if start is None or end is None:
            st.error("Enter a start time and an end time.")
            return
        try:
            if scope == "This and all future occurrences":
                t.pet.edit_series(t, updates)
            elif recurring:
                t.pet.edit_occurrence(t, updates)
            else:
                t.pet.edit_task(t, updates)
        except ValueError as e:
            st.error(str(e))
            return
        st.session_state.notice = f"Saved '{t.name}'."
        st.session_state.edit_warnings = Scheduler(owner).warnings_for(t)
        close_panel()
        st.rerun()


def delete_panel(t: Task) -> None:
    """Show the delete confirmation for a task, directly under its row."""
    pet = t.pet
    with st.container(border=True):
        st.write(f"Delete '{t.name}' ({pet.name}) on {t.date.strftime('%a, %b %d')}?")
        if t.recurrence == "none":
            confirm_col, cancel_col = st.columns(2)
            if confirm_col.button("Delete", key=f"confirm_delete_{t.id}"):
                pet.remove_task(t)
                st.session_state.notice = f"Deleted '{t.name}'."
                close_panel()
                st.rerun()
        else:
            one_col, all_col, cancel_col = st.columns(3)
            if one_col.button("This occurrence only", key=f"delete_one_{t.id}"):
                follow_up = pet.skip_task(t)
                st.session_state.notice = (
                    f"Deleted '{t.name}' on {t.date.strftime('%b %d')}; "
                    f"next one is {follow_up.date.strftime('%b %d')}."
                )
                close_panel()
                st.rerun()
            if all_col.button("This and all future", key=f"delete_all_{t.id}"):
                removed = pet.remove_series(t)
                st.session_state.notice = f"Deleted '{t.name}' and {removed - 1} later occurrence(s)."
                close_panel()
                st.rerun()
        if cancel_col.button("Cancel", key=f"cancel_delete_{t.id}"):
            close_panel()
            st.rerun()


if "notice" in st.session_state:
    st.toast(st.session_state.pop("notice"))
for message in st.session_state.pop("edit_warnings", []):
    st.warning(message)

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
        widths = [1.4, 2.0, 2.0, 1.4, 1.3, 0.9, 0.8, 0.8]
        table_header(widths, ["Status", "Time", "Task", "Pet", "Category", "Priority", "", ""])
        open_kind, open_id = st.session_state.get("panel", (None, None))
        for t in plan:
            with st.container(border=True):
                (status_col, time_col, task_col, pet_col, category_col,
                 priority_col, edit_col, delete_col) = st.columns(widths, vertical_alignment="center")
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
                priority_col.write(str(t.priority))
                edit_col.button(
                    "✏️", key=f"edit_{t.id}", help="Edit task", on_click=open_panel, args=("edit", t)
                )
                delete_col.button(
                    "🗑️", key=f"delete_{t.id}", help="Delete task", on_click=open_panel, args=("delete", t)
                )
                if open_id == t.id:
                    if open_kind == "edit":
                        edit_panel(t)
                    elif open_kind == "delete":
                        delete_panel(t)
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
