from datetime import date, time, timedelta

import pytest

from pawpal_system import PawPal, Scheduler, Task


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


def make_two_pet_scheduler():
    """Two pets on 2026-10-11: Donut has Breakfast (done) and Vet; Mongo has Breakfast and Walk."""
    owner = PawPal().add_owner("Ana")
    donut = owner.add_pet("Princess Donut", "Cat", 3)
    mongo = owner.add_pet("Mongo", "Dog", 1)
    donut_breakfast = make_task(name="Breakfast")
    donut.add_task(donut_breakfast)
    donut.add_task(make_task(name="Vet Visit", category="meds", start_time=time(14, 0), end_time=time(15, 0)))
    mongo.add_task(make_task(name="Breakfast"))
    mongo.add_task(make_task(name="Walk", category="walk", start_time=time(10, 0), end_time=time(11, 0)))
    donut_breakfast.mark_complete()
    return Scheduler(owner)


def names(tasks):
    return [(t.pet.name, t.name) for t in tasks]


DAY = date(2026, 10, 11)


def test_filter_without_filters_returns_whole_day_in_time_order():
    tasks = make_two_pet_scheduler().filter_tasks(DAY)

    assert names(tasks) == [
        ("Princess Donut", "Breakfast"),
        ("Mongo", "Breakfast"),
        ("Mongo", "Walk"),
        ("Princess Donut", "Vet Visit"),
    ]


def test_filter_by_pet():
    tasks = make_two_pet_scheduler().filter_tasks(DAY, pet_name="Mongo")

    assert names(tasks) == [("Mongo", "Breakfast"), ("Mongo", "Walk")]


def test_filter_by_status():
    scheduler = make_two_pet_scheduler()

    assert names(scheduler.filter_tasks(DAY, status="done")) == [("Princess Donut", "Breakfast")]
    assert len(scheduler.filter_tasks(DAY, status="pending")) == 3


def test_filter_by_pet_and_status():
    tasks = make_two_pet_scheduler().filter_tasks(DAY, pet_name="Princess Donut", status="pending")

    assert names(tasks) == [("Princess Donut", "Vet Visit")]


def test_filter_by_category():
    tasks = make_two_pet_scheduler().filter_tasks(DAY, category="feeding")

    assert names(tasks) == [("Princess Donut", "Breakfast"), ("Mongo", "Breakfast")]


def test_filter_unknown_pet_returns_empty_list():
    assert make_two_pet_scheduler().filter_tasks(DAY, pet_name="Nobody") == []


def test_filter_rejects_invalid_status():
    with pytest.raises(ValueError):
        make_two_pet_scheduler().filter_tasks(DAY, status="finished")


def test_filter_status_is_per_date():
    pet = make_pet()
    task = make_task(recurrence="daily")
    pet.add_task(task)
    follow_up = task.mark_complete()
    scheduler = Scheduler(pet.owner)

    assert scheduler.filter_tasks(DAY, status="done") == [task]
    assert scheduler.filter_tasks(follow_up.date, status="pending") == [follow_up]
    assert scheduler.filter_tasks(follow_up.date, status="done") == []


def make_conflict_setup():
    owner = PawPal().add_owner("Ana")
    donut = owner.add_pet("Princess Donut", "Cat", 3)
    mongo = owner.add_pet("Mongo", "Dog", 1)
    return Scheduler(owner), donut, mongo


def test_no_overlap_means_no_warnings():
    scheduler, donut, mongo = make_conflict_setup()
    donut.add_task(make_task(start_time=time(9, 0), end_time=time(9, 30)))
    mongo.add_task(make_task(start_time=time(9, 30), end_time=time(10, 0)))  # back-to-back

    assert scheduler.find_conflicts(DAY) == []
    assert scheduler.conflict_warnings(DAY) == []


def test_no_tasks_means_no_warnings():
    scheduler, _, _ = make_conflict_setup()

    assert scheduler.conflict_warnings(DAY) == []


def test_same_pet_overlap_is_a_conflict():
    scheduler, donut, _ = make_conflict_setup()
    donut.add_task(make_task(name="Walk", category="walk", start_time=time(10, 0), end_time=time(11, 0)))
    donut.add_task(make_task(name="Groom", category="grooming", start_time=time(10, 30), end_time=time(11, 30)))

    (message,) = scheduler.conflict_warnings(DAY)

    assert message.startswith("Conflict:")
    assert "'Walk' and 'Groom' for Princess Donut" in message
    assert "10:30 AM - 11:00 AM" in message


def test_different_pets_different_categories_is_a_conflict():
    scheduler, donut, mongo = make_conflict_setup()
    donut.add_task(make_task(name="Breakfast", category="feeding"))
    mongo.add_task(make_task(name="Walk", category="walk", start_time=time(9, 15), end_time=time(10, 0)))

    (message,) = scheduler.conflict_warnings(DAY)

    assert message.startswith("Conflict:")
    assert "can't do both" in message


def test_different_pets_same_category_is_a_heads_up():
    scheduler, donut, mongo = make_conflict_setup()
    donut.add_task(make_task(name="Breakfast"))
    mongo.add_task(make_task(name="Breakfast"))

    pairs = scheduler.find_conflicts(DAY)
    (message,) = scheduler.conflict_warnings(DAY)

    assert len(pairs) == 1
    assert Scheduler.is_shared_time(*pairs[0]) is True
    assert message.startswith("Heads-up:")


def test_same_pet_same_category_is_still_a_conflict():
    scheduler, donut, _ = make_conflict_setup()
    donut.add_task(make_task(name="Walk A", category="walk"))
    donut.add_task(make_task(name="Walk B", category="walk"))

    (message,) = scheduler.conflict_warnings(DAY)

    assert message.startswith("Conflict:")


def test_find_conflicts_pairs_every_overlap():
    scheduler, donut, mongo = make_conflict_setup()
    donut.add_task(make_task(name="Long", category="walk", start_time=time(9, 0), end_time=time(12, 0)))
    mongo.add_task(make_task(name="A", category="meds", start_time=time(9, 30), end_time=time(10, 0)))
    mongo.add_task(make_task(name="B", category="enrichment", start_time=time(11, 0), end_time=time(11, 30)))
    mongo.add_task(make_task(name="C", category="grooming", start_time=time(13, 0), end_time=time(14, 0)))

    pairs = {(a.name, b.name) for a, b in scheduler.find_conflicts(DAY)}

    assert pairs == {("Long", "A"), ("Long", "B")}


def test_warnings_for_new_task_lists_only_its_overlaps():
    scheduler, donut, mongo = make_conflict_setup()
    mongo.add_task(make_task(name="Walk", category="walk", start_time=time(10, 0), end_time=time(11, 0)))
    mongo.add_task(make_task(name="Dinner", start_time=time(18, 0), end_time=time(18, 30)))
    new_task = make_task(name="Groom", category="grooming", start_time=time(10, 30), end_time=time(11, 30))
    donut.add_task(new_task)

    (message,) = scheduler.warnings_for(new_task)

    assert "'Walk' (Mongo)" in message and "'Groom' (Princess Donut)" in message


def test_warnings_for_task_without_overlap_is_empty_and_does_not_raise():
    scheduler, donut, _ = make_conflict_setup()
    task = make_task()
    donut.add_task(task)

    assert scheduler.warnings_for(task) == []


def test_adding_task_increases_pet_task_count():
    pet = make_pet()
    assert len(pet.get_tasks()) == 0

    pet.add_task(make_task())

    assert len(pet.get_tasks()) == 1
