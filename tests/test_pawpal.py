from datetime import date, datetime, time, timedelta

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


def make_duration_scheduler():
    """One pet with tasks of 15, 30, 45, 60 and 90 minutes on 2026-10-11."""
    owner = PawPal().add_owner("Ana")
    pet = owner.add_pet("Mongo", "dog", 1)
    for name, minutes in [("A", 15), ("B", 30), ("C", 45), ("D", 60), ("E", 90)]:
        start = datetime.combine(DAY, time(8, 0))
        pet.add_task(make_task(
            name=name, start_time=start.time(), end_time=(start + timedelta(minutes=minutes)).time()
        ))
    return Scheduler(owner)


def test_filter_by_duration_buckets_use_the_documented_boundaries():
    scheduler = make_duration_scheduler()

    short = scheduler.filter_tasks(DAY, at_most=30)
    medium = scheduler.filter_tasks(DAY, longer_than=30, at_most=60)
    long_ = scheduler.filter_tasks(DAY, longer_than=60)

    assert sorted(t.name for t in short) == ["A", "B"]  # 30 counts as short
    assert sorted(t.name for t in medium) == ["C", "D"]  # 60 counts as medium
    assert [t.name for t in long_] == ["E"]


def test_filter_by_duration_without_bounds_returns_everything():
    assert len(make_duration_scheduler().filter_tasks(DAY)) == 5


def test_filter_by_duration_with_impossible_range_returns_empty_list():
    assert make_duration_scheduler().filter_tasks(DAY, longer_than=60, at_most=30) == []


def test_filter_by_duration_combines_with_other_filters():
    scheduler = make_two_pet_scheduler()  # Breakfasts are 30 min, Walk and Vet are 60 min

    tasks = scheduler.filter_tasks(DAY, pet_name="Mongo", at_most=30)

    assert names(tasks) == [("Mongo", "Breakfast")]
    assert names(scheduler.filter_tasks(DAY, longer_than=30, status="pending")) == [
        ("Mongo", "Walk"),
        ("Princess Donut", "Vet Visit"),
    ]


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


def pet_with_daily_task(**overrides):
    pet = make_pet()
    task = make_task(recurrence="daily", **overrides)
    pet.add_task(task)
    return pet, task


def dates_of(pet):
    return [t.date for t in pet.get_tasks()]


def test_follow_up_shares_series_id_but_other_tasks_do_not():
    pet, task = pet_with_daily_task()
    other = make_task(name="Other")
    pet.add_task(other)

    follow_up = task.mark_complete()

    assert follow_up.series_id == task.series_id
    assert other.series_id != task.series_id


def test_edit_task_updates_fields_and_rolls_back_when_invalid():
    pet = make_pet()
    task = make_task()
    pet.add_task(task)

    pet.edit_task(task, {"name": "Brunch", "priority": 2})
    assert (task.name, task.priority) == ("Brunch", 2)

    with pytest.raises(ValueError):
        pet.edit_task(task, {"name": "Lunch", "end_time": time(8, 0)})  # ends before it starts
    assert task.name == "Brunch"
    assert task.end_time == time(9, 30)


def test_editing_date_or_time_of_completed_task_makes_it_pending():
    pet = make_pet()
    task = make_task()
    pet.add_task(task)
    task.mark_complete()

    pet.edit_task(task, {"date": date(2026, 10, 13)})
    assert task.is_complete() is False

    task.mark_complete()
    pet.edit_task(task, {"start_time": time(8, 0)})
    assert task.is_complete() is False


def test_editing_other_fields_of_completed_task_keeps_it_done():
    pet = make_pet()
    task = make_task()
    pet.add_task(task)
    task.mark_complete()

    pet.edit_task(task, {"name": "Brunch", "priority": 1, "comment": "new note"})

    assert task.is_complete() is True


def test_edit_with_same_date_keeps_completed_task_done():
    pet = make_pet()
    task = make_task()
    pet.add_task(task)
    task.mark_complete()

    pet.edit_task(task, {"date": task.date})

    assert task.is_complete() is True


