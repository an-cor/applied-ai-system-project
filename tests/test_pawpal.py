from pawpal_system import Task, Pet, Owner, Scheduler


def test_sort_tasks_by_time():
    """Tasks added out of order come back sorted chronologically."""
    owner = Owner(name="Alex")
    pet = Pet(name="Mochi", species="Dog")
    pet.add_task(Task(title="Evening Walk",   duration_minutes=30, priority="medium", time="18:00"))
    pet.add_task(Task(title="Feed Breakfast", duration_minutes=10, priority="high",   time="08:00"))
    pet.add_task(Task(title="Midday Check",   duration_minutes=5,  priority="low",    time="12:00"))
    owner.add_pet(pet)

    schedule = Scheduler().build_daily_schedule(owner)

    assert schedule[0].time == "08:00"
    assert schedule[1].time == "12:00"
    assert schedule[2].time == "18:00"


def test_filter_by_pet_name():
    """Only tasks belonging to the requested pet are returned."""
    scheduler = Scheduler()
    tasks = [
        Task(title="Walk",  duration_minutes=30, priority="high",   time="08:00", pet_name="Mochi"),
        Task(title="Feed",  duration_minutes=5,  priority="high",   time="08:00", pet_name="Luna"),
        Task(title="Brush", duration_minutes=10, priority="medium", time="09:00", pet_name="Mochi"),
    ]

    result = scheduler.filter_tasks(tasks, pet_name="Mochi")

    assert len(result) == 2
    assert all(t.pet_name == "Mochi" for t in result)


def test_filter_by_completion_status():
    """Pending and completed tasks can each be retrieved independently."""
    scheduler = Scheduler()
    done = Task(title="Walk", duration_minutes=30, priority="high", time="07:00", pet_name="Mochi")
    done.mark_complete()
    tasks = [
        done,
        Task(title="Feed",  duration_minutes=10, priority="high",   time="08:00", pet_name="Mochi"),
        Task(title="Brush", duration_minutes=5,  priority="medium", time="09:00", pet_name="Luna"),
    ]

    pending = scheduler.filter_tasks(tasks, completed=False)
    assert len(pending) == 2

    completed = scheduler.filter_tasks(tasks, completed=True)
    assert len(completed) == 1
    assert completed[0].title == "Walk"


def test_recurring_daily_creates_next_day():
    """Completing a daily task appends a new task scheduled for the following day."""
    pet = Pet(name="Mochi", species="Dog")
    pet.add_task(Task(
        title="Morning Walk", duration_minutes=30, priority="high",
        time="07:30", frequency="daily", date="2026-03-29",
    ))

    pet.complete_task("Morning Walk")

    tasks = pet.get_tasks()
    assert len(tasks) == 2
    assert tasks[0].completed is True
    assert tasks[1].completed is False
    assert tasks[1].date == "2026-03-30"


def test_recurring_weekly_creates_next_week():
    """Completing a weekly task appends a new task scheduled seven days later."""
    pet = Pet(name="Luna", species="Cat")
    pet.add_task(Task(
        title="Grooming", duration_minutes=20, priority="medium",
        time="10:00", frequency="weekly", date="2026-03-29",
    ))

    pet.complete_task("Grooming")

    tasks = pet.get_tasks()
    assert len(tasks) == 2
    assert tasks[0].completed is True
    assert tasks[1].completed is False
    assert tasks[1].date == "2026-04-05"


def test_same_time_higher_priority_comes_first():
    """When two tasks share the same time, the higher-priority one appears first."""
    scheduler = Scheduler()
    tasks = [
        Task(title="Low Task",  duration_minutes=10, priority="low",  time="09:00"),
        Task(title="High Task", duration_minutes=10, priority="high", time="09:00"),
    ]

    result = scheduler.sort_tasks_by_time(tasks)

    assert result[0].title == "High Task"
    assert result[1].title == "Low Task"


def test_find_next_available_slot():
    """Slot finder skips busy blocks and returns the first open window."""
    scheduler = Scheduler()
    tasks = [
        # 08:00 – 09:00
        Task(title="Morning Walk", duration_minutes=60, priority="high", time="08:00"),
        # 09:00 – 09:30
        Task(title="Feed",         duration_minutes=30, priority="high", time="09:00"),
    ]

    # First free 20-min gap starts at 09:30
    slot = scheduler.find_next_available_slot(tasks, duration_minutes=20)
    assert slot == "09:30"

    # If the whole day is packed, return None
    packed = [Task(title="Block", duration_minutes=600, priority="high", time="08:00")]
    assert scheduler.find_next_available_slot(packed, duration_minutes=30) is None


def test_conflict_detection_flags_overlap():
    """Two tasks whose time windows overlap produce a conflict warning."""
    scheduler = Scheduler()
    tasks = [
        # Walk runs 07:30 – 08:00
        Task(title="Walk",            duration_minutes=30, priority="high", time="07:30", pet_name="Mochi"),
        # Vet runs 07:45 – 08:45 — starts before Walk ends
        Task(title="Vet Appointment", duration_minutes=60, priority="high", time="07:45", pet_name="Luna"),
    ]

    conflicts = scheduler.detect_conflicts(tasks)

    assert len(conflicts) == 1
    assert "Walk" in conflicts[0]
    assert "Vet Appointment" in conflicts[0]
