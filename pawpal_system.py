from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Task:
    """Represents a pet care task."""
    title: str
    duration_minutes: int
    priority: str
    time: str
    frequency: str = "once"
    completed: bool = False

    def mark_complete(self) -> None:
        """Marks the task as complete."""
        pass

    def is_recurring(self) -> bool:
        """Returns whether the task repeats."""
        pass


@dataclass
class Pet:
    """Represents a pet and its care tasks."""
    name: str
    species: str
    age: int = 0
    notes: str = ""
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Adds a task to this pet."""
        pass

    def remove_task(self, task_title: str) -> None:
        """Removes a task by title."""
        pass

    def get_tasks(self) -> List[Task]:
        """Returns this pet's tasks."""
        pass


@dataclass
class Owner:
    """Represents a pet owner."""
    name: str
    preferences: dict = field(default_factory=dict)
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Adds a pet to the owner."""
        pass

    def get_pet(self, pet_name: str) -> Optional[Pet]:
        """Finds a pet by name."""
        pass

    def get_all_tasks(self) -> List[Task]:
        """Returns all tasks across all pets."""
        pass


class Scheduler:
    """Builds and explains schedules for pet care tasks."""

    def build_daily_schedule(self, owner: Owner) -> List[Task]:
        """Builds a daily schedule from the owner's pets and tasks."""
        pass

    def sort_tasks_by_time(self, tasks: List[Task]) -> List[Task]:
        """Sorts tasks by time."""
        pass

    def filter_tasks(
        self,
        tasks: List[Task],
        completed: Optional[bool] = None,
        pet_name: Optional[str] = None,
    ) -> List[Task]:
        """Filters tasks by selected criteria."""
        pass

    def detect_conflicts(self, tasks: List[Task]) -> List[str]:
        """Returns warnings for conflicting task times."""
        pass

    def explain_schedule(self, tasks: List[Task]) -> List[str]:
        """Explains why tasks appear in the generated schedule."""
        pass