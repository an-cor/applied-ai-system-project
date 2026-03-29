# PawPal+ (Module 2 Project)

**PawPal+** is a Streamlit app that helps a pet owner stay on top of daily pet care tasks — from morning walks to evening meds.

## Features

- Add an owner profile and multiple pets
- Create tasks with a title, time, duration, priority, and recurrence (once / daily / weekly)
- Generate a daily schedule sorted by time, with priority tie-breaking
- Detect and display conflicts when two tasks overlap
- Recurring tasks automatically queue their next occurrence when completed
- Plain-English schedule breakdown so the plan is easy to read
- Finds the next open time slot in the day for a new task of any duration, automatically skipping over busy blocks
- Returns `None` if no gap fits before the end of the day (18:00), so you always get a clear answer
- Priority shown with color-coded emoji labels (🔴 High, 🟡 Medium, 🟢 Low) in both the task list and schedule
- Task and schedule tables use a clean dataframe layout with compact columns for Time, Duration, and Status
- Conflict warnings stand out with highlighted `st.warning` blocks
- Schedule breakdown is tucked into a collapsible section to keep the page uncluttered
- CLI output shows priority labels and `✓`/`·` status symbols so printed schedules are easier to scan

## 📸 Demo

<!-- Add a screenshot of your running app here -->
<!-- To capture one: run `streamlit run app.py`, take a screenshot, save it as `demo.png`, and replace the line below -->
![PawPal+ UI](UI.png)
![PawPal+ demo](demo.png)

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

## Testing PawPal+

Run the test suite with:

```bash
python -m pytest tests/
```

The tests cover:

Scheduling logic — tasks are sorted by time, and ties are broken by priority (high → medium → low)
Recurring tasks — completing a daily or weekly task automatically queues the next occurrence
Filtering & conflict detection — tasks can be filtered by pet or completion status, and overlapping time windows are flagged
Confidence Level: 4/5 — Core scheduling and task management behaviors are well covered. Edge cases like removing tasks and back-to-back conflict boundaries are tested too. The main gap is around the AI explanation features, which are harder to unit test.

## Smarter Scheduling

The scheduler does more than just list tasks — it organizes them in a way that makes sense for a real day:

- Tasks are sorted by time so the schedule runs in order from morning to night
- When two tasks are scheduled at the same time, the higher priority task goes first (high → medium → low)
- Priority is shown with color-coded labels in both the task list and the generated schedule (🔴 High, 🟡 Medium, 🟢 Low) so it's easy to spot at a glance
- Conflict detection checks every pair of tasks and warns you if their time windows overlap
- Recurring tasks (daily or weekly) automatically create the next occurrence when marked complete

## UML representation of code

```
classDiagram
    class Owner {
        +str name
        +dict preferences
        +List pets
        +add_pet(pet)
        +get_pet(name) Pet
        +get_all_tasks() List
    }

    class Pet {
        +str name
        +str species
        +int age
        +str notes
        +List tasks
        +add_task(task)
        +complete_task(task_title)
        +remove_task(task_title)
        +get_tasks() List
    }

    class Task {
        +str title
        +int duration_minutes
        +str priority
        +str time
        +str frequency
        +bool completed
        +str pet_name
        +str date
        +mark_complete()
        +is_recurring() bool
        +next_occurrence() Task
    }

    class Scheduler {
        +build_daily_schedule(owner) List
        +sort_tasks_by_time(tasks) List
        +filter_tasks(tasks, completed, pet_name) List
        +detect_conflicts(tasks) List
        +explain_schedule(tasks) List
    }

    Owner "1" --> "*" Pet : has
    Pet "1" --> "*" Task : has
    Scheduler --> Owner : reads from
    Scheduler --> Task : organizes
```

This is visible using [Mermaid](https://mermaid.live/) (copy & paste)
![Mermaid UML](mermaid_UML_updated.png)