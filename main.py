#testing grounds
from pawpal_system import PawPal, Owner, Pet, Task, Schedule, Scheduler
from datetime import date, time, timedelta

#create an Owner
pawpal = PawPal()
owner = pawpal.add_owner("Ana")

#create two Pets
donut = owner.add_pet("Princess Donut", "Cat", 3)
mongo = owner.add_pet("Mongo", "Dog", 1)

#add four tasks with different times
donut.add_task(Task("Breakfast", "feeding", date.today(), time(9, 0), time(9, 30), 5))
donut.add_task(Task("Vet Visit", "meds", date.today(),  time(14, 0), time(16, 0), 5, "Donut needs to get her vaccinations"))
mongo.add_task(Task("Breakfast", "feeding", date.today(), time(9, 0), time(9, 30), 5))
mongo_walk = Task("Morning Walk", "walk", date.today(), time(10, 0), time(11, 0), 4, recurrence="daily")
mongo.add_task(mongo_walk)

#print "Today's Schedule"
today = date.today()
scheduler = Scheduler(owner)

print(f"Today's Schedule for {owner.name} - {today.strftime('%A, %B %d, %Y')}")
print("-" * 60)
for task in scheduler.daily_plan(today):
    start = task.start_time.strftime("%I:%M %p")
    end = task.end_time.strftime("%I:%M %p")
    status = "[x] Done    " if task.is_complete(today) else "[ ] Not done"
    print(f"{status} {start} - {end}  {task.name:<15} ({task.pet.name}, {task.category}, priority {task.priority})")
    if task.comment:
        print(f"             note: {task.comment}")
print("-" * 60)
print(f"Minutes remaining: {scheduler.remaining_minutes(today):.0f}")

#add a task that overlaps Mongo's walk: the scheduler returns warnings, it never crashes
grooming = Task("Grooming", "grooming", today, time(10, 30), time(11, 30), 3)
donut.add_task(grooming)
print()
for message in scheduler.warnings_for(grooming):
    print(f"WARNING when adding '{grooming.name}': {message}")

warnings = scheduler.conflict_warnings(today)
if warnings:
    print()
    for message in warnings:
        print(message)

#complete the daily walk: the next occurrence is created automatically
print()
print(f"Completing '{mongo_walk.name}' ({mongo.name}, repeats {mongo_walk.recurrence})...")
next_walk = mongo.complete_task(mongo_walk)
if next_walk:
    print(f"Next occurrence created for {next_walk.date.strftime('%A, %B %d, %Y')} "
          f"at {next_walk.start_time.strftime('%I:%M %p')}")

#completing the same task again must not create a duplicate
print(f"Completing it again creates a new task: {mongo.complete_task(mongo_walk) is not None}")

tomorrow = today + timedelta(days=1)
print(f"\nTomorrow's Schedule - {tomorrow.strftime('%A, %B %d, %Y')}")
print("-" * 60)
for task in scheduler.daily_plan(tomorrow):
    print(f"{task.start_time.strftime('%I:%M %p')} - {task.end_time.strftime('%I:%M %p')}  "
          f"{task.name:<15} ({task.pet.name})")