"""Natural language task parser for PawPal+.

Converts plain-English task requests into structured Task objects.
Validates required fields and returns clarification messages if needed.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional
from pawpal_system import Task, Owner, Scheduler


@dataclass
class TaskCreationResult:
    """Represents the outcome of parsing a natural-language task request.
    
    Fields:
        success: True if parsing succeeded (regardless of conflicts).
        task: The parsed Task object if successful, None otherwise.
        missing_fields: List of fields that were missing (e.g., ['pet name', 'time']).
        clarification_message: Guidance message if parsing failed.
        conflict_detected: True if the parsed task conflicts with existing tasks.
        conflicts: List of conflict warning messages.
        suggested_time: Suggested alternative time if conflict exists and slot available.
        suggestion_message: Message explaining the suggestion or lack thereof.
    """
    success: bool
    task: Optional[Task] = None
    missing_fields: List[str] = None
    clarification_message: str = ""
    conflict_detected: bool = False
    conflicts: List[str] = field(default_factory=list)
    suggested_time: Optional[str] = None
    suggestion_message: str = ""

    def __post_init__(self):
        if self.missing_fields is None:
            self.missing_fields = []


@dataclass
class ScheduleExplanationResult:
    """Represents the outcome of a schedule explanation request.
    
    Fields:
        success: True if explanation generated successfully.
        explanation: Multi-line plain-English description of the schedule.
        is_empty: True if there are no tasks scheduled for today.
        task_count: Number of tasks in the schedule.
        conflict_warnings: List of conflict warning messages (empty if none).
        message: Additional guidance or metadata.
    """
    success: bool
    explanation: str = ""
    is_empty: bool = False
    task_count: int = 0
    conflict_warnings: List[str] = field(default_factory=list)
    message: str = ""


class PawPalPlanner:
    """Parses natural-language requests into structured task actions."""

    def __init__(self, owner: Owner):
        """Initialize with an owner to validate pet names.
        
        Args:
            owner: The Owner instance containing known pets.
        """
        self.owner = owner
        self.pet_names = [pet.name for pet in owner.pets]

    def classify_request(self, request: str) -> str:
        """Classify whether the request is for task creation, schedule explanation, or unsupported.
        
        Returns:
            "add_task" if request appears to be creating a new task.
            "explain_schedule" if request appears to be asking for a schedule explanation.
            "unsupported" if request appears to be asking for non-scheduling advice or information.
        
        Detection logic:
        - Explanation requests have: trigger words (explain, what, summary, etc.)
          AND schedule scope words (schedule, plan, agenda, tasks, pet care plan, day's plan, today's plan)
        - Unsupported requests have: trigger words AND no schedule scope words
        - Add-task requests have: a specific time (at 9 AM) AND/OR explicit action verbs
        """
        request_lower = request.lower()

        explanation_triggers = r"\b(?:explain|what|what's|what is|summary|summarize|recap|breakdown|tell me|tell|show|show me|describe|should|how)\b"
        schedule_scope = r"\b(?:schedule|plan|agenda|tasks|pet care plan|day's plan|today's plan|day)\b"
        task_action = r"\b(?:add|schedule|create|set|walk|feed|groom|give|play|bathe|brush|train|take)\b"
        specific_time = r"\bat\s+(?:\d{1,2}(?::\d{2})?\s*(?:am|pm)?|\d{1,2}:\d{2})"

        has_explanation_trigger = bool(re.search(explanation_triggers, request_lower))
        has_schedule_scope = bool(re.search(schedule_scope, request_lower))
        has_task_action = bool(re.search(task_action, request_lower))
        has_specific_time = bool(re.search(specific_time, request_lower))

        if has_explanation_trigger and has_schedule_scope:
            return "explain_schedule"

        if has_explanation_trigger and not has_schedule_scope:
            return "unsupported"

        if has_specific_time or (has_task_action and not has_explanation_trigger):
            return "add_task"

        return "add_task"

    def explain_schedule(self) -> ScheduleExplanationResult:
        """Generate a plain-English explanation of today's schedule.
        
        Returns:
            ScheduleExplanationResult with formatted explanation, task count, and conflict info.
        """
        scheduler = Scheduler()
        schedule = scheduler.build_daily_schedule(self.owner)

        if not schedule:
            return ScheduleExplanationResult(
                success=True,
                explanation="No tasks scheduled for today yet. Your day is clear!",
                is_empty=True,
                task_count=0,
            )

        conflict_warnings = scheduler.detect_conflicts(schedule)

        lines = ["Your schedule for today:", ""]

        for task in schedule:
            status = "done" if task.completed else "pending"
            recurrence = f"repeats {task.frequency}" if task.is_recurring() else "one-time"
            line = (
                f"{task.time} — {task.title} (for {task.pet_name}, "
                f"{task.duration_minutes} min, {task.priority} priority, {recurrence}, {status})"
            )
            lines.append(line)

        lines.append("")
        lines.append(f"Total: {len(schedule)} task{'s' if len(schedule) != 1 else ''}.")

        if conflict_warnings:
            lines.append("")
            lines.append("Conflicts detected:")
            for warning in conflict_warnings:
                lines.append(f"  - {warning}")
        else:
            lines.append("No conflicts detected.")

        explanation_text = "\n".join(lines)

        return ScheduleExplanationResult(
            success=True,
            explanation=explanation_text,
            is_empty=False,
            task_count=len(schedule),
            conflict_warnings=conflict_warnings,
        )

    def parse_request(self, request: str) -> TaskCreationResult:
        """Parse a natural-language task request into a Task or clarification.

        Args:
            request: Plain-English task description (e.g., "Walk Mochi at 9 AM for 30 minutes").

        Returns:
            TaskCreationResult with either a valid Task or clarification message.
        """
        if not request or not request.strip():
            return TaskCreationResult(
                success=False,
                missing_fields=["request"],
                clarification_message="Please describe a task. Example: 'Walk Mochi at 9 AM for 30 minutes'."
            )

        # Check request classification
        classification = self.classify_request(request)
        if classification == "explain_schedule":
            # This should be handled by explain_schedule(), not here
            return TaskCreationResult(
                success=False,
                clarification_message="Use the schedule explanation feature for schedule questions."
            )
        elif classification == "unsupported":
            return TaskCreationResult(
                success=False,
                clarification_message="Paw AI Planner only helps with scheduling pet care tasks. For medical, nutrition, or health advice, please consult a veterinarian."
            )

        # Extract fields from request
        pet_name = self._extract_pet_name(request)
        task_title = self._extract_task_title(request, pet_name)
        time_str = self._extract_time(request)
        duration = self._extract_duration(request)
        priority = self._extract_priority(request)
        frequency = self._extract_frequency(request)

        # Validate required fields
        missing = []
        if not pet_name:
            missing.append("pet name")
        if not task_title:
            missing.append("task title")
        if not time_str:
            missing.append("time (HH:MM format)")

        if missing:
            return TaskCreationResult(
                success=False,
                missing_fields=missing,
                clarification_message=self._build_clarification_message(
                    request, pet_name, task_title, time_str, duration, priority, missing
                )
            )

        # All required fields present — construct Task
        task = Task(
            title=task_title,
            duration_minutes=duration,
            priority=priority,
            time=time_str,
            frequency=frequency,
            pet_name=pet_name,
        )

        # Check for conflicts with existing tasks
        existing_tasks = self.owner.get_all_tasks()
        all_tasks = [task] + existing_tasks
        scheduler = Scheduler()
        conflict_warnings = scheduler.detect_conflicts(all_tasks)
        
        result = TaskCreationResult(success=True, task=task)
        if conflict_warnings:
            result.conflict_detected = True
            result.conflicts = conflict_warnings
            # Try to find next available slot starting from the requested time
            requested_hour = int(time_str.split(":")[0])
            next_slot = scheduler.find_next_available_slot(existing_tasks, task.duration_minutes, start_hour=requested_hour)
            if next_slot:
                result.suggested_time = next_slot
                result.suggestion_message = f"The next available slot is at {next_slot}."
            else:
                result.suggestion_message = "No available slots found for the rest of the day."
        
        return result

    def _extract_pet_name(self, request: str) -> Optional[str]:
        """Extract pet name by matching against known pets.
        
        Word-boundary match only (case-insensitive). Returns first match found.
        Matches pet name as a complete word: "Luna" matches "walk Luna at 9 AM"
        but not "Lunar eclipse".
        """
        request_lower = request.lower()
        for pet_name in self.pet_names:
            # Use word boundaries to match pet name as a complete word
            if re.search(rf"\b{re.escape(pet_name.lower())}\b", request_lower):
                return pet_name  # Return original case from owner's pet list
        return None

    def _extract_task_title(self, request: str, pet_name: Optional[str]) -> Optional[str]:
        """Extract task title from request, removing pet names and structured tokens.
        
        Strategy: Remove pet name, time patterns, duration patterns, and priority keywords.
        The remaining noun phrase is the task title.
        """
        if not request:
            return None

        text = request
        # Remove pet name if found
        if pet_name:
            text = re.sub(rf"\b{re.escape(pet_name)}\b", "", text, flags=re.IGNORECASE)

        # Remove time patterns (e.g., "at 9 AM", "at 9:00")
        text = re.sub(r"\bat\s+\d{1,2}(?::\d{2})?\s*(?:am|pm|AM|PM)?", "", text, flags=re.IGNORECASE)

        # Remove duration patterns (e.g., "for 30 minutes", "for 20 mins")
        text = re.sub(r"\bfor\s+\d+\s*(?:minute|min|hour|hr)s?", "", text, flags=re.IGNORECASE)

        # Remove priority keywords and surrounding prepositions
        priority_keywords = r"\b(?:with\s+)?(?:high|medium|low|priority|urgent|asap|routine)\b"
        text = re.sub(priority_keywords, "", text, flags=re.IGNORECASE)

        # Remove action verbs like "add", "schedule", "give"
        text = re.sub(r"\b(?:add|schedule|give|create|set)\b", "", text, flags=re.IGNORECASE)

        # Remove frequency keywords (tomorrow, daily, weekly, etc.)
        frequency_keywords = r"\b(?:tomorrow|today|daily|weekly|every\s+day)\b"
        text = re.sub(frequency_keywords, "", text, flags=re.IGNORECASE)

        # Remove common prepositions (for, with, from, to) that might linger
        text = re.sub(r"\b(?:for|with|from|to)\b", "", text, flags=re.IGNORECASE)

        # Clean up extra punctuation and commas
        text = re.sub(r"[,\s]+", " ", text)  # Replace commas and multiple spaces with single space

        # Clean up whitespace and convert to title case
        text = " ".join(text.split())
        text = text.strip()

        return text if text else None

    def _extract_time(self, request: str) -> Optional[str]:
        """Extract time in HH:MM format.
        
        Recognizes: "at 9 AM", "at 09:00", "at 3:30 PM", "at 15:30"
        Returns time in 24-hour HH:MM format.
        """
        # Pattern 1 (Priority): "at HH:MM AM/PM" or "at H:MM AM/PM" (e.g., "at 3:30 PM")
        match = re.search(r"\bat\s+(\d{1,2}):(\d{2})\s*(am|pm)", request, re.IGNORECASE)
        if match:
            hour, minute, meridiem = int(match.group(1)), int(match.group(2)), match.group(3).lower()
            if meridiem == "pm" and hour != 12:
                hour += 12
            elif meridiem == "am" and hour == 12:
                hour = 0
            return f"{hour:02d}:{minute:02d}"

        # Pattern 2: "at H AM/PM" or "at HH AM/PM"
        match = re.search(r"\bat\s+(\d{1,2})\s*(am|pm)", request, re.IGNORECASE)
        if match:
            hour, meridiem = int(match.group(1)), match.group(2).lower()
            if meridiem == "pm" and hour != 12:
                hour += 12
            elif meridiem == "am" and hour == 12:
                hour = 0
            return f"{hour:02d}:00"

        # Pattern 3: "at HH:MM" or "at H:MM" (24-hour format)
        match = re.search(r"\bat\s+(\d{1,2}):(\d{2})(?!\s*(?:am|pm))", request, re.IGNORECASE)
        if match:
            hour, minute = int(match.group(1)), int(match.group(2))
            return f"{hour:02d}:{minute:02d}"

        return None

    def _extract_duration(self, request: str) -> int:
        """Extract duration in minutes.
        
        Recognizes: "for 30 minutes", "for 20 mins", "for 1 hour", "for 2 hrs"
        Defaults to 30 minutes if not found.
        """
        # Pattern: "for N minute(s) / min(s) / hour(s) / hr(s)"
        match = re.search(r"\bfor\s+(\d+)\s*(?:minute|min|hour|hr)s?", request, re.IGNORECASE)
        if match:
            value = int(match.group(1))
            # Check if it's hours
            if "hour" in request[match.start():match.end()].lower() or \
               "hr" in request[match.start():match.end()].lower():
                return value * 60
            return value

        return 30  # Default: 30 minutes

    def _extract_priority(self, request: str) -> str:
        """Extract priority level from request keywords.
        
        Recognizes: "high", "urgent", "asap" → "high"
                   "low", "routine" → "low"
                   Default: "medium"
        """
        request_lower = request.lower()

        if re.search(r"\b(?:high|urgent|asap|immediately)\b", request_lower):
            return "high"
        elif re.search(r"\b(?:low|routine|whenever)\b", request_lower):
            return "low"
        else:
            return "medium"

    def _extract_frequency(self, request: str) -> str:
        """Extract frequency/recurrence from request keywords.
        
        Recognizes: "daily", "every day" → "daily"
                   "weekly", "every week" → "weekly"
                   Default: "once"
        """
        request_lower = request.lower()

        if re.search(r"\b(?:daily|every\s+day|each\s+day)\b", request_lower):
            return "daily"
        elif re.search(r"\b(?:weekly|every\s+week)\b", request_lower):
            return "weekly"
        else:
            return "once"

    def _build_clarification_message(
        self,
        request: str,
        pet_name: Optional[str],
        task_title: Optional[str],
        time_str: Optional[str],
        duration: int,
        priority: str,
        missing: List[str],
    ) -> str:
        """Build a friendly clarification message for missing or unclear fields."""
        understood = []
        if pet_name:
            understood.append(f"pet={pet_name}")
        if task_title:
            understood.append(f"task={task_title}")
        if time_str:
            understood.append(f"time={time_str}")
        if duration != 30:
            understood.append(f"duration={duration}min")
        if priority != "medium":
            understood.append(f"priority={priority}")

        understood_str = ", ".join(understood) if understood else "nothing"
        missing_str = ", ".join(missing)

        msg = f"I understood: {understood_str}\n\n"
        msg += f"I need: {missing_str}\n\n"
        msg += "Example: 'Walk Mochi at 9 AM for 30 minutes, high priority'"

        return msg
