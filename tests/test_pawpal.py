from datetime import date, time

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


def test_adding_task_increases_pet_task_count():
    pet = make_pet()
    assert len(pet.get_tasks()) == 0

    pet.add_task(make_task())

    assert len(pet.get_tasks()) == 1
