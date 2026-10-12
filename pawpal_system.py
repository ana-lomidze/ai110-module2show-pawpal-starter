"""
PawPal+ logic layer:
core classes for the app (PawPal), owners, pets, schedules, tasks, and scheduling.
"""

import calendar
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from typing import ClassVar, Dict, List, Optional, Set, Tuple
from uuid import uuid4

# Private token: Owners may only be created through PawPal.add_owner()
_OWNER_TOKEN = object()


@dataclass
class Task:
    name: str
    category: str
    date: date
    start_time: time
    end_time: time
    priority: int
    comment: str = ""
    recurrence: str = "none"
    completed_dates: Set[date] = field(default_factory=set)
    id: str = field(default_factory=lambda: uuid4().hex)
    series_id: str = field(default_factory=lambda: uuid4().hex)  # shared by a task and its follow-ups
    pet: Optional["Pet"] = field(default=None, repr=False, compare=False)

    CATEGORIES: ClassVar[List[str]] = ["walk", "feeding", "meds", "enrichment", "grooming"]
    RECURRENCES: ClassVar[List[str]] = ["none", "daily", "weekly", "monthly"]
    RECURRENCE_DAYS: ClassVar[Dict[str, int]] = {"daily": 1, "weekly": 7, "monthly": 30}
    MIN_PRIORITY: ClassVar[int] = 1
    MAX_PRIORITY: ClassVar[int] = 5

    def __post_init__(self) -> None:
        """Validate the task as soon as it is created."""
        self.validate()

    def validate(self) -> None:
        """Raise ValueError if any task field holds an invalid value."""
        if not self.name.strip():
            raise ValueError("Task name cannot be empty")
        if self.category not in self.CATEGORIES:
            raise ValueError(f"Category must be one of {self.CATEGORIES}")
        if self.recurrence not in self.RECURRENCES:
            raise ValueError(f"Recurrence must be one of {self.RECURRENCES}")
        if not self.MIN_PRIORITY <= self.priority <= self.MAX_PRIORITY:
            raise ValueError(
                f"Priority must be between {self.MIN_PRIORITY} and {self.MAX_PRIORITY}"
            )
        if self.end_time <= self.start_time:
            raise ValueError("End time must be after start time")

    def get_duration(self) -> float:
        """Return the task's length in minutes."""
        start = datetime.combine(self.date, self.start_time)
        end = datetime.combine(self.date, self.end_time)
        return (end - start).total_seconds() / 60

    def occurs_on(self, date: date) -> bool:
        """Return True if the task falls on the given date (each instance has one date)."""
        return date == self.date

    def next_date(self) -> Optional[date]:
        """Return the date of the next occurrence, or None if the task doesn't repeat."""
        days = self.RECURRENCE_DAYS.get(self.recurrence)
        return self.date + timedelta(days=days) if days else None

    def is_complete(self, on: Optional[date] = None) -> bool:
        """Return True if the task has been completed on the given date (default: its own date)."""
        return (on or self.date) in self.completed_dates

    def mark_complete(self, on: Optional[date] = None) -> Optional["Task"]:
        """Mark the task complete for the given date (default: its own date).

        If the task repeats and belongs to a pet, the next occurrence is added to that
        pet's schedule and returned. Returns None when nothing new is created.
        """
        on = on or self.date
        if not self.occurs_on(on):
            raise ValueError(f"Task does not occur on {on}")
        self.completed_dates.add(on)
        return self.spawn_next()

    def spawn_next(self) -> Optional["Task"]:
        """Add the next occurrence to this task's pet and return it.

        Returns None if the task doesn't repeat, has no pet, or the next occurrence
        already exists (so completing or editing twice never creates duplicates).
        """
        next_date = self.next_date()
        if next_date is None or self.pet is None:
            return None
        already_exists = any(
            t.series_id == self.series_id and t.date == next_date
            for t in self.pet.schedule.tasks
        )
        if already_exists:
            return None
        follow_up = Task(
            self.name, self.category, next_date, self.start_time,
            self.end_time, self.priority, self.comment, self.recurrence,
            series_id=self.series_id,
        )
        self.pet.add_task(follow_up)
        return follow_up


