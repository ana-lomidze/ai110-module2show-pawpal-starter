# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

Three Core Actions:
1. Add owner and Pet information
2. Add/Edit tasks (duriation, name of task, category, priority)
3. Scheduling: Display a daily schedule/plan based on constraints (filters) and priorities.

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

Classes Used:
1. PawPal: Stores the list of owners. Responsibilities include adding an owner and fetching the list of owners.
2. Owner: Stores the name of owner, and list of their pets. Responsibilities include adding a pet, getting the list of the owner's pets.
3. Pet: Stores the pet's name, type, age, owner, and schedule. Responsibilities include editing the information capabilities.
4. Schedule: Stores the list of tasks. Responsibilities include adding, editing, and removing a task. It also fetches a list of tasks, has a filter for task name, category, priority, duration, completed, and/or date. Also includes a daily, weekly, and monthly display.
5. Task: Stores the name, category, date, start and end time, priority, and comment of a task. It also keeps track if the task has been completed and if the task is repeated (the recurrance). Responsibilities include getting the duration of the task, getting the date of the task, and marking the task as complete.
6. Scheduler: Stores the schedule. Responsibilities include compiling the daily plan, sorting the tasks, and finding conflicts.


**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.
My design changed while I turned the UML into Python stubs and reviewed the class relationships. The biggest change was adding a top-level PawPal class that holds all owners, so owners are created through PawPal.add_owner() instead of directly. I also changed Scheduler to plan for an Owner instead of a single Schedule. The first version could only plan for one pet, but a real owner has several pets and needs one daily plan across all of them. To support that, I gave Task, Schedule and Pet back-references to their pet and owner. I also added a unique id to Task, so editing or removing a task can't hit a different task with identical details.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
