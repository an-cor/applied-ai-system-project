"""Tests for the AI planner natural-language parser."""

import pytest
from pawpal_system import Owner, Pet, Task
from ai_planner import PawPalPlanner, TaskCreationResult


@pytest.fixture
def owner_with_pets():
    """Create an owner with two pets for testing."""
    owner = Owner(name="Jordan")
    owner.add_pet(Pet(name="Mochi", species="dog"))
    owner.add_pet(Pet(name="Luna", species="cat"))
    return owner


class TestPetNameExtraction:
    """Test pet name extraction from requests."""

    def test_extract_pet_name_exact_match(self, owner_with_pets):
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("Walk Mochi at 9 AM")
        assert result.task.pet_name == "Mochi"

    def test_extract_pet_name_case_insensitive(self, owner_with_pets):
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("walk mochi at 9 AM")
        assert result.task.pet_name == "Mochi"

    def test_extract_pet_name_missing_returns_error(self, owner_with_pets):
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("Walk the dog at 9 AM")
        assert result.success is False
        assert "pet name" in result.missing_fields

    def test_extract_different_pet(self, owner_with_pets):
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("Give Luna medicine at 8 PM")
        assert result.task.pet_name == "Luna"

    def test_extract_pet_name_word_boundary_not_substring(self, owner_with_pets):
        """Pet name should NOT match as substring of another word."""
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("The Lunar eclipse at 9 AM")
        # "Luna" is substring of "Lunar", but should not match without word boundary
        assert result.success is False
        assert "pet name" in result.missing_fields

    def test_extract_pet_name_word_boundary_short_name(self):
        """Short pet names should use word boundaries to avoid false positives."""
        owner = Owner(name="Test")
        owner.add_pet(Pet(name="Mo", species="dog"))
        planner = PawPalPlanner(owner)
        
        # "Mo" in "Mogul" should not match
        result = planner.parse_request("Feed the Mogul at 9 AM")
        assert result.success is False
        assert "pet name" in result.missing_fields
        
        # "Mo" as standalone word should match
        result2 = planner.parse_request("Feed Mo at 9 AM")
        assert result2.success is True
        assert result2.task.pet_name == "Mo"

    def test_extract_pet_name_in_sentence(self, owner_with_pets):
        """Pet name should match when used naturally in sentence."""
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("I need to take Mochi for a walk at 3 PM")
        assert result.task.pet_name == "Mochi"

    def test_extract_pet_name_multiple_pets_first_match(self, owner_with_pets):
        """When multiple pet names mentioned, first one found should be used."""
        planner = PawPalPlanner(owner_with_pets)
        # Create owner with distinct pets in known order
        owner = Owner(name="Test")
        owner.add_pet(Pet(name="Alpha", species="dog"))
        owner.add_pet(Pet(name="Beta", species="cat"))
        planner = PawPalPlanner(owner)
        
        result = planner.parse_request("Walk Alpha and feed Beta at 9 AM")
        # Should match first pet found (Alpha appears first in text)
        assert result.task.pet_name == "Alpha"


class TestTimeExtraction:
    """Test time extraction in various formats."""

    def test_extract_time_24_hour_format(self, owner_with_pets):
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("Walk Mochi at 09:00")
        assert result.task.time == "09:00"

    def test_extract_time_12_hour_am(self, owner_with_pets):
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("Walk Mochi at 9 AM")
        assert result.task.time == "09:00"

    def test_extract_time_12_hour_pm(self, owner_with_pets):
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("Walk Mochi at 5 PM")
        assert result.task.time == "17:00"

    def test_extract_time_with_minutes_am(self, owner_with_pets):
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("Walk Mochi at 9:30 AM")
        assert result.task.time == "09:30"

    def test_extract_time_with_minutes_pm(self, owner_with_pets):
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("Walk Mochi at 3:45 PM")
        assert result.task.time == "15:45"

    def test_extract_time_noon(self, owner_with_pets):
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("Feed Mochi at 12 PM")
        assert result.task.time == "12:00"

    def test_extract_time_midnight(self, owner_with_pets):
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("Feed Mochi at 12 AM")
        assert result.task.time == "00:00"

    def test_extract_time_missing_returns_error(self, owner_with_pets):
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("Walk Mochi for 30 minutes")
        assert result.success is False
        assert any("time" in field for field in result.missing_fields)