class Schedule:
    EDITABLE_FIELDS = {
        "name", "category", "date", "start_time", "end_time",
        "priority", "comment", "recurrence",
    }
    RESET_COMPLETION_FIELDS = {"date", "start_time", "end_time"}

    def __init__(self, pet: "Pet") -> None:
        """Create an empty schedule for the given pet."""
        self.pet: Pet = pet
        self.tasks: List[Task] = []

    def get_task(self, task: Task) -> Task:
        """Return the stored task matching the given task's id, or raise ValueError."""
        for t in self.tasks:
            if t.id == task.id:
                return t
        raise ValueError("Task not found in this schedule")

    def add_task(self, task: Task) -> None:
        """Add a task to the schedule and link it to this schedule's pet."""
        if any(t.id == task.id for t in self.tasks):
            raise ValueError("Task is already in this schedule")
        task.pet = self.pet
        self.tasks.append(task)

    def edit_task(self, task: Task, updates: dict) -> None:
        """Apply field updates to one task, rolling back if the result is invalid.

        Changing a task's date or times makes it pending again.
        """
        stored = self.get_task(task)
        unknown = set(updates) - self.EDITABLE_FIELDS
        if unknown:
            raise ValueError(f"Cannot edit field(s): {', '.join(sorted(unknown))}")
        original = {k: getattr(stored, k) for k in updates}
        for key, value in updates.items():
            setattr(stored, key, value)
        try:
            stored.validate()
        except ValueError:
            for key, value in original.items():
                setattr(stored, key, value)
            raise
        if any(updates[k] != original[k] for k in self.RESET_COMPLETION_FIELDS & set(updates)):
            stored.completed_dates.clear()

    def edit_occurrence(self, task: Task, updates: dict) -> None:
        """Edit only this occurrence; the next occurrence is created from the unedited task."""
        stored = self.get_task(task)
        follow_up = stored.spawn_next()
        try:
            self.edit_task(stored, updates)
        except ValueError:
            if follow_up is not None:
                self.remove_task(follow_up)
            raise

    def _later_in_series(self, task: Task) -> List[Task]:
        """Return the task's later occurrences (same series, later date), in date order."""
        return sorted(
            (t for t in self.tasks if t.series_id == task.series_id and t.date > task.date),
            key=lambda t: t.date,
        )

    def edit_series(self, task: Task, updates: dict) -> None:
        """Edit this task and its later occurrences; the date only changes this occurrence."""
        stored = self.get_task(task)
        later = self._later_in_series(stored)
        self.edit_task(stored, updates)
        shared = {k: v for k, v in updates.items() if k != "date"}
        for t in later:
            self.edit_task(t, shared)

    def complete_task(self, task: Task, on: Optional[date] = None) -> Optional[Task]:
        """Mark a task complete and, if it repeats, add the next occurrence; return the new task."""
        return self.get_task(task).mark_complete(on)

    def remove_task(self, task: Task) -> None:
        """Remove a task from the schedule and unlink it from the pet."""
        stored = self.get_task(task)
        self.tasks.remove(stored)
        stored.pet = None

    def skip_task(self, task: Task) -> Optional[Task]:
        """Remove this occurrence but keep the series going; return the next occurrence.

        The next occurrence is created if needed; None only if the task doesn't repeat.
        """
        stored = self.get_task(task)
        next_date = stored.next_date()
        stored.spawn_next()
        follow_up = next(
            (t for t in self.tasks if t.series_id == stored.series_id and t.date == next_date),
            None,
        )
        self.remove_task(stored)
        return follow_up

    def remove_series(self, task: Task) -> int:
        """Remove this occurrence and all its later occurrences; return how many were removed."""
        stored = self.get_task(task)
        doomed = [stored] + self._later_in_series(stored)
        for t in doomed:
            self.remove_task(t)
        return len(doomed)

    def get_tasks(self) -> List[Task]:
        """Return a copy of all tasks, sorted by date then start time."""
        return sorted(self.tasks, key=lambda t: (t.date, t.start_time))

    def filter_tasks(
        self,
        name: Optional[str] = None,
        category: Optional[str] = None,
        priority: Optional[int] = None,
        duration: Optional[float] = None,
        completed: Optional[bool] = None,
        date: Optional[date] = None,
    ) -> List[Task]:
        """Return tasks matching every filter given (duration is a maximum in minutes)."""
        results: List[Task] = []
        for t in self.get_tasks():
            if name is not None and name.lower() not in t.name.lower():
                continue
            if category is not None and t.category != category:
                continue
            if priority is not None and t.priority != priority:
                continue
            if duration is not None and t.get_duration() > duration:
                continue
            if completed is not None and t.is_complete(date) != completed:
                continue
            if date is not None and not t.occurs_on(date):
                continue
            results.append(t)
        return results

    def daily_display(self, date: date) -> List[Task]:
        """Return the tasks occurring on the given date, sorted by start time."""
        return sorted(
            (t for t in self.tasks if t.occurs_on(date)),
            key=lambda t: t.start_time,
        )

    def weekly_display(self, start_date: date) -> Dict[date, List[Task]]:
        """Return a day-to-tasks mapping for the seven days starting at start_date."""
        days = [start_date + timedelta(days=i) for i in range(7)]
        return {day: self.daily_display(day) for day in days}

    def monthly_display(self, month: int, year: int) -> Dict[date, List[Task]]:
        """Return a day-to-tasks mapping for every day of the given month."""
        if not 1 <= month <= 12:
            raise ValueError("Month must be between 1 and 12")
        days_in_month = calendar.monthrange(year, month)[1]
        days = [date(year, month, d) for d in range(1, days_in_month + 1)]
        return {day: self.daily_display(day) for day in days}


