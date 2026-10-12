# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## Implementation Summary

PawPal+'s logic lives in `pawpal_system.py` as six classes. Data flows down the chain
`PawPal → Owner → Pet → Schedule → Task`, and a separate `Scheduler` reads across it.

| Class | Role |
|-------|------|
| `PawPal` | Top-level registry of owners. It is the only way to create an `Owner`, and it rejects blank or duplicate names. |
| `Owner` | Holds the owner's pets, daily available minutes and preferences. `get_all_tasks()` collects the tasks of every pet, so the rest of the app never reads a single pet directly. |
| `Pet` | Stores pet details and owns one `Schedule`. Its task methods pass calls through to that schedule. |
| `Schedule` | One pet's list of tasks. It adds, edits, removes and filters tasks, and builds daily, weekly and monthly views. |
| `Task` | One activity: name, category, date, start and end time, priority (1-5), recurrence and per-date completion. It validates itself on creation and on every edit. |
| `Scheduler` | The "brain". It plans across all of an owner's pets: it sorts the day's tasks, detects overlapping tasks and computes remaining time. |

**How they work together**

1. You create an owner through `PawPal.add_owner()` and pets through `Owner.add_pet()`.
2. Tasks are added with `Pet.add_task()`, which hands them to the pet's `Schedule`. The schedule links each task back to its pet.
3. `Scheduler` takes an `Owner`, calls `Owner.get_all_tasks()` to pull every pet's tasks together, and keeps only those that occur on the requested date.
4. From that combined list it produces the daily plan in time order, sorts by time, priority or duration, finds conflicts, and returns remaining minutes. Conflicts are found across pets, because one person cannot do two things at once.

**Key design decisions**

- **Per-date completion:** a task stores the set of dates it was completed on, so finishing a recurring task today does not mark every future day done.
- **Recurrence:** tasks can repeat `daily`, `weekly` or `monthly`, and `occurs_on(date)` decides whether a task falls on a given day.
- **Validation:** bad input, such as a blank name, an out-of-range priority or an end time before the start, raises a `ValueError`. Editing a task rolls back if the new values are invalid.
- **Overbooking:** `remaining_minutes` can go negative, which shows by how much a day is overbooked.



## 🖥️ Sample Output

### CLI (`python main.py`)
```
Today's Schedule for Ana - Sunday, October 11, 2026
------------------------------------------------------------
[ ] Not done 09:00 AM - 09:30 AM  Breakfast       (Princess Donut, feeding, priority 5)
[ ] Not done 09:00 AM - 09:30 AM  Breakfast       (Mongo, feeding, priority 5)
[ ] Not done 10:00 AM - 11:00 AM  Morning Walk    (Mongo, walk, priority 4)
[ ] Not done 02:00 PM - 04:00 PM  Vet Visit       (Princess Donut, meds, priority 5)
             note: Donut needs to get her vaccinations
------------------------------------------------------------
Minutes remaining: 240

WARNING: 'Breakfast' (Princess Donut) overlaps 'Breakfast' (Mongo)
```

Paste a sample of your app's CLI or Streamlit output here so a reader can see what a generated plan looks like:

```
# e.g.:
# Daily plan for Biscuit (Golden Retriever):
#   08:00 — Morning walk (30 min) [priority: high]
#   09:00 — Feeding (10 min) [priority: high]
#   ...
```

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
# Paste your pytest output here
```

## 📐 Smarter Scheduling

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_tasks`, `Scheduler.daily_plan` | by `"time"`, `"priority"` (highest first) or `"duration"` (shortest first); the daily plan is in time order across all pets |
| Filtering | `Scheduler.filter_tasks` | one day's tasks across all pets, by pet name, status (`"done"` or `"pending"` for that date), category and length (`longer_than` / `at_most` minutes). The app offers pet, status and length dropdowns. `Schedule.filter_tasks` still filters a single pet's tasks by name, category, priority, max duration, completion and date |
| Conflict handling | `Scheduler.find_conflicts`, `Scheduler.conflict_warnings`, `Scheduler.warnings_for` | finds overlapping tasks in one pass over the day (back-to-back is not an overlap) and returns warning messages instead of raising. Same pet, or different pets with different categories: `Conflict`. Different pets, same category: a softer `Heads-up`, since both can be done together (`Scheduler.is_shared_time`). `warnings_for` checks a single task, e.g. right after it is added or edited |
| Recurring tasks | `Task.next_date`, `Task.mark_complete`, `Task.spawn_next`, `Schedule.complete_task` | `daily` (+1 day), `weekly` (+7 days) or `monthly` (every 30 days). Each task is one dated occurrence; completing it creates the next one automatically, and never creates it twice. Completion is per date |
| Editing and deleting | `Schedule.edit_task`, `edit_occurrence`, `edit_series`, `skip_task`, `remove_series` | recurring tasks can be changed or deleted for **this occurrence only** or **this and all future occurrences** (occurrences are linked by a `series_id`). Changing a completed task's date or times makes it pending again |
| Time left in the day | `Scheduler.remaining_minutes` | available minutes minus scheduled minutes, with overlapping time counted once, so two pets fed together use 30 minutes, not 60. Negative means overbooked |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
