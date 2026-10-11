from datetime import date, time, timedelta

from pawpal_system import PawPal, Task


def make_task(**overrides):
    fields = dict(
        name="Breakfast",
        category="feeding",
        date=date(2026, 10, 11),
        start_time=time(9, 0),
        end_time=time(9, 30),
        priority=5,
    )
    fields.update(overrides)
    return Task(**fields)


def make_pet():
    owner = PawPal().add_owner("Ana")
    return owner.add_pet("Princess Donut", "Cat", 3)


def test_mark_complete_changes_task_status():
    task = make_task()
    assert task.is_complete() is False

    task.mark_complete()

    assert task.is_complete() is True


def test_next_date_uses_recurrence_interval():
    start = date(2026, 10, 11)
    assert make_task(recurrence="daily").next_date() == start + timedelta(days=1)
    assert make_task(recurrence="weekly").next_date() == start + timedelta(days=7)
    assert make_task(recurrence="monthly").next_date() == start + timedelta(days=30)
    assert make_task(recurrence="none").next_date() is None


def test_task_occurs_only_on_its_own_date():
    task = make_task(recurrence="daily")
    assert task.occurs_on(date(2026, 10, 11)) is True
    assert task.occurs_on(date(2026, 10, 12)) is False
    assert task.occurs_on(date(2026, 10, 10)) is False


def test_completing_recurring_task_creates_next_occurrence():
    pet = make_pet()
    task = make_task(recurrence="weekly", comment="walk the block")
    pet.add_task(task)

    follow_up = pet.complete_task(task)

    assert task.is_complete() is True
    assert follow_up is not None
    assert follow_up.date == date(2026, 10, 18)
    assert follow_up.id != task.id
    assert follow_up.is_complete() is False
    assert (follow_up.name, follow_up.start_time, follow_up.recurrence, follow_up.comment) == (
        task.name, task.start_time, task.recurrence, task.comment
    )
    assert follow_up.pet is pet
    assert len(pet.get_tasks()) == 2


def test_mark_complete_directly_creates_next_occurrence():
    pet = make_pet()
    task = make_task(recurrence="daily")
    pet.add_task(task)

    follow_up = task.mark_complete()

    assert follow_up is not None
    assert follow_up.date == date(2026, 10, 12)
    assert len(pet.get_tasks()) == 2
    assert task.mark_complete() is None  # no duplicate
    assert len(pet.get_tasks()) == 2


def test_mark_complete_on_task_without_pet_creates_nothing():
    task = make_task(recurrence="daily")

    assert task.mark_complete() is None
    assert task.is_complete() is True


def test_completing_non_recurring_task_creates_nothing():
    pet = make_pet()
    task = make_task()
    pet.add_task(task)

    assert pet.complete_task(task) is None
    assert len(pet.get_tasks()) == 1


def test_completing_twice_does_not_duplicate_next_occurrence():
    pet = make_pet()
    task = make_task(recurrence="daily")
    pet.add_task(task)

    pet.complete_task(task)
    assert pet.complete_task(task) is None
    assert len(pet.get_tasks()) == 2


def test_adding_task_increases_pet_task_count():
    pet = make_pet()
    assert len(pet.get_tasks()) == 0

    pet.add_task(make_task())

    assert len(pet.get_tasks()) == 1