@dataclass
class Pet:
    name: str
    pet_type: str
    age: int
    owner: "Owner" = field(repr=False, compare=False)
    schedule: Schedule = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        """Give the pet its own empty schedule."""
        self.schedule = Schedule(self)

    def edit_info(self, name: str, pet_type: str, age: int) -> None:
        """Update the pet's name, type and age after validating them."""
        name = name.strip()
        if not name:
            raise ValueError("Pet name cannot be empty")
        if age < 0:
            raise ValueError("Pet age cannot be negative")
        if any(p is not self and p.name.lower() == name.lower() for p in self.owner.pets):
            raise ValueError(f"Pet '{name}' already exists for {self.owner.name}")
        self.name = name
        self.pet_type = pet_type
        self.age = age

    def add_task(self, task: Task) -> None:
        """Add a task to this pet's schedule."""
        self.schedule.add_task(task)

    def edit_task(self, task: Task, updates: dict) -> None:
        """Edit a task in this pet's schedule."""
        self.schedule.edit_task(task, updates)

    def complete_task(self, task: Task, on: Optional[date] = None) -> Optional[Task]:
        """Complete a task in this pet's schedule, returning the next occurrence if it repeats."""
        return self.schedule.complete_task(task, on)

    def edit_occurrence(self, task: Task, updates: dict) -> None:
        """Edit only this occurrence of a task in this pet's schedule."""
        self.schedule.edit_occurrence(task, updates)

    def edit_series(self, task: Task, updates: dict) -> None:
        """Edit a task and its later occurrences in this pet's schedule."""
        self.schedule.edit_series(task, updates)

    def remove_task(self, task: Task) -> None:
        """Remove a task from this pet's schedule."""
        self.schedule.remove_task(task)

    def skip_task(self, task: Task) -> Optional[Task]:
        """Remove one occurrence and keep the series going; return the next occurrence."""
        return self.schedule.skip_task(task)

    def remove_series(self, task: Task) -> int:
        """Remove a task and its later occurrences; return how many were removed."""
        return self.schedule.remove_series(task)

    def get_tasks(self) -> List[Task]:
        """Return this pet's tasks, sorted by date then start time."""
        return self.schedule.get_tasks()