class TestTaskTitleExtraction:
    """Test task title extraction."""

    def test_extract_simple_title(self, owner_with_pets):
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("Walk Mochi at 9 AM")
        assert result.task.title == "Walk"

    def test_extract_multi_word_title(self, owner_with_pets):
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("Take Mochi for a walk at 9 AM")
        assert "walk" in result.task.title.lower()

    def test_extract_title_with_medicine(self, owner_with_pets):
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("Give Mochi medicine at 8 PM")
        assert "medicine" in result.task.title.lower()

    def test_extract_title_missing_returns_error(self, owner_with_pets):
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("Mochi at 9 AM for 30 minutes")
        assert result.success is False
        assert "task title" in result.missing_fields

    def test_extract_title_removes_scheduling_words(self, owner_with_pets):
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("Schedule feeding for Mochi at 7 AM")
        # "Schedule" and "for" should be removed; "feeding" should remain
        assert "feeding" in result.task.title.lower()
        assert "schedule" not in result.task.title.lower()


class TestDurationExtraction:
    """Test duration extraction with defaults."""

    def test_extract_duration_minutes(self, owner_with_pets):
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("Walk Mochi at 9 AM for 20 minutes")
        assert result.task.duration_minutes == 20

    def test_extract_duration_mins_short(self, owner_with_pets):
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("Walk Mochi at 9 AM for 20 mins")
        assert result.task.duration_minutes == 20

    def test_extract_duration_hours(self, owner_with_pets):
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("Walk Mochi at 9 AM for 1 hour")
        assert result.task.duration_minutes == 60

    def test_extract_duration_hours_short(self, owner_with_pets):
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("Walk Mochi at 9 AM for 2 hrs")
        assert result.task.duration_minutes == 120

    def test_extract_duration_default_when_missing(self, owner_with_pets):
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("Walk Mochi at 9 AM")
        assert result.task.duration_minutes == 30

    def test_extract_duration_zero_default_not_inferred(self, owner_with_pets):
        """Duration extraction should not fail; it defaults to 30."""
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("Walk Mochi at 9 AM")
        assert result.success is True
        assert result.task.duration_minutes == 30


class TestPriorityExtraction:
    """Test priority inference from keywords."""

    def test_extract_priority_high_keyword(self, owner_with_pets):
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("Walk Mochi at 9 AM high priority")
        assert result.task.priority == "high"

    def test_extract_priority_urgent_keyword(self, owner_with_pets):
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("Give Mochi medicine at 8 PM urgent")
        assert result.task.priority == "high"

    def test_extract_priority_asap_keyword(self, owner_with_pets):
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("Feed Mochi ASAP at 7 AM")
        assert result.task.priority == "high"

    def test_extract_priority_low_keyword(self, owner_with_pets):
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("Groom Luna at 10 AM low priority")
        assert result.task.priority == "low"

    def test_extract_priority_routine_keyword(self, owner_with_pets):
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("Play with Mochi at 4 PM routine")
        assert result.task.priority == "low"

    def test_extract_priority_default_medium(self, owner_with_pets):
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("Walk Mochi at 9 AM")
        assert result.task.priority == "medium"


class TestFrequencyExtraction:
    """Test frequency/recurrence extraction."""

    def test_extract_frequency_daily(self, owner_with_pets):
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("Walk Mochi at 9 AM daily")
        assert result.task.frequency == "daily"

    def test_extract_frequency_every_day(self, owner_with_pets):
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("Walk Mochi at 9 AM every day")
        assert result.task.frequency == "daily"

    def test_extract_frequency_weekly(self, owner_with_pets):
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("Groom Mochi at 10 AM weekly")
        assert result.task.frequency == "weekly"

    def test_extract_frequency_every_week(self, owner_with_pets):
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("Groom Mochi at 10 AM every week")
        assert result.task.frequency == "weekly"

    def test_extract_frequency_default_once(self, owner_with_pets):
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("Walk Mochi at 9 AM")
        assert result.task.frequency == "once"


