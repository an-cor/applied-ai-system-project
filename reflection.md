# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.

My initial UML design takes into account the pet, the owner, what's important for both of them and a structure to map this to a schedule.

- What classes did you include, and what responsibilities did you assign to each?

Classes:
- Pet: contains needs and attributes of pet
- Owner: needs to know pet. contains attributes of owner
- Calendar: Tracks dates and repetitions for pet. Tracks tasks and constraints for owner.
- Care Tasks: Pet tasks related to calendar like walks, feeding, meds, enrichment, grooming, etc.

Three core actions a user should be able to perform:
- Add a pet with pet care info
- Add events to a calendar with contraints and filter info
- View pet, personal and calendar info

**b. Design changes**

- Did your design change during implementation?

Yes.

- If yes, describe at least one change and why you made it.

Changed the classes "Calendar" to "Scheduler" and "Care Tasks" to "Tasks". 

I made this because I noticed that complexity was a lot higher by having the name "Calendar" as the class to handle scheduling. AI kept wanting to implement everything a calendar has to offer like a full date/time system but is not necessary for the scope of this project. Also having "Care Tasks" to just "Tasks" made this easier to implement. It a more well rounded term for its use case.

**c. Building Blocks**

**Owner**
- attributes: name, preferences, pets
- methods: add_pet(), get_pet(), get_all_tasks()

**Pet**
- attributes: name, species, age, notes, tasks
- methods: add_task(), remove_task(), get_tasks()

**Task**
- attributes: title, duration_minutes, priority, time, frequency, completed
- methods: mark_complete(), is_recurring()

**Scheduler**
- methods: build_daily_schedule(), sort_tasks_by_time(), filter_tasks(), detect_conflicts(), explain_schedule()

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