class Owner:
    def __init__(
        self,
        name: str,
        daily_available_minutes: int = 480,
        preferences: Optional[List[str]] = None,
        _token: object = None,
    ) -> None:
        """Create an owner; only allowed through PawPal.add_owner()."""
        if _token is not _OWNER_TOKEN:
            raise TypeError("Owners must be created with PawPal.add_owner()")
        self.name: str = name
        self.pets: List[Pet] = []
        self.daily_available_minutes: int = daily_available_minutes
        self.preferences: List[str] = preferences if preferences is not None else []

    def add_pet(self, name: str, pet_type: str, age: int) -> Pet:
        """Create a pet for this owner after validating its details, and return it."""
        name = name.strip()
        if not name:
            raise ValueError("Pet name cannot be empty")
        if age < 0:
            raise ValueError("Pet age cannot be negative")
        if any(p.name.lower() == name.lower() for p in self.pets):
            raise ValueError(f"Pet '{name}' already exists for {self.name}")
        pet = Pet(name, pet_type, age, owner=self)
        self.pets.append(pet)
        return pet

    def get_pets(self) -> List[Pet]:
        """Return a copy of the owner's list of pets."""
        return list(self.pets)

    def get_all_tasks(self) -> List[Task]:
        """Return every task from all of the owner's pets."""
        tasks: List[Task] = []
        for pet in self.pets:
            tasks.extend(pet.get_tasks())
        return tasks


class PawPal:
    def __init__(self) -> None:
        """Create an app registry with no owners."""
        self.owners: List[Owner] = []

    def add_owner(self, name: str) -> Owner:
        """Create and register a new owner with a unique, non-empty name."""
        name = name.strip()
        if not name:
            raise ValueError("Owner name cannot be empty")
        if any(o.name.lower() == name.lower() for o in self.owners):
            raise ValueError(f"Owner '{name}' already exists")
        owner = Owner(name, _token=_OWNER_TOKEN)
        self.owners.append(owner)
        return owner

    def get_owners(self) -> List[Owner]:
        """Return a copy of the list of registered owners."""
        return list(self.owners)


