# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

Three Core Actions:
1. Add owner and Pet information
2. Add/Edit tasks (duriation, name of task, category, priority)
3. Scheduling: Display a daily schedule/plan based on constraints (filters).


Classes Used:
1. PawPal: Stores the list of owners. Responsibilities include adding an owner and fetching the list of owners.
2. Owner: Stores the name of owner, and list of their pets. Responsibilities include adding a pet, getting the list of the owner's pets.
3. Pet: Stores the pet's name, type, age, owner, and schedule. Responsibilities include editing the information capabilities.
4. Schedule: Stores the list of tasks. Responsibilities include adding, editing, and removing a task. It also fetches a list of tasks, has a filter for task name, category, priority, duration, completed, and/or date. Also includes a daily, weekly, and monthly display.
5. Task: Stores the name, category, date, start and end time, priority, and comment of a task. It also keeps track if the task has been completed and if the task is repeated (the recurrance). Responsibilities include getting the duration of the task, getting the date of the task, and marking the task as complete.
6. Scheduler: Stores the schedule. Responsibilities include compiling the daily plan, sorting the tasks, and finding conflicts.


**b. Design changes**

My design changed while I turned the UML into Python stubs and reviewed the class relationships. The biggest change was adding a top-level PawPal class that holds all owners, so owners are created through PawPal.add_owner() instead of directly. I also changed Scheduler to plan for an Owner instead of a single Schedule. The first version could only plan for one pet, but a real owner has several pets and needs one daily plan across all of them. To support that, I gave Task, Schedule and Pet back-references to their pet and owner. I also added a unique id to Task, so editing or removing a task can't hit a different task with identical details.

After checking the project requirements, I also added add_task, edit_task, remove_task and get_tasks methods to Pet. Originally the tasks lived only in Pet.schedule, so the methods for managing them were on Schedule, and Pet itself had no way to manage its own tasks. The new Pet methods simply forward to its schedule. That makes Pet the clear place to add and manage a pet's tasks, and Schedule keeps the filtering and display logic.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

In the README it stated to consider the owner's prefence. I decided to include it in my inital plannin, but as I started implementing the code, I couldn't think of a purose for a "prefrence." Wouldn't know what it could be used for either and how it could be tracked or measured. So for the time being, I decided to remove this from the code.

The Owner's prefrence can also meld into the priority and the filters they can have on the schedule. So I think my final decision was ok to make.

**b. Tradeoffs**

 Editing only the current occurance of reoccurring tasks creates the next occurance right away. This is so that changes doesn't carry over into the rest of the occurances since the reoccurance just 'copies' the current instance of the task.

---

## 3. AI Collaboration

**a. How you used AI**

I used AI for brainstorming and finding holes in my inital design. My very first design - like me just drawing out the idea on paper - was very bare bones. When I gave Claude my plan it agreed fully but when I got started talking with it and going back-and-forth, I realized that there were aspects of my design missing. A big one was the overall connection and relationship between all the classes across the application. An owner needs to be linked to their pet(s) in some way. Schedule needs to linked to the owner. All of these things came slowly from me brainstorming the app idea with Claude.

**b. Judgment and verification**

One AI suggestion that I rejected was during the implementation of the 'skeleton' classes. While working on Owner, Claude suggested get_pet_names() alongside get_pets(). I thought that this was redundent for the time being. There is no need to have both those functions. The function get_pet_names() could be implemented as a helper function down the line, but for the time being, it wasn't needed.

---

## 4. Testing and Verification

**a. What you tested**

I tested running the application and seeing how the UI worked/looked. I want to point out, all the testing done (test_pawpal.py and main.py tests included) is very important. Especially when the UI isn't ready or fully developed yet. But I found that once the UI was ready to run, I tested different cases on tht UI a lot. I tried different combinations of task, pets, times, durations. This is where a good deal of finds were done on my end.

AI is really good at testing from the command prompt, but it can't test directly on the UI (at least not our AI since it doesn't have any skills built into it). So I noticed things that the Claude couldn't.

**b. Confidence**

Overall I think this app works well for the amount of time put into it! However, there are things I would like to add. For example, for conflicts, I would like to have added a warning directly next to the tasks on the schedule that are conflicting.

I would also like to add a multiple owner functionality.

---

## 5. Reflection

**a. What went well**

Testing. I believe that the testing went smooth. I think this is in part because Claude was very diligent and tested all the changes it made along the implementation.

**b. What you would improve**

I would incorporate a database to keep track of owners, pets, and tasks on the database so that new entries don't have to be added upon each new run of the app.

**c. Key takeaway**

AI is really good at remembering things! I would tell it "Here is a list of things we need to do. Let's do this one-by-one and take considerations of implementation for each." Once we were done with one of the items on the list Claude would tell me "Here is a list of things that is left: ... Which one should we cover next?" I really liked this because we were able to take things step-by-step. I think this helped a lot in the grand scheme of things since this is how programming should be (and was before the use of AI). We would implement things one clasee, or one function at a time. And doing this with a very smart helper I think reduced the amount of bugs I ran into.
