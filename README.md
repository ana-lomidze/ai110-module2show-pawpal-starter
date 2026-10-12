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
| `Owner` | Holds the owner's pets and daily available minutes. `get_all_tasks()` collects the tasks of every pet, so the rest of the app never reads a single pet directly. |
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
- **Recurrence:** tasks can repeat `daily`, `weekly` or `monthly`. Each task is a single dated occurrence, so `occurs_on(date)` only matches its own date. Completing a repeating task creates the next occurrence (+1, +7 or +30 days), and never creates it twice. Occurrences are linked by a `series_id`.
- **Validation:** bad input, such as a blank name, an out-of-range priority or an end time before the start, raises a `ValueError`. Editing a task rolls back if the new values are invalid.
- **Overbooking:** `remaining_minutes` can go negative, which shows by how much a day is overbooked.



## 🖥️ Sample Output

### CLI (`python main.py`)

Note: This was from a very early run of this app.
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


## 🧪 Testing PawPal+

```bash
# Run the full test suite:
python -m pytest

# `-v` to list every test by name:
python -m pytest -v
```

### What the tests cover

The suite in `tests/test_pawpal.py` has 86 tests covering the core scheduling logic:

- **Sorting:** the daily plan comes back in chronological order across all pets. Tasks can also be sorted by priority (highest first) or duration (shortest first), with ties broken by start time. Filtered results can be sorted the same way (`sort_by`), and the sort is applied after filtering. Tasks from other dates are excluded, and an unknown sort key raises an error.
- **Recurring tasks:** completing a daily, weekly or monthly task creates the next occurrence once and never twice. The date rolls over correctly at month, year and leap-day boundaries. Follow-ups keep the task's details and series, and completion is tracked per date.
- **Conflict detection:** overlapping tasks are flagged across pets. A same-pet overlap or a different-category overlap is a `Conflict`. Different pets doing the same category is a softer `Heads-up`. Back-to-back tasks are not flagged. Three-way and nested overlaps are handled. Tasks at the same time on different dates don't conflict.
- **Filtering:** the day's tasks can be filtered by pet, status, category and length, alone or combined, including boundary lengths and empty results. Results default to time order and can be re-sorted by priority or duration.
- **Editing and deleting:** edits roll back if invalid. Recurring tasks can be changed or deleted for one occurrence or for the whole series.
- **Time remaining:** overlapping tasks are counted once, back-to-back tasks in full, and an overbooked day gives a negative number.


### Sample Output:

