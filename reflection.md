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

**Final Building Blocks**
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

My scheduler considers time and priority as its main goals. Everything is sorted from first to last in a day and highest priority to lowest. 

- How did you decide which constraints mattered most?

The outcome is what mattered most. The generated schedule had to make sense to a user. If the dates are all over the place, lower priority things are being shown first, the name of the pets are not showing or what a task is, then it doesn't make sense how to use this tool. Usability from a user perspective I think is what mattered most and drove my decisions. 

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.

My original scheduler only checked for exact matching task times. Then filtered from highest priority to lowest. It had overlapping conflicts but the code did not have a conflict warning appear after generating a schedule. 

This was simpler to implement and explain but during testing, this missed overlapping tasks with different start times. So I improved the conflict detection to compare task durations as well.

This is the edge case that made it obvious.
Here is your schedule for today:
- 11:00 — 'Shower' for Mochi (medium priority, 61 min, repeats daily, pending)
- 11:30 — 'nap time' for Claus (medium priority, 60 min, repeats daily, pending)
- 12:00 — 'Morning walk' for Stinker (high priority, 60 min, repeats daily, pending)

- Why is that tradeoff reasonable for this scenario?

The simplicity is the trade off. A more understable scheduler adds complexity to the tool and the code but is far more usable and understable for a user. This tradeoff is reasonable because it is a small fix that has a large improvement on usability.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project?

I use Claude to help me design brainstorming in the UML class system, debugging after testing and running the code, then refactoring the code after bugs are found with the logic. 

- What kinds of prompts or questions were most helpful?

It was helpful to isolate the logic behind testing implementations. Understanding how the code is being tested by the model helped me understand the core code itself and what I am supposed to be on the look out. I used the code logic in tests/* to make sure that the UI matched the same logic. 

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.

The AI suggestion to display information "as-is" for a task in the scheduler without naming the actual pet. Only the tasks, time and priority were mentioned when the owner had one pet but never mentioend the pet. I did not like this because this creates gaps of logic regarding what the pet being taken cared for is. The name of the pet should be a constant part of a user interacting with the tool. 

- How did you evaluate or verify what the AI suggested?

I scanned the code to make sure the logic made sense for this project. I checked that the pytests were actually calling the other functions and running the code plus comparing it some expected output. Made sure the expected output was correct by running the commands on my terminal constantly through iterations. Made sure to check UI logic after backend implementation kept getting more and more complex. 

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?

This is what I tested
- add a name for user
- add a pet with name
- add a second pet 
- add different kinds of pets
- add tasks to multiple pets 
- click generate schedule 
- confirm the schedule 
- confirm conflict warning appears

- Why were these tests important?

These tests are important because it is what is expected for the tool to be used for. These behaviors mask the original three core actions a user should be able to perform of what was discussined in section 1 (system design). Without being able to do this, a user would not have their needs met using this tool.

**b. Confidence**

- How confident are you that your scheduler works correctly?

Condence 4/5

- What edge cases would you test next if you had more time?

If I had more time, I would add more tests regarding time and scheduling. For example tasks that start and end at the exact same time or when one ends and another starts immidiately at the same time and flag conflicts accordingly. I would also tests what happens when a pet doesn't have any tasks. I would also test removing tasks, before a schedule has been generated, in the middle of a cycle and after a cycle. 

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

I was very satisfied with the UI as soon as it was created. The logic was already implemented and the UI was very easy to use after. I liked that the testing I made using CLI had a smooth transition into testing with pytest and manually using the UI. 

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

I would also add a way to run the pytest tasks and make sure the backend is good using the UI. There is currently no button to test that the backend logic is working. This would help in not having to go back and forth with testing from the CLI and running commands to a more automated version where my tests are done only using the UI. Also, I would redesign how the input is handled in writing the time for a task. Its currently `HH:MM` which can be broken easily but a time widget can make this a lot easier to interact with.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

Having Claude only do one thing at a time is better than having multiple things done at once. I used separate Claude chats for different parts of the project. When I was doing too much in a single conversation, it was harder for me to follow along what Claude was implementing and I could tell the code quality dropped. I also learned I should avoid accepting AI output as-is. AI can be technically correct but misses the whole point of the app. I was able to catch things only because I know the real world use of this tool but AI does not have any context of this and just wants runnable code.