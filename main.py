#testing grounds
from pawpal_system import PawPal, Owner, Pet, Task, Schedule, Scheduler
from datetime import date, time, timedelta

#create an Owner
pawpal = PawPal()
owner = pawpal.add_owner("Ana")

#create two Pets
donut = owner.add_pet("Princess Donut", "Cat", 3)
mongo = owner.add_pet("Mongo", "Dog", 1)

#add tasks with different times
donut.add_task(Task("Breakfast", "feeding", date.today(), time(9, 0), time(9, 30), 5))
donut.add_task(Task("Vet Visit", "meds", date.today(),  time(14, 0), time(16, 0), 5, "Donut needs to get her vaccinations"))
mongo.add_task(Task("Breakfast", "feeding", date.today(), time(9, 0), time(9, 30), 5))
mongo_walk = Task("Morning Walk", "walk", date.today(), time(10, 0), time(11, 0), 4, recurrence="daily")
mongo.add_task(mongo_walk)

today = date.today()
tomorrow = today + timedelta(days=1)
scheduler = Scheduler(owner)


def print_tasks(tasks, day, heading=None):
    """Print each task on its own line (with its status for the given day)."""
    if heading:
        print(heading)
    if not tasks:
        print("  (no tasks)")
    for task in tasks:
        start = task.start_time.strftime("%I:%M %p")
        end = task.end_time.strftime("%I:%M %p")
        status = "[x] Done    " if task.is_complete(day) else "[ ] Not done"
        print(f"{status} {start} - {end}  {task.name:<15} ({task.pet.name}, {task.category}, priority {task.priority})")
        if task.comment:
            print(f"             note: {task.comment}")


def print_minutes_remaining(day):
    """Print how many of the owner's available minutes are left on the given day."""
    print(f"Minutes remaining: {scheduler.remaining_minutes(day):.0f}")


def print_warnings(day, heading=None):
    """Print every conflict and heads-up message for the given day."""
    if heading:
        print(heading)
    for message in scheduler.conflict_warnings(day) or ["(no conflicts)"]:
        print(f"  {message}")


#print "Today's Schedule"
print(f"Today's Schedule for {owner.name} - {today.strftime('%A, %B %d, %Y')}")
print("-" * 60)
print_tasks(scheduler.daily_plan(today), today)
print("-" * 60)
print_minutes_remaining(today)

#add a task that overlaps Mongo's walk: the scheduler returns warnings, it never crashes
grooming = Task("Grooming", "grooming", today, time(10, 30), time(11, 30), 3)
donut.add_task(grooming)
print()
for message in scheduler.warnings_for(grooming):
    print(f"WARNING when adding '{grooming.name}': {message}")

print()
print_warnings(today, "All conflicts today:")
print_minutes_remaining(today)  # overlapping time is counted once

#filtering: one day's tasks across all pets, by pet, length and status
print("\nFiltering today's tasks")
print("-" * 60)
print_tasks(scheduler.filter_tasks(today, pet_name="Mongo"), today, "Only Mongo:")
print_tasks(scheduler.filter_tasks(today, at_most=30), today, "\n30 minutes or shorter:")
print_tasks(scheduler.filter_tasks(today, longer_than=60), today, "\nLonger than an hour:")
print_tasks(scheduler.filter_tasks(today, pet_name="Princess Donut", status="pending", at_most=60),
            today, "\nDonut's pending tasks up to an hour:")

#editing a task: fix the conflict by moving Grooming to the afternoon
print("\nFixing the conflict: moving Grooming to 12:00 PM - 1:00 PM")
donut.edit_task(grooming, {"start_time": time(12, 0), "end_time": time(13, 0)})
print_warnings(today, "Conflicts now:")
print_minutes_remaining(today)

#a bad edit is rejected and the task is left unchanged
try:
    donut.edit_task(grooming, {"end_time": time(11, 0)})
except ValueError as error:
    print(f"\nEdit rejected: {error} (Grooming still ends at {grooming.end_time.strftime('%I:%M %p')})")

#deleting a task
print(f"\nDeleting '{grooming.name}'...")
donut.remove_task(grooming)
print(f"Tasks left today: {len(scheduler.daily_plan(today))}")
print_minutes_remaining(today)

#editing a pet
print(f"\nEditing {donut.name}: a year older")
donut.edit_info(donut.name, donut.pet_type, donut.age + 1)
print(f"{donut.name} is now {donut.age} years old")
try:
    donut.edit_info(" ", "Cat", 4)
except ValueError as error:
    print(f"Edit rejected: {error}")
try:
    donut.edit_info("mongo", "Cat", 4)
except ValueError as error:
    print(f"Edit rejected: {error}")

#complete the daily walk: the next occurrence is created automatically
print()
print(f"Completing '{mongo_walk.name}' ({mongo.name}, repeats {mongo_walk.recurrence})...")
next_walk = mongo.complete_task(mongo_walk)
if next_walk:
    print(f"Next occurrence created for {next_walk.date.strftime('%A, %B %d, %Y')} "
          f"at {next_walk.start_time.strftime('%I:%M %p')}")

#completing the same task again must not create a duplicate
print(f"Completing it again creates a new task: {mongo.complete_task(mongo_walk) is not None}")

print(f"\nTomorrow's Schedule - {tomorrow.strftime('%A, %B %d, %Y')}")
print("-" * 60)
print_tasks(scheduler.daily_plan(tomorrow), tomorrow)

#editing a recurring task: only tomorrow's walk moves; the one after keeps its time
print("\nMoving only tomorrow's walk to 9:30 AM - 10:15 AM (this occurrence only)...")
mongo.edit_occurrence(next_walk, {"start_time": time(9, 30), "end_time": time(10, 15)})
for day in (tomorrow, tomorrow + timedelta(days=1)):
    print_tasks(scheduler.daily_plan(day), day, f"{day.strftime('%A, %B %d')}:")

#deleting a recurring task: this occurrence and every later one
print("\nDeleting tomorrow's walk and all future ones...")
removed = mongo.remove_series(next_walk)
print(f"Removed {removed} occurrence(s)")
print_tasks(scheduler.daily_plan(tomorrow), tomorrow, f"{tomorrow.strftime('%A, %B %d')}:")