```
python -m pytest -v
========================================================= test session starts =========================================================
platform win32 -- Python 3.14.7, pytest-9.1.1, pluggy-1.6.0 -- 
testpaths: tests
plugins: anyio-4.15.1
collected 86 items

tests/test_pawpal.py::test_mark_complete_changes_task_status PASSED                                                              [  1%]
tests/test_pawpal.py::test_next_date_uses_recurrence_interval PASSED                                                             [  2%]
tests/test_pawpal.py::test_task_occurs_only_on_its_own_date PASSED                                                               [  3%]
tests/test_pawpal.py::test_completing_recurring_task_creates_next_occurrence PASSED                                              [  4%]
tests/test_pawpal.py::test_mark_complete_directly_creates_next_occurrence PASSED                                                 [  5%]
tests/test_pawpal.py::test_mark_complete_on_task_without_pet_creates_nothing PASSED                                              [  6%]
tests/test_pawpal.py::test_completing_non_recurring_task_creates_nothing PASSED                                                  [  8%]
tests/test_pawpal.py::test_completing_twice_does_not_duplicate_next_occurrence PASSED                                            [  9%]
tests/test_pawpal.py::test_filter_without_filters_returns_whole_day_in_time_order PASSED                                         [ 10%]
tests/test_pawpal.py::test_filter_by_pet PASSED                                                                                  [ 11%]
tests/test_pawpal.py::test_filter_by_status PASSED                                                                               [ 12%]
tests/test_pawpal.py::test_filter_by_pet_and_status PASSED                                                                       [ 13%]
tests/test_pawpal.py::test_filter_by_category PASSED                                                                             [ 15%]
tests/test_pawpal.py::test_filter_by_duration_buckets_use_the_documented_boundaries PASSED                                       [ 16%]
tests/test_pawpal.py::test_filter_by_duration_without_bounds_returns_everything PASSED                                           [ 17%]
tests/test_pawpal.py::test_filter_by_duration_with_impossible_range_returns_empty_list PASSED                                    [ 18%]
tests/test_pawpal.py::test_filter_by_duration_combines_with_other_filters PASSED                                                 [ 19%]
tests/test_pawpal.py::test_filter_unknown_pet_returns_empty_list PASSED                                                          [ 20%]
tests/test_pawpal.py::test_filter_rejects_invalid_status PASSED                                                                  [ 22%]
tests/test_pawpal.py::test_filter_status_is_per_date PASSED                                                                      [ 23%]
tests/test_pawpal.py::test_no_overlap_means_no_warnings PASSED                                                                   [ 24%]
tests/test_pawpal.py::test_no_tasks_means_no_warnings PASSED                                                                     [ 25%]
tests/test_pawpal.py::test_same_pet_overlap_is_a_conflict PASSED                                                                 [ 26%]
tests/test_pawpal.py::test_different_pets_different_categories_is_a_conflict PASSED                                              [ 27%]
tests/test_pawpal.py::test_different_pets_same_category_is_a_heads_up PASSED                                                     [ 29%]
tests/test_pawpal.py::test_same_pet_same_category_is_still_a_conflict PASSED                                                     [ 30%]
tests/test_pawpal.py::test_find_conflicts_pairs_every_overlap PASSED                                                             [ 31%]
tests/test_pawpal.py::test_warnings_for_new_task_lists_only_its_overlaps PASSED                                                  [ 32%]
tests/test_pawpal.py::test_warnings_for_task_without_overlap_is_empty_and_does_not_raise PASSED                                  [ 33%]
tests/test_pawpal.py::test_follow_up_shares_series_id_but_other_tasks_do_not PASSED                                              [ 34%]
tests/test_pawpal.py::test_edit_task_updates_fields_and_rolls_back_when_invalid PASSED                                           [ 36%]
tests/test_pawpal.py::test_editing_date_or_time_of_completed_task_makes_it_pending PASSED                                        [ 37%]
tests/test_pawpal.py::test_editing_other_fields_of_completed_task_keeps_it_done PASSED                                           [ 38%]
tests/test_pawpal.py::test_edit_with_same_date_keeps_completed_task_done PASSED                                                  [ 39%]
tests/test_pawpal.py::test_uncompleting_by_edit_then_completing_again_does_not_duplicate_follow_up PASSED                        [ 40%]
tests/test_pawpal.py::test_edit_occurrence_leaves_next_occurrence_unchanged PASSED                                               [ 41%]
tests/test_pawpal.py::test_edit_occurrence_on_already_followed_task_does_not_duplicate PASSED                                    [ 43%]
tests/test_pawpal.py::test_invalid_edit_occurrence_rolls_back_and_creates_nothing PASSED                                         [ 44%]
tests/test_pawpal.py::test_edit_series_changes_this_and_later_but_not_earlier_or_other_series PASSED                             [ 45%]
tests/test_pawpal.py::test_edit_series_date_only_changes_this_occurrence PASSED                                                  [ 46%]
tests/test_pawpal.py::test_skip_task_removes_occurrence_and_keeps_series_going PASSED                                            [ 47%]
tests/test_pawpal.py::test_skip_task_returns_existing_next_occurrence_without_duplicating PASSED                                 [ 48%]
tests/test_pawpal.py::test_skip_non_recurring_task_just_removes_it PASSED                                                        [ 50%]
tests/test_pawpal.py::test_remove_series_removes_this_and_later_only PASSED                                                      [ 51%]
tests/test_pawpal.py::test_remove_task_removes_only_that_instance PASSED                                                         [ 52%]
tests/test_pawpal.py::test_edit_or_delete_clears_conflict_warning PASSED                                                         [ 53%]
tests/test_pawpal.py::test_edit_info_updates_pet_and_keeps_its_tasks PASSED                                                      [ 54%]
tests/test_pawpal.py::test_edit_info_rejects_blank_name_and_negative_age_without_changing_pet PASSED                             [ 55%]
tests/test_pawpal.py::test_edit_info_rejects_another_pets_name_but_allows_own_name PASSED                                        [ 56%]
tests/test_pawpal.py::test_remaining_minutes_on_empty_day_is_all_available_time PASSED                                           [ 58%]
tests/test_pawpal.py::test_remaining_minutes_adds_separate_tasks PASSED                                                          [ 59%]
tests/test_pawpal.py::test_remaining_minutes_counts_identical_overlap_once PASSED                                                [ 60%]
tests/test_pawpal.py::test_remaining_minutes_counts_partial_overlap_as_one_block PASSED                                          [ 61%]
tests/test_pawpal.py::test_remaining_minutes_ignores_task_nested_inside_another PASSED                                           [ 62%]
tests/test_pawpal.py::test_remaining_minutes_counts_back_to_back_tasks_in_full PASSED                                            [ 63%]
tests/test_pawpal.py::test_remaining_minutes_merges_a_chain_of_overlaps PASSED                                                   [ 65%]
tests/test_pawpal.py::test_remaining_minutes_goes_negative_when_overbooked PASSED                                                [ 66%]
tests/test_pawpal.py::test_remaining_minutes_counts_simultaneous_tasks_for_two_pets_once PASSED                                  [ 67%]
tests/test_pawpal.py::test_remaining_minutes_ignores_tasks_on_other_dates PASSED                                                 [ 68%]
tests/test_pawpal.py::test_busy_minutes_handles_unsorted_tasks PASSED                                                            [ 69%]
tests/test_pawpal.py::test_adding_task_increases_pet_task_count PASSED                                                           [ 70%]
tests/test_pawpal.py::test_daily_plan_is_in_chronological_order_across_pets PASSED                                               [ 72%]
tests/test_pawpal.py::test_sort_by_priority_is_highest_first_with_ties_by_time PASSED                                            [ 73%]
tests/test_pawpal.py::test_sort_by_duration_is_shortest_first_with_ties_by_time PASSED                                           [ 74%]
tests/test_pawpal.py::test_filter_sorts_by_time_by_default PASSED                                                                [ 75%]
tests/test_pawpal.py::test_filter_can_sort_by_priority_and_duration PASSED                                                       [ 76%]
tests/test_pawpal.py::test_filter_sorts_after_filtering PASSED                                                                   [ 77%]
tests/test_pawpal.py::test_filter_rejects_unknown_sort_key PASSED                                                                [ 79%]
tests/test_pawpal.py::test_sort_excludes_tasks_from_other_dates PASSED                                                           [ 80%]
tests/test_pawpal.py::test_sort_rejects_unknown_sort_key PASSED                                                                  [ 81%]
tests/test_pawpal.py::test_sort_on_empty_day_returns_empty_list PASSED                                                           [ 82%]
tests/test_pawpal.py::test_pet_get_tasks_sorts_by_date_then_start_time PASSED                                                    [ 83%]
tests/test_pawpal.py::test_follow_up_date_crosses_month_and_year_boundaries[daily-start0-expected0] PASSED                       [ 84%]
tests/test_pawpal.py::test_follow_up_date_crosses_month_and_year_boundaries[daily-start1-expected1] PASSED                       [ 86%]
tests/test_pawpal.py::test_follow_up_date_crosses_month_and_year_boundaries[daily-start2-expected2] PASSED                       [ 87%]
tests/test_pawpal.py::test_follow_up_date_crosses_month_and_year_boundaries[weekly-start3-expected3] PASSED                      [ 88%]
tests/test_pawpal.py::test_follow_up_date_crosses_month_and_year_boundaries[monthly-start4-expected4] PASSED                     [ 89%]
tests/test_pawpal.py::test_completing_a_date_the_task_does_not_occur_on_raises_and_changes_nothing PASSED                        [ 90%]
tests/test_pawpal.py::test_follow_up_copies_category_priority_and_end_time PASSED                                                [ 91%]
tests/test_pawpal.py::test_completing_each_follow_up_keeps_the_chain_going PASSED                                                [ 93%]
tests/test_pawpal.py::test_completing_recurring_task_does_not_mark_follow_up_done PASSED                                         [ 94%]
tests/test_pawpal.py::test_three_way_overlap_reports_all_three_pairs PASSED                                                      [ 95%]
tests/test_pawpal.py::test_same_time_on_different_dates_is_not_a_conflict PASSED                                                 [ 96%]
tests/test_pawpal.py::test_identical_times_for_same_pet_is_a_conflict PASSED                                                     [ 97%]
tests/test_pawpal.py::test_task_nested_inside_another_is_a_conflict PASSED                                                       [ 98%]
tests/test_pawpal.py::test_warnings_for_ignores_back_to_back_and_never_lists_the_task_against_itself PASSED                      [100%]

========================================================= 86 passed in 0.15s ==========================================================
```