def test_uncompleting_by_edit_then_completing_again_does_not_duplicate_follow_up():
    pet, task = pet_with_daily_task()
    task.mark_complete()
    pet.edit_task(task, {"start_time": time(8, 0), "end_time": time(8, 30)})
    assert task.is_complete() is False

    task.mark_complete()

    assert dates_of(pet) == [date(2026, 10, 11), date(2026, 10, 12)]


def test_edit_occurrence_leaves_next_occurrence_unchanged():
    pet, task = pet_with_daily_task()

    pet.edit_occurrence(task, {"start_time": time(7, 0), "end_time": time(7, 30)})

    first, second = pet.get_tasks()
    assert first.start_time == time(7, 0)
    assert second.date == date(2026, 10, 12)
    assert second.start_time == time(9, 0)  # the original time
    assert second.series_id == first.series_id


def test_edit_occurrence_on_already_followed_task_does_not_duplicate():
    pet, task = pet_with_daily_task()
    task.mark_complete()

    pet.edit_occurrence(task, {"priority": 1})

    assert dates_of(pet) == [date(2026, 10, 11), date(2026, 10, 12)]


def test_invalid_edit_occurrence_rolls_back_and_creates_nothing():
    pet, task = pet_with_daily_task()

    with pytest.raises(ValueError):
        pet.edit_occurrence(task, {"end_time": time(8, 0)})

    assert dates_of(pet) == [date(2026, 10, 11)]
    assert task.end_time == time(9, 30)


def test_edit_series_changes_this_and_later_but_not_earlier_or_other_series():
    pet, task = pet_with_daily_task()
    other = make_task(name="Other", recurrence="daily")
    pet.add_task(other)
    second = task.mark_complete()
    third = second.mark_complete()
    # edit from the second occurrence onward
    pet.edit_series(second, {"name": "Brunch", "priority": 1})

    assert task.name == "Breakfast"  # earlier: untouched
    assert (second.name, second.priority) == ("Brunch", 1)
    assert (third.name, third.priority) == ("Brunch", 1)
    assert other.name == "Other"


def test_edit_series_date_only_changes_this_occurrence():
    pet, task = pet_with_daily_task()
    second = task.mark_complete()

    pet.edit_series(task, {"date": date(2026, 10, 20), "priority": 2})

    assert task.date == date(2026, 10, 20)
    assert second.date == date(2026, 10, 12)  # keeps its own date
    assert second.priority == 2


def test_skip_task_removes_occurrence_and_keeps_series_going():
    pet, task = pet_with_daily_task()

    follow_up = pet.skip_task(task)

    assert follow_up.date == date(2026, 10, 12)
    assert dates_of(pet) == [date(2026, 10, 12)]
    assert task.pet is None


def test_skip_task_returns_existing_next_occurrence_without_duplicating():
    pet, task = pet_with_daily_task()
    existing = task.mark_complete()

    follow_up = pet.skip_task(task)

    assert follow_up is existing
    assert dates_of(pet) == [date(2026, 10, 12)]


def test_skip_non_recurring_task_just_removes_it():
    pet = make_pet()
    task = make_task()
    pet.add_task(task)

    assert pet.skip_task(task) is None
    assert pet.get_tasks() == []


def test_remove_series_removes_this_and_later_only():
    pet, task = pet_with_daily_task()
    other = make_task(name="Other", recurrence="daily")
    pet.add_task(other)
    second = task.mark_complete()
    third = second.mark_complete()

    removed = pet.remove_series(second)

    assert removed == 2
    remaining = pet.get_tasks()
    assert task in remaining and other in remaining
    assert second not in remaining and third not in remaining


def test_remove_task_removes_only_that_instance():
    pet, task = pet_with_daily_task()
    second = task.mark_complete()

    pet.remove_task(task)

    assert pet.get_tasks() == [second]


