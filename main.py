#testing grounds
from pawpal_system import PawPal, Owner, Pet, Task, Schedule, Scheduler
from datetime import date, time

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
mongo.add_task(Task("Morning Walk", "walk", date.today(), time(10, 0), time(11, 0), 4))

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

conflicts = scheduler.find_conflicts(today)
if conflicts:
    print()
    for a, b in conflicts:
        print(f"WARNING: '{a.name}' ({a.pet.name}) overlaps '{b.name}' ({b.pet.name})")