### Confidence Level 
⭐⭐⭐⭐½ (4.5 / 5)

All 86 tests pass, and they cover the core behaviors that matter most for a scheduler: sorting, recurring tasks and conflict detection. They also cover the edge cases around them: month, year and leap-day rollovers, back-to-back versus overlapping tasks, three-way and nested overlaps, and invalid edits that must roll back.

I'm holding back half a star because I do believe that one of the best ways to test behavior is to run the application and try different scenarios on the app itself.


## 📐 Smarter Scheduling

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_tasks`, `Scheduler.daily_plan`, `Scheduler.filter_tasks(sort_by=...)` | by `"time"`, `"priority"` (highest first) or `"duration"` (shortest first), ties broken by start time. The daily plan is in time order across all pets, and the app has a "Sort by" dropdown |
| Filtering | `Scheduler.filter_tasks` | one day's tasks across all pets, by pet name, status (`"done"` or `"pending"` for that date), category and length (`longer_than` / `at_most` minutes), then sorted by `sort_by` (time by default). The app offers pet, status, length and sort dropdowns. `Schedule.filter_tasks` still filters a single pet's tasks by name, category, priority, max duration, completion and date |
| Conflict handling | `Scheduler.find_conflicts`, `Scheduler.conflict_warnings`, `Scheduler.warnings_for` | finds overlapping tasks in one pass over the day (back-to-back is not an overlap) and returns warning messages instead of raising. Same pet, or different pets with different categories: `Conflict`. Different pets, same category: a softer `Heads-up`, since both can be done together (`Scheduler.is_shared_time`). `warnings_for` checks a single task, e.g. right after it is added or edited |
| Recurring tasks | `Task.next_date`, `Task.mark_complete`, `Task.spawn_next`, `Schedule.complete_task` | `daily` (+1 day), `weekly` (+7 days) or `monthly` (every 30 days). Each task is one dated occurrence; completing it creates the next one automatically, and never creates it twice. Completion is per date |
| Editing and deleting | `Schedule.edit_task`, `edit_occurrence`, `edit_series`, `skip_task`, `remove_series` | recurring tasks can be changed or deleted for **this occurrence only** or **this and all future occurrences** (occurrences are linked by a `series_id`). Changing a completed task's date or times makes it pending again |
| Time left in the day | `Scheduler.remaining_minutes` | available minutes minus scheduled minutes, with overlapping time counted once, so two pets fed together use 30 minutes, not 60. Negative means overbooked |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. Add an Owner's name to create an owner.
2. Add a Pet. Enter their name, species and age. Click "Add pet."
3. You realized you entered the wrong age! Click the pencil icon nect to your pet to edit the pet's age to the correct one.
4. You have two pets. So you add another pet, with all their information.
5. Scrolling down to the tasks section, you add a task for the first pet you entered. You have to feed them lunch this afternoon! You add the title, time, and category. For "Repeats" you pick "daily." Click "Add task."
6. You add the same task for your second pet because you usually feed them at the same time. You get a warning for conflict, but the system knows that this task can be done at the same time.
7. You have completed these tasks so you click the "Mark done" button on the schedule. This task gets generated for the next day for both animals! You see you can filter the schedule for "Done" and "Pending" tasks. Selecting "Done" in the dropdown shows you these two tasks! Selecting "Pending" gives you text that says no tasks have been found with this filter.
8. You add a second task for your first pet for the time 13:00-13:30.
9. You add a third task for your first pet for the time 13:15-15:00 (different category). You get a warning that doesn't go away until you change the time of on of the conflicting tasks or delete one of the conflict tasks. You decide to delete this task by clicking the trash can icon next to this task on the schedule.
10. You add a 3 new, non-conflicting, task for you second pet that is for 2 hours, 30 minutes, and 1 hour. All three with different priority levels.
11. You realize you made a spelling mistake for one of the tasks! You click the pencil icon next to the task and edit the spelling mistake. Click save. The task's title has been updated!
12. You see the sorting. You want to be able to see the tasks you have listed in the duration (from longest to shorted). You select "Duration" in the "Sort by" dropdown. It sorts the tasks by duration! You select "Priority" next. The schedule shows the tasks hightest to lowest. You change the sort to the default (Time).
13. You try the "Show length" dropdown. The filters work as indended.

```
Today's Schedule for Ana - Sunday, October 11, 2026
------------------------------------------------------------
[ ] Not done 09:00 AM - 09:30 AM  Breakfast       (Princess Donut, feeding, priority 5)
[ ] Not done 09:00 AM - 09:30 AM  Breakfast       (Mongo, feeding, priority 5)
[ ] Not done 10:00 AM - 11:00 AM  Morning Walk    (Mongo, walk, priority 4)
[ ] Not done 02:00 PM - 04:00 PM  Vet Visit       (Princess Donut, meds, priority 5)
             note: Donut needs to get her vaccinations