class TestClarificationMessages:
    """Test clarification message generation."""

    def test_clarification_missing_pet_name(self, owner_with_pets):
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("Walk at 9 AM")
        assert result.success is False
        assert "pet name" in result.clarification_message.lower()
        assert "Example:" in result.clarification_message

    def test_clarification_missing_time(self, owner_with_pets):
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("Walk Mochi for 30 minutes")
        assert result.success is False
        assert "time" in result.clarification_message.lower()
        assert "pet=Mochi" in result.clarification_message

    def test_clarification_missing_multiple_fields(self, owner_with_pets):
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("Walk for 30 minutes")
        assert result.success is False
        assert len(result.missing_fields) >= 2

    def test_clarification_empty_request(self, owner_with_pets):
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("")
        assert result.success is False
        assert "Please describe a task" in result.clarification_message


class TestComplexRequests:
    """Test parsing of realistic complex requests."""

    def test_full_request_all_fields(self, owner_with_pets):
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("Give Mochi medicine at 8 PM for 5 minutes, high priority, daily")
        assert result.success is True
        assert result.task.pet_name == "Mochi"
        assert result.task.title == "medicine"
        assert result.task.time == "20:00"
        assert result.task.duration_minutes == 5
        assert result.task.priority == "high"
        assert result.task.frequency == "daily"

    def test_full_request_minimal_fields(self, owner_with_pets):
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("Walk Mochi at 9 AM")
        assert result.success is True
        assert result.task.pet_name == "Mochi"
        assert result.task.time == "09:00"
        assert result.task.duration_minutes == 30  # default
        assert result.task.priority == "medium"  # default
        assert result.task.frequency == "once"  # default

    def test_request_natural_language_sentence(self, owner_with_pets):
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("I need to walk Luna tomorrow at 3:30 PM for 45 minutes")
        assert result.success is True
        assert result.task.pet_name == "Luna"
        assert result.task.time == "15:30"
        assert result.task.duration_minutes == 45

    def test_request_conversational(self, owner_with_pets):
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("Schedule feeding for Luna at 7 AM with high priority")
        assert result.success is True
        assert result.task.pet_name == "Luna"
        assert result.task.title == "feeding"
        assert result.task.time == "07:00"
        assert result.task.priority == "high"

    def test_request_with_extra_text(self, owner_with_pets):
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("Please remember to give Mochi medicine at 8 PM, it's urgent!")
        assert result.success is True
        assert result.task.pet_name == "Mochi"
        assert result.task.priority == "high"  # "urgent" detected


class TestTaskCreationResult:
    """Test the TaskCreationResult dataclass."""

    def test_result_success_has_task(self, owner_with_pets):
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("Walk Mochi at 9 AM")
        assert result.success is True
        assert result.task is not None
        assert result.missing_fields == []
        assert result.clarification_message == ""

    def test_result_failure_has_clarification(self, owner_with_pets):
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("Walk at 9 AM")
        assert result.success is False
        assert result.task is None
        assert len(result.missing_fields) > 0
        assert len(result.clarification_message) > 0