def test_edit_or_delete_clears_conflict_warning():
    scheduler, donut, mongo = make_conflict_setup()
    walk = make_task(name="Walk", category="walk", start_time=time(10, 0), end_time=time(11, 0))
    groom = make_task(name="Groom", category="grooming", start_time=time(10, 30), end_time=time(11, 30))
    mongo.add_task(walk)
    donut.add_task(groom)
    assert len(scheduler.conflict_warnings(DAY)) == 1

    donut.edit_task(groom, {"start_time": time(12, 0), "end_time": time(13, 0)})
    assert scheduler.conflict_warnings(DAY) == []

    donut.edit_task(groom, {"start_time": time(10, 30), "end_time": time(11, 30)})
    assert len(scheduler.conflict_warnings(DAY)) == 1
    donut.remove_task(groom)
    assert scheduler.conflict_warnings(DAY) == []


def test_edit_info_updates_pet_and_keeps_its_tasks():
    pet = make_pet()
    pet.add_task(make_task())

    pet.edit_info("  Biscuit ", "dog", 5)

    assert (pet.name, pet.pet_type, pet.age) == ("Biscuit", "dog", 5)
    assert len(pet.get_tasks()) == 1
    assert pet.get_tasks()[0].pet is pet


def test_edit_info_rejects_blank_name_and_negative_age_without_changing_pet():
    pet = make_pet()

    with pytest.raises(ValueError):
        pet.edit_info("   ", "dog", 5)
    with pytest.raises(ValueError):
        pet.edit_info("Biscuit", "dog", -1)

    assert (pet.name, pet.pet_type, pet.age) == ("Princess Donut", "Cat", 3)


def test_edit_info_rejects_another_pets_name_but_allows_own_name():
    owner = PawPal().add_owner("Ana")
    donut = owner.add_pet("Princess Donut", "cat", 3)
    owner.add_pet("Mongo", "dog", 1)

    with pytest.raises(ValueError):
        donut.edit_info("mongo", "cat", 3)  # duplicate, ignoring case

    donut.edit_info("princess donut", "cat", 4)  # re-casing its own name is fine
    assert (donut.name, donut.age) == ("princess donut", 4)


def remaining_after(*slots, available=480, pets=1, day=DAY):
    """Add one task per (start, end) slot to a new owner's pet and return remaining_minutes(day)."""
    owner = PawPal().add_owner("Ana")
    owner.daily_available_minutes = available
    pet_list = [owner.add_pet(f"Pet{i}", "dog", 1) for i in range(pets)]
    for i, (start, end) in enumerate(slots):
        pet_list[i % pets].add_task(make_task(name=f"Task{i}", start_time=start, end_time=end))
    return Scheduler(owner).remaining_minutes(day)


def test_remaining_minutes_on_empty_day_is_all_available_time():
    assert remaining_after() == 480


def test_remaining_minutes_adds_separate_tasks():
    assert remaining_after((time(9, 0), time(9, 30)), (time(10, 0), time(11, 0))) == 390


def test_remaining_minutes_counts_identical_overlap_once():
    assert remaining_after((time(9, 0), time(9, 30)), (time(9, 0), time(9, 30))) == 450


def test_remaining_minutes_counts_partial_overlap_as_one_block():
    assert remaining_after((time(9, 0), time(9, 30)), (time(9, 15), time(10, 0))) == 420


def test_remaining_minutes_ignores_task_nested_inside_another():
    assert remaining_after((time(9, 0), time(11, 0)), (time(9, 30), time(10, 0))) == 360


def test_remaining_minutes_counts_back_to_back_tasks_in_full():
    assert remaining_after((time(9, 0), time(9, 30)), (time(9, 30), time(10, 0))) == 420


def test_remaining_minutes_merges_a_chain_of_overlaps():
    slots = (
        (time(9, 0), time(10, 0)),
        (time(9, 30), time(10, 30)),
        (time(10, 15), time(11, 0)),
    )
    assert remaining_after(*slots) == 480 - 120


def test_remaining_minutes_goes_negative_when_overbooked():
    assert remaining_after((time(9, 0), time(18, 0)), available=60) == 60 - 540