class Scheduler:
    def __init__(self, owner: Owner) -> None:
        """Create a scheduler that plans tasks across all of the given owner's pets."""
        self.owner: Owner = owner

    @staticmethod
    def _overlaps(a: Task, b: Task) -> bool:
        """Return True if two tasks' time ranges overlap (back-to-back is not an overlap)."""
        return a.start_time < b.end_time and b.start_time < a.end_time

    def _tasks_on(self, date: date) -> List[Task]:
        """Return all of the owner's tasks, across every pet, that occur on the date."""
        return [t for t in self.owner.get_all_tasks() if t.occurs_on(date)]

    def daily_plan(self, date: date) -> List[Task]:
        """Return the whole day's tasks across all pets, in time order."""
        return self.sort_tasks(date, "time")

    def sort_tasks(self, date: date, by: str) -> List[Task]:
        """Return the day's tasks sorted by "time", "priority" (highest first) or "duration"."""
        keys = {
            "time": lambda t: t.start_time,
            "priority": lambda t: (-t.priority, t.start_time),
            "duration": lambda t: (t.get_duration(), t.start_time),
        }
        if by not in keys:
            raise ValueError(f"Sort by must be one of {list(keys)}")
        return sorted(self._tasks_on(date), key=keys[by])

    def filter_tasks(
        self,
        date: date,
        pet_name: Optional[str] = None,
        status: Optional[str] = None,
        category: Optional[str] = None,
    ) -> List[Task]:
        """Return the day's tasks in time order, filtered by pet name, status and category.

        status is "done", "pending" or None; completion is checked for this date only.
        """
        if status not in (None, "done", "pending"):
            raise ValueError("Status must be 'done', 'pending' or None")
        results: List[Task] = []
        for t in self.sort_tasks(date, "time"):
            if pet_name is not None and t.pet.name != pet_name:
                continue
            if category is not None and t.category != category:
                continue
            if status is not None and t.is_complete(date) != (status == "done"):
                continue
            results.append(t)
        return results

    def find_conflicts(self, date: date) -> List[Tuple[Task, Task]]:
        """Return every pair of overlapping tasks on the date, across all pets.

        One pass over the tasks in start order: each task is only compared with the
        earlier tasks that are still running when it starts.
        """
        pairs: List[Tuple[Task, Task]] = []
        running: List[Task] = []
        for task in self.sort_tasks(date, "time"):
            running = [t for t in running if t.end_time > task.start_time]
            pairs.extend((t, task) for t in running)
            running.append(task)
        return pairs

    @staticmethod
    def is_shared_time(a: Task, b: Task) -> bool:
        """Return True if two overlapping tasks can be done together (same category, different pets)."""
        return a.pet is not b.pet and a.category == b.category

    @staticmethod
    def describe_conflict(a: Task, b: Task) -> str:
        """Return a warning message for two overlapping tasks (a "Conflict" or a softer "Heads-up")."""
        start = max(a.start_time, b.start_time)
        end = min(a.end_time, b.end_time)
        when = f"{start:%I:%M %p} - {end:%I:%M %p}"
        pet_a = a.pet.name if a.pet else "no pet"
        pet_b = b.pet.name if b.pet else "no pet"
        if a.pet is b.pet:
            return f"Conflict: '{a.name}' and '{b.name}' for {pet_a} overlap ({when})."
        if Scheduler.is_shared_time(a, b):
            return (
                f"Heads-up: '{a.name}' ({pet_a}) and '{b.name}' ({pet_b}) overlap ({when}). "
                "Fine if you do them together."
            )
        return (
            f"Conflict: '{a.name}' ({pet_a}) and '{b.name}' ({pet_b}) overlap ({when}). "
            "You can't do both at once."
        )

    def conflict_warnings(self, date: date) -> List[str]:
        """Return a warning message for every overlap on the date (empty list if none)."""
        return [self.describe_conflict(a, b) for a, b in self.find_conflicts(date)]

    def warnings_for(self, task: Task) -> List[str]:
        """Return warning messages for the other tasks on the same date that overlap this task."""
        return [
            self.describe_conflict(other, task)
            for other in self._tasks_on(task.date)
            if other.id != task.id and self._overlaps(other, task)
        ]

    @staticmethod
    def _busy_minutes(tasks: List[Task]) -> float:
        """Return total minutes covered by the tasks, counting overlapping time once."""
        busy = 0.0
        block_end = None  # end of the merged block we're currently extending
        for t in sorted(tasks, key=lambda t: t.start_time):
            if block_end is None or t.start_time >= block_end:  # starts a new block
                busy += t.get_duration()
                block_end = t.end_time
            elif t.end_time > block_end:  # extends the current block
                gap = datetime.combine(t.date, t.end_time) - datetime.combine(t.date, block_end)
                busy += gap.total_seconds() / 60
                block_end = t.end_time
            # otherwise fully inside the current block: adds nothing
        return busy

    def remaining_minutes(self, date: date) -> float:
        """Return available minutes minus scheduled minutes (overlaps counted once; negative if overbooked)."""
        return self.owner.daily_available_minutes - self._busy_minutes(self._tasks_on(date))
