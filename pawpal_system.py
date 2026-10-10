"""
PawPal+ logic layer: 
core classes for owners, pets, tasks, and scheduling.
"""

from dataclasses import dataclass, field
from datetime import date, time
from typing import ClassVar, List, Optional


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

    CATEGORIES: ClassVar[List[str]] = ["walk", "feeding", "meds", "enrichment", "grooming"]

    @classmethod
    def add_category(cls, name: str) -> None:
        pass

    def get_duration(self) -> float:
        pass

    def occurs_on(self, date: date) -> bool:
        pass

    def mark_complete(self) -> None:
        pass


class Schedule:
    def __init__(self) -> None:
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

    def daily_display(self, date: date) -> None:
        pass

    def weekly_display(self, start_date: date) -> None:
        pass

    def monthly_display(self, month: int, year: int) -> None:
        pass


@dataclass
class Pet:
    name: str
    pet_type: str
    age: int
    schedule: Schedule = field(default_factory=Schedule)

    def edit_info(self, name: str, pet_type: str, age: int) -> None:
        pass


class Owner:
    def __init__(self, name: str) -> None:
        self.name: str = name
        self.pets: List[Pet] = []

    def add_pet(self, name: str, pet_type: str, age: int) -> Pet:
        pass

    def get_pet_names(self) -> List[Pet]:
        pass


class Scheduler:
    def __init__(self, schedule: Schedule) -> None:
        self.schedule: Schedule = schedule

    def daily_plan(self, date: date) -> List[Task]:
        pass

    def sort_tasks(self, by: str) -> List[Task]:
        pass

    def find_conflicts(self) -> List[Task]:
        pass