------------------------------------------------------------
Minutes remaining: 270

WARNING when adding 'Grooming': Conflict: 'Morning Walk' (Mongo) and 'Grooming' (Princess Donut) overlap (10:30 AM - 11:00 AM). You can't do both at once.

All conflicts today:
  Heads-up: 'Breakfast' (Princess Donut) and 'Breakfast' (Mongo) overlap (09:00 AM - 09:30 AM). Fine if you do them together.
  Conflict: 'Morning Walk' (Mongo) and 'Grooming' (Princess Donut) overlap (10:30 AM - 11:00 AM). You can't do both at once.
Minutes remaining: 240

Filtering today's tasks
------------------------------------------------------------
Only Mongo:
[ ] Not done 09:00 AM - 09:30 AM  Breakfast       (Mongo, feeding, priority 5)
[ ] Not done 10:00 AM - 11:00 AM  Morning Walk    (Mongo, walk, priority 4)

30 minutes or shorter:
[ ] Not done 09:00 AM - 09:30 AM  Breakfast       (Princess Donut, feeding, priority 5)
[ ] Not done 09:00 AM - 09:30 AM  Breakfast       (Mongo, feeding, priority 5)

Longer than an hour:
[ ] Not done 02:00 PM - 04:00 PM  Vet Visit       (Princess Donut, meds, priority 5)
             note: Donut needs to get her vaccinations