def test_remaining_minutes_counts_simultaneous_tasks_for_two_pets_once():
    assert remaining_after((time(9, 0), time(9, 30)), (time(9, 0), time(9, 30)), pets=2) == 450


def test_remaining_minutes_ignores_tasks_on_other_dates():
    assert remaining_after((time(9, 0), time(9, 30)), day=date(2026, 10, 12)) == 480


def test_busy_minutes_handles_unsorted_tasks():
    tasks = [
        make_task(start_time=time(10, 15), end_time=time(11, 0)),
        make_task(start_time=time(9, 0), end_time=time(10, 0)),
        make_task(start_time=time(9, 30), end_time=time(10, 30)),
    ]

    assert Scheduler._busy_minutes(tasks) == 120


def test_adding_task_increases_pet_task_count():
    pet = make_pet()
    assert len(pet.get_tasks()) == 0

    pet.add_task(make_task())

    assert len(pet.get_tasks()) == 1


# ---------- Sorting ----------

def make_sorting_scheduler():
    """Tasks added deliberately out of order, across two pets, plus one on another day."""
    owner = PawPal().add_owner("Ana")
    donut = owner.add_pet("Princess Donut", "cat", 3)
    mongo = owner.add_pet("Mongo", "dog", 1)
    donut.add_task(make_task(name="Late", start_time=time(18, 0), end_time=time(18, 15), priority=2))
    mongo.add_task(make_task(name="Early", start_time=time(7, 0), end_time=time(8, 30), priority=5))
    donut.add_task(make_task(name="Mid", start_time=time(12, 0), end_time=time(12, 45), priority=5))
    mongo.add_task(make_task(name="Tomorrow", date=date(2026, 10, 12), start_time=time(6, 0), end_time=time(6, 10)))
    return Scheduler(owner)


def test_daily_plan_is_in_chronological_order_across_pets():
    plan = make_sorting_scheduler().daily_plan(DAY)

    assert [t.name for t in plan] == ["Early", "Mid", "Late"]


def test_sort_by_priority_is_highest_first_with_ties_by_time():
    result = make_sorting_scheduler().sort_tasks(DAY, "priority")

    assert [t.name for t in result] == ["Early", "Mid", "Late"]  # 5, 5 (earlier first), 2


def test_sort_by_duration_is_shortest_first_with_ties_by_time():
    result = make_sorting_scheduler().sort_tasks(DAY, "duration")

    assert [t.name for t in result] == ["Late", "Mid", "Early"]  # 15, 45, 90 min


def test_sort_excludes_tasks_from_other_dates():
    scheduler = make_sorting_scheduler()

    assert "Tomorrow" not in [t.name for t in scheduler.sort_tasks(DAY, "time")]
    assert [t.name for t in scheduler.sort_tasks(date(2026, 10, 12), "time")] == ["Tomorrow"]


def test_sort_rejects_unknown_sort_key():
    with pytest.raises(ValueError):
        make_sorting_scheduler().sort_tasks(DAY, "alphabet")


def test_sort_on_empty_day_returns_empty_list():
    scheduler, _, _ = make_conflict_setup()

    assert scheduler.daily_plan(DAY) == []


def test_pet_get_tasks_sorts_by_date_then_start_time():
    pet = make_pet()
    pet.add_task(make_task(name="D2 early", date=date(2026, 10, 12), start_time=time(7, 0), end_time=time(7, 30)))
    pet.add_task(make_task(name="D1 late", start_time=time(20, 0), end_time=time(20, 30)))
    pet.add_task(make_task(name="D1 early", start_time=time(6, 0), end_time=time(6, 30)))

    assert [t.name for t in pet.get_tasks()] == ["D1 early", "D1 late", "D2 early"]


# ---------- Recurrence edge cases ----------