class TestUnsupportedRequests:
    """Test handling of unrelated or unsupported requests."""

    def test_unrelated_request_no_pet_or_time(self, owner_with_pets):
        """Completely unrelated text should be rejected safely (missing required fields)."""
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("What's the weather like today?")
        assert result.success is False
        assert result.task is None
        assert "pet name" in result.clarification_message.lower() or "time" in result.clarification_message.lower()

    def test_unrelated_request_random_text(self, owner_with_pets):
        """Random gibberish should fail gracefully."""
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("xyz abc 123 qwerty asdf")
        assert result.success is False
        assert result.task is None
        assert len(result.missing_fields) > 0

    def test_unrelated_request_math_problem(self, owner_with_pets):
        """Math problem should be rejected (missing pet and time)."""
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("What is 2 + 2?")
        assert result.success is False
        assert "pet name" in result.clarification_message.lower() or "time" in result.clarification_message.lower()

    def test_unrelated_request_movie_quote(self, owner_with_pets):
        """Movie quote should be rejected (missing required fields)."""
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("May the Force be with you")
        assert result.success is False
        assert result.task is None

    def test_request_with_time_but_no_pet_or_title(self, owner_with_pets):
        """Request with only time should still fail (missing pet and title)."""
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("At 3 PM")
        assert result.success is False
        assert "pet name" in result.missing_fields or "pet" in result.clarification_message.lower()

    def test_request_with_pet_but_no_time(self, owner_with_pets):
        """Request mentioning pet but no time should return clarification."""
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("Mochi needs a walk")
        assert result.success is False
        assert any("time" in field.lower() for field in result.missing_fields)

    def test_whitespace_only_request(self, owner_with_pets):
        """Whitespace-only request should fail gracefully."""
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("   ")
        assert result.success is False
        assert result.task is None
        assert "Please describe a task" in result.clarification_message


class TestIntegrationWithPawPal:
    """Test integration between AI planner and PawPal+ system."""

    def test_parsed_task_can_be_added_to_pet(self, owner_with_pets):
        """Parsed Task should be compatible with Pet.add_task()."""
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("Walk Mochi at 9 AM for 30 minutes with high priority")
        
        assert result.success is True
        pet = owner_with_pets.get_pet("Mochi")
        pet.add_task(result.task)
        
        # Verify task was added correctly
        tasks = pet.get_tasks()
        assert len(tasks) == 1
        assert tasks[0].title == "Walk"
        assert tasks[0].time == "09:00"
        assert tasks[0].priority == "high"

    def test_multiple_tasks_from_natural_language(self, owner_with_pets):
        """Multiple natural-language requests should create multiple tasks."""
        planner = PawPalPlanner(owner_with_pets)
        
        requests = [
            "Walk Mochi at 9 AM",
            "Feed Luna at 7 AM",
            "Groom Mochi at 2 PM with low priority",
        ]
        
        tasks = []
        for req in requests:
            result = planner.parse_request(req)
            assert result.success is True
            tasks.append(result.task)
        
        # Add all parsed tasks to the system
        mochi_pet = owner_with_pets.get_pet("Mochi")
        luna_pet = owner_with_pets.get_pet("Luna")
        
        for task in tasks:
            if task.pet_name == "Mochi":
                mochi_pet.add_task(task)
            else:
                luna_pet.add_task(task)
        
        # Verify all tasks were added
        all_tasks = owner_with_pets.get_all_tasks()
        assert len(all_tasks) == 3

    def test_parsed_task_works_with_scheduler(self, owner_with_pets):
        """Parsed Task should work correctly with Scheduler.build_daily_schedule()."""
        from pawpal_system import Scheduler
        
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("Walk Mochi at 9 AM for 30 minutes")
        
        assert result.success is True
        mochi = owner_with_pets.get_pet("Mochi")
        mochi.add_task(result.task)
        
        scheduler = Scheduler()
        schedule = scheduler.build_daily_schedule(owner_with_pets)
        
        assert len(schedule) == 1
        assert schedule[0].title == "Walk"
        assert schedule[0].time == "09:00"