Donut's pending tasks up to an hour:
[ ] Not done 09:00 AM - 09:30 AM  Breakfast       (Princess Donut, feeding, priority 5)
[ ] Not done 10:30 AM - 11:30 AM  Grooming        (Princess Donut, grooming, priority 3)

Fixing the conflict: moving Grooming to 12:00 PM - 1:00 PM
Conflicts now:
  Heads-up: 'Breakfast' (Princess Donut) and 'Breakfast' (Mongo) overlap (09:00 AM - 09:30 AM). Fine if you do them together.
Minutes remaining: 210

Edit rejected: End time must be after start time (Grooming still ends at 01:00 PM)

Deleting 'Grooming'...
Tasks left today: 4
Minutes remaining: 270

Editing Princess Donut: a year older
Princess Donut is now 4 years old
Edit rejected: Pet name cannot be empty
Edit rejected: Pet 'mongo' already exists for Ana

Completing 'Morning Walk' (Mongo, repeats daily)...
Next occurrence created for Monday, October 12, 2026 at 10:00 AM
Completing it again creates a new task: False

Tomorrow's Schedule - Monday, October 12, 2026
------------------------------------------------------------
[ ] Not done 10:00 AM - 11:00 AM  Morning Walk    (Mongo, walk, priority 4)

Moving only tomorrow's walk to 9:30 AM - 10:15 AM (this occurrence only)...
Monday, October 12:
[ ] Not done 09:30 AM - 10:15 AM  Morning Walk    (Mongo, walk, priority 4)
Tuesday, October 13:
[ ] Not done 10:00 AM - 11:00 AM  Morning Walk    (Mongo, walk, priority 4)

Deleting tomorrow's walk and all future ones...
Removed 2 occurrence(s)
Monday, October 12:
  (no tasks)
```


## 🚀 Stretch Goals

Ideas I considered but deliberately left out to keep the scope focused. None of them are needed for the core features above.

- **Multiple owners in the app.** The backend already supports several owners (`PawPal` keeps a registry with unique names), but the Streamlit app holds a single owner in `st.session_state`. Supporting more would need an owner picker and an "add another owner" flow.
- **Smarter conflict presentation.** Conflicts are listed below the schedule and named in the message. Possible improvements: mark the affected rows with a warning icon, keep the "just added" warning on screen until the next change, show a count ("2 conflicts, 1 heads-up"), and suggest the next free time slot that fits the task.
- **Monthly recurrence on the same day of the month.** "Monthly" currently means every 30 days, so a task slides around the calendar (Jan 15, Feb 14, Mar 16). Tracking the original day would keep it on the 15th, clamped to the last day in short months.
- **Catch-up for missed recurring tasks.** The next occurrence is created when a task is completed, so a task that is never completed stops repeating. A future version could create the next occurrence automatically once a day has passed.
- **Delete a pet, or move a task to another pet.** Pets can be edited but not removed, and a task can't be reassigned (it has to be deleted and re-added). Deleting a pet would need a decision about what happens to its tasks.
- **Fewer repeated calculations.** The page rebuilds the day's task list several times per refresh (plan, filters, conflicts, remaining time). Computing it once and passing it along would be a small efficiency gain.