@pytest.mark.parametrize("recurrence, start, expected", [
    ("daily", date(2026, 10, 31), date(2026, 11, 1)),    # month boundary
    ("daily", date(2026, 12, 31), date(2027, 1, 1)),     # year boundary
    ("daily", date(2028, 2, 28), date(2028, 2, 29)),     # leap day
    ("weekly", date(2026, 12, 28), date(2027, 1, 4)),
    ("monthly", date(2026, 10, 11), date(2026, 11, 10)),  # documented as 30 days
])
def test_follow_up_date_crosses_month_and_year_boundaries(recurrence, start, expected):
    pet = make_pet()
    task = make_task(date=start, recurrence=recurrence)
    pet.add_task(task)

    assert task.mark_complete().date == expected


def test_completing_a_date_the_task_does_not_occur_on_raises_and_changes_nothing():
    pet, task = pet_with_daily_task()

    with pytest.raises(ValueError):
        task.mark_complete(on=date(2026, 10, 15))

    assert task.is_complete() is False
    assert len(pet.get_tasks()) == 1


def test_follow_up_copies_category_priority_and_end_time():
    pet = make_pet()
    task = make_task(category="meds", priority=2, end_time=time(9, 45), recurrence="daily")
    pet.add_task(task)

    follow_up = task.mark_complete()

    assert (follow_up.category, follow_up.priority, follow_up.end_time) == ("meds", 2, time(9, 45))


def test_completing_each_follow_up_keeps_the_chain_going():
    pet, task = pet_with_daily_task()

    second = task.mark_complete()
    third = second.mark_complete()

    assert dates_of(pet) == [date(2026, 10, 11), date(2026, 10, 12), date(2026, 10, 13)]
    assert third.series_id == task.series_id


def test_completing_recurring_task_does_not_mark_follow_up_done():
    pet, task = pet_with_daily_task()

    follow_up = task.mark_complete()

    assert Scheduler(pet.owner).filter_tasks(follow_up.date, status="pending") == [follow_up]


# ---------- Conflict edge cases ----------

def test_three_way_overlap_reports_all_three_pairs():
    scheduler, donut, mongo = make_conflict_setup()
    donut.add_task(make_task(name="A", category="walk", start_time=time(9, 0), end_time=time(11, 0)))
    mongo.add_task(make_task(name="B", category="meds", start_time=time(9, 30), end_time=time(10, 30)))
    donut.add_task(make_task(name="C", category="grooming", start_time=time(10, 0), end_time=time(10, 15)))

    pairs = {frozenset((a.name, b.name)) for a, b in scheduler.find_conflicts(DAY)}

    assert pairs == {frozenset("AB"), frozenset("AC"), frozenset("BC")}


def test_same_time_on_different_dates_is_not_a_conflict():
    scheduler, donut, mongo = make_conflict_setup()
    donut.add_task(make_task(name="Today", category="walk"))
    mongo.add_task(make_task(name="Tomorrow", category="meds", date=date(2026, 10, 12)))

    assert scheduler.conflict_warnings(DAY) == []
    assert scheduler.conflict_warnings(date(2026, 10, 12)) == []


def test_identical_times_for_same_pet_is_a_conflict():
    scheduler, donut, _ = make_conflict_setup()
    donut.add_task(make_task(name="One", category="walk"))
    donut.add_task(make_task(name="Two", category="meds"))

    assert len(scheduler.find_conflicts(DAY)) == 1


def test_task_nested_inside_another_is_a_conflict():
    scheduler, donut, _ = make_conflict_setup()
    donut.add_task(make_task(name="Outer", category="walk", start_time=time(9, 0), end_time=time(12, 0)))
    donut.add_task(make_task(name="Inner", category="meds", start_time=time(10, 0), end_time=time(10, 30)))

    (message,) = scheduler.conflict_warnings(DAY)

    assert "10:00 AM - 10:30 AM" in message


def test_warnings_for_ignores_back_to_back_and_never_lists_the_task_against_itself():
    scheduler, donut, mongo = make_conflict_setup()
    first = make_task(name="First", start_time=time(9, 0), end_time=time(9, 30))
    second = make_task(name="Second", category="walk", start_time=time(9, 30), end_time=time(10, 0))
    donut.add_task(first)
    mongo.add_task(second)

    assert scheduler.warnings_for(first) == []
    assert scheduler.warnings_for(second) == []
