"""
PawPal+ logic layer:
core classes for the app (PawPal), owners, pets, schedules, tasks, and scheduling.
"""

from dataclasses import dataclass, field
from datetime import date, time
from typing import ClassVar, List, Optional, Tuple
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
    completed: bool = False
    id: str = field(default_factory=lambda: uuid4().hex)
    pet: Optional["Pet"] = field(default=None, repr=False, compare=False)

    CATEGORIES: ClassVar[List[str]] = ["walk", "feeding", "meds", "enrichment", "grooming"]

    def get_duration(self) -> float:
        pass

    def occurs_on(self, date: date) -> bool:
        pass

    def mark_complete(self) -> None:
        pass


class Schedule:
    def __init__(self, pet: "Pet") -> None:
        self.pet: Pet = pet
        self.tasks: List[Task] = []

    def add_task(self, task: Task) -> None:
        pass

    def edit_task(self, task: Task, updates: dict) -> None:
        pass

    def remove_task(self, task: Task) -> None:
        pass

    def get_tasks(self) -> List[Task]:
        pass

    def filter_tasks(
        self,
        name: Optional[str] = None,
        category: Optional[str] = None,
        priority: Optional[int] = None,
        duration: Optional[float] = None,
        completed: Optional[bool] = None,
        date: Optional[date] = None,
    ) -> List[Task]:
        pass

    def daily_display(self, date: date) -> List[Task]:
        pass

    def weekly_display(self, start_date: date) -> List[Task]:
        pass

    def monthly_display(self, month: int, year: int) -> List[Task]:
        pass


@dataclass
class Pet:
    name: str
    pet_type: str
    age: int
    owner: "Owner" = field(repr=False, compare=False)
    schedule: Schedule = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        self.schedule = Schedule(self)

    def edit_info(self, name: str, pet_type: str, age: int) -> None:
        pass


class Owner:
    def __init__(
        self,
        name: str,
        daily_available_minutes: int = 480,
        preferences: Optional[List[str]] = None,
        _token: object = None,
    ) -> None:
        if _token is not _OWNER_TOKEN:
            raise TypeError("Owners must be created with PawPal.add_owner()")
        self.name: str = name
        self.pets: List[Pet] = []
        self.daily_available_minutes: int = daily_available_minutes
        self.preferences: List[str] = preferences if preferences is not None else []

    def add_pet(self, name: str, pet_type: str, age: int) -> Pet:
        pass

    def get_pet_names(self) -> List[Pet]:
        pass


class PawPal:
    def __init__(self) -> None:
        self.owners: List[Owner] = []

    def add_owner(self, name: str) -> Owner:
        pass

    def get_owners(self) -> List[Owner]:
        pass


class Scheduler:
    def __init__(self, owner: Owner) -> None:
        self.owner: Owner = owner

    def daily_plan(self, date: date) -> List[Task]:
        pass

    def sort_tasks(self, date: date, by: str) -> List[Task]:
        pass

    def find_conflicts(self, date: date) -> List[Tuple[Task, Task]]:
        pass

    def remaining_minutes(self, date: date) -> float:
        pass
