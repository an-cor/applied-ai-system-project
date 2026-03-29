from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import List, Optional


@dataclass
class Task:
    """Represents a single pet care activity."""
    title: str
    duration_minutes: int
    priority: str
    time: str
    frequency: str = "once"
    completed: bool = False
    pet_name: str = ""  # set when collected from an Owner; useful for filtering
    date: str = field(default_factory=lambda: date.today().isoformat())

    def mark_complete(self) -> None:
        """Sets the task as completed."""
        self.completed = True

    def is_recurring(self) -> bool:
        """Returns True if this task repeats (i.e. frequency is not 'once')."""
        return self.frequency != "once"

    def next_occurrence(self) -> Optional["Task"]:
        """Returns a copy of this task scheduled for its next due date, or None if frequency is 'once'.
        Daily tasks advance by 1 day; weekly tasks advance by 7 days.
        The new task is unmarked (completed=False) and preserves all other fields.
        """
        if self.frequency == "once":
            return None
        current = date.fromisoformat(self.date)
        if self.frequency == "daily":
            next_date = current + timedelta(days=1)
        elif self.frequency == "weekly":
            next_date = current + timedelta(weeks=1)
        else:
            return None
        return Task(
            title=self.title,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            time=self.time,
            frequency=self.frequency,
            pet_name=self.pet_name,
            date=next_date.isoformat(),
        )


@dataclass
class Pet:
    """Stores a pet's details and its list of care tasks."""
    name: str
    species: str
    age: int = 0
    notes: str = ""
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Adds a task to this pet's task list and records which pet owns it."""
        task.pet_name = self.name
        self.tasks.append(task)

    def complete_task(self, task_title: str) -> None:
        """Marks a task complete. If it recurs, appends the next occurrence to this pet's tasks."""
        for task in self.tasks:
            if task.title == task_title and not task.completed:
                task.mark_complete()
                next_task = task.next_occurrence()
                if next_task is not None:
                    self.add_task(next_task)
                return

    def remove_task(self, task_title: str) -> None:
        """Removes the first task whose title matches the given string."""
        self.tasks = [t for t in self.tasks if t.title != task_title]

    def get_tasks(self) -> List[Task]:
        """Returns all tasks belonging to this pet."""
        return self.tasks


@dataclass
class Owner:
    """Manages a collection of pets and their tasks."""
    name: str
    preferences: dict = field(default_factory=dict)
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Adds a pet to the owner's pet list."""
        self.pets.append(pet)

    def get_pet(self, pet_name: str) -> Optional[Pet]:
        """Returns the pet with the given name, or None if not found."""
        for pet in self.pets:
            if pet.name == pet_name:
                return pet
        return None

    def get_all_tasks(self) -> List[Task]:
        """Collects and returns every task from every pet."""
        all_tasks = []
        for pet in self.pets:
            all_tasks.extend(pet.get_tasks())
        return all_tasks


class Scheduler:
    """Builds and explains daily schedules for a pet owner."""

    def build_daily_schedule(self, owner: Owner) -> List[Task]:
        """Gathers all tasks from the owner and returns them sorted by time."""
        all_tasks = owner.get_all_tasks()
        return self.sort_tasks_by_time(all_tasks)

    def sort_tasks_by_time(self, tasks: List[Task]) -> List[Task]:
        """Sorts tasks by 'HH:MM' time string (ascending).
        Tasks at the same time are ordered by priority: high first, then medium, then low.
        Any unrecognized priority value is placed last."""
        priority_order = {"high": 0, "medium": 1, "low": 2}

        def sort_key(task: Task):
            return (task.time, priority_order.get(task.priority, 99))

        return sorted(tasks, key=sort_key)

    def filter_tasks(
        self,
        tasks: List[Task],
        completed: Optional[bool] = None,
        pet_name: Optional[str] = None,
    ) -> List[Task]:
        """Returns a subset of tasks matching the given filters.
        Pass completed=True/False to filter by status, or pet_name to filter by pet.
        Both filters can be applied together; omitting a filter skips that check.
        """
        result = tasks
        if completed is not None:
            result = [t for t in result if t.completed == completed]
        if pet_name is not None:
            result = [t for t in result if t.pet_name == pet_name]
        return result

    def detect_conflicts(self, tasks: List[Task]) -> List[str]:
        """Checks every pair of tasks for overlapping time windows.
        Two tasks conflict when one starts before the other finishes.
        Returns a list of warning strings — empty if no conflicts exist.
        """
        def to_minutes(time_str: str) -> int:
            """Convert 'HH:MM' to total minutes since midnight."""
            h, m = time_str.split(":")
            return int(h) * 60 + int(m)

        warnings = []
        for i in range(len(tasks)):
            for j in range(i + 1, len(tasks)):
                a, b = tasks[i], tasks[j]
                a_start = to_minutes(a.time)
                a_end   = a_start + a.duration_minutes
                b_start = to_minutes(b.time)
                b_end   = b_start + b.duration_minutes
                # Overlap exists when each interval starts before the other ends
                if a_start < b_end and b_start < a_end:
                    warnings.append(
                        f"Conflict: '{a.title}' ({a.pet_name}, {a.time}, {a.duration_minutes} min)"
                        f" overlaps '{b.title}' ({b.pet_name}, {b.time}, {b.duration_minutes} min)"
                    )
        return warnings

    def find_next_available_slot(
        self, tasks: List[Task], duration_minutes: int,
        start_hour: int = 8, end_hour: int = 18,
    ) -> Optional[str]:
        """Scans the day from start_hour to end_hour and returns the first
        'HH:MM' time where a task of duration_minutes fits without overlapping
        any existing task.  Returns None if no slot is available.

        Tasks are checked in time order.  The search advances minute-by-minute
        only when blocked, so it always lands on the earliest possible opening.
        """
        day_start = start_hour * 60          # e.g. 480  (08:00)
        day_end   = end_hour   * 60          # e.g. 1080 (18:00)

        # Build a sorted list of (start, end) intervals from existing tasks
        busy = sorted(
            (int(h) * 60 + int(m), int(h) * 60 + int(m) + t.duration_minutes)
            for t in tasks
            for h, m in [t.time.split(":")]
        )

        candidate = day_start
        while candidate + duration_minutes <= day_end:
            candidate_end = candidate + duration_minutes
            # Find any busy block that overlaps this candidate window
            blocked_until = None
            for b_start, b_end in busy:
                if b_start < candidate_end and candidate < b_end:
                    blocked_until = b_end   # push past this block
                    break
            if blocked_until is None:
                return f"{candidate // 60:02d}:{candidate % 60:02d}"
            candidate = blocked_until       # jump to end of blocking task

        return None

    def explain_schedule(self, tasks: List[Task]) -> List[str]:
        """Returns a plain-English explanation for why each task is in the schedule."""
        explanations = []
        for task in tasks:
            pet_label = f"for {task.pet_name}" if task.pet_name else ""
            recurrence = f"repeats {task.frequency}" if task.is_recurring() else "one-time"
            status = "already done" if task.completed else "pending"
            line = (
                f"{task.time} — '{task.title}' {pet_label} "
                f"({task.priority} priority, {task.duration_minutes} min, {recurrence}, {status})"
            )
            explanations.append(line)
        return explanations