class TestConflictDetectionDuringParsing:
    """Test conflict detection when parsing natural-language task requests."""

    def test_parse_detects_conflict_with_existing_task(self, owner_with_pets):
        """New task that overlaps with existing task should be marked as conflicting."""
        mochi = owner_with_pets.get_pet("Mochi")
        mochi.add_task(Task(
            title="Morning Walk",
            duration_minutes=30,
            priority="high",
            time="09:00",
            pet_name="Mochi"
        ))
        
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("Feed Mochi at 09:15 for 20 minutes")
        
        assert result.success is True
        assert result.task is not None
        assert result.conflict_detected is True
        assert len(result.conflicts) > 0
        assert "Morning Walk" in result.conflicts[0]
        assert "Feed" in result.conflicts[0]

    def test_parse_no_conflict_when_times_separate(self, owner_with_pets):
        """New task at different time should not conflict."""
        mochi = owner_with_pets.get_pet("Mochi")
        mochi.add_task(Task(
            title="Morning Walk",
            duration_minutes=30,
            priority="high",
            time="09:00",
            pet_name="Mochi"
        ))
        
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("Feed Mochi at 10:00 for 20 minutes")
        
        assert result.success is True
        assert result.task is not None
        assert result.conflict_detected is False
        assert len(result.conflicts) == 0

    def test_parse_detects_multiple_conflicts(self, owner_with_pets):
        """New task that conflicts with multiple existing tasks should report all conflicts."""
        mochi = owner_with_pets.get_pet("Mochi")
        mochi.add_task(Task(
            title="Morning Walk",
            duration_minutes=30,
            priority="high",
            time="09:00",
            pet_name="Mochi"
        ))
        luna = owner_with_pets.get_pet("Luna")
        luna.add_task(Task(
            title="Cat Feeding",
            duration_minutes=10,
            priority="high",
            time="09:20",
            pet_name="Luna"
        ))
        
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("Groom Mochi at 09:15 for 30 minutes")
        
        assert result.success is True
        assert result.conflict_detected is True
        assert len(result.conflicts) >= 2

    def test_parse_conflicts_across_different_pets(self, owner_with_pets):
        """Conflicts should be detected across different pets (all tasks share time space)."""
        mochi = owner_with_pets.get_pet("Mochi")
        mochi.add_task(Task(
            title="Walk",
            duration_minutes=30,
            priority="high",
            time="09:00",
            pet_name="Mochi"
        ))
        luna = owner_with_pets.get_pet("Luna")
        luna.add_task(Task(
            title="Vet Appointment",
            duration_minutes=60,
            priority="high",
            time="08:45",
            pet_name="Luna"
        ))
        
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("Feed Mochi at 09:10 for 20 minutes")
        
        assert result.success is True
        assert result.conflict_detected is True
        assert len(result.conflicts) > 0

    def test_parse_failure_no_conflict_check(self, owner_with_pets):
        """If parsing fails, conflict_detected should remain False (no check performed)."""
        mochi = owner_with_pets.get_pet("Mochi")
        mochi.add_task(Task(
            title="Morning Walk",
            duration_minutes=30,
            priority="high",
            time="09:00",
            pet_name="Mochi"
        ))
        
        planner = PawPalPlanner(owner_with_pets)
        # Missing time — parse should fail
        result = planner.parse_request("Walk Mochi for 30 minutes")
        
        assert result.success is False
        assert result.task is None
        assert result.conflict_detected is False
        assert len(result.conflicts) == 0

    def test_parse_no_conflict_back_to_back_tasks(self, owner_with_pets):
        """Back-to-back tasks (one ends when other starts) should not conflict."""
        mochi = owner_with_pets.get_pet("Mochi")
        mochi.add_task(Task(
            title="Morning Walk",
            duration_minutes=30,
            priority="high",
            time="09:00",
            pet_name="Mochi"
        ))
        
        planner = PawPalPlanner(owner_with_pets)
        # Starts exactly when previous task ends
        result = planner.parse_request("Feed Mochi at 09:30 for 20 minutes")
        
        assert result.success is True
        assert result.task is not None
        assert result.conflict_detected is False
        assert len(result.conflicts) == 0

    def test_parse_conflict_fields_initialized_on_success_no_conflict(self, owner_with_pets):
        """When parsing succeeds with no conflict, conflict fields should be explicitly False/empty."""
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("Walk Mochi at 09:00 for 30 minutes")
        
        assert result.success is True
        assert result.conflict_detected is False
        assert result.conflicts == []
