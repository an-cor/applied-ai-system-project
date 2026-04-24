"""Tests for the AI planner natural-language parser."""

import pytest
from pawpal_system import Owner, Pet, Task, Scheduler
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

    def test_extract_pet_name_feed_luna_example(self, owner_with_pets):
        """Test pet name extraction for 'Feed Luna at 7 PM for 15 minutes'."""
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("Feed Luna at 7 PM for 15 minutes")
        assert result.success is True
        assert result.task.pet_name == "Luna"
        assert result.task.title == "Feed"

    def test_extract_pet_name_schedule_feeding_luna_example(self, owner_with_pets):
        """Test pet name extraction for 'Schedule feeding for Luna at 9:05 AM for 15 minutes'."""
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("Schedule feeding for Luna at 9:05 AM for 15 minutes")
        assert result.success is True
        assert result.task.pet_name == "Luna"
        assert result.task.title == "feeding"

    def test_extract_pet_name_give_medicine_luna_example(self, owner_with_pets):
        """Test pet name extraction for 'Give Luna medicine at 8 PM for 10 minutes, daily'."""
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("Give Luna medicine at 8 PM for 10 minutes, daily")
        assert result.success is True
        assert result.task.pet_name == "Luna"
        assert result.task.title == "medicine"

    def test_extract_pet_name_add_training_luna_example(self, owner_with_pets):
        """Test pet name extraction for 'Add training for Luna at 9 AM for 45 minutes'."""
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("Add training for Luna at 9 AM for 45 minutes")
        assert result.success is True
        assert result.task.pet_name == "Luna"
        assert result.task.title == "training"


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
        """Completely unrelated text should be rejected safely."""
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("What's the weather like today?")
        assert result.success is False
        assert result.task is None
        assert "Paw AI Planner only helps with scheduling" in result.clarification_message

    def test_unrelated_request_random_text(self, owner_with_pets):
        """Random gibberish should fail gracefully."""
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("xyz abc 123 qwerty asdf")
        assert result.success is False
        assert result.task is None
        assert len(result.missing_fields) > 0

    def test_unrelated_request_math_problem(self, owner_with_pets):
        """Math problem should be rejected."""
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("What is 2 + 2?")
        assert result.success is False
        assert "Paw AI Planner only helps with scheduling" in result.clarification_message

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

    def test_unsupported_medicine_dosage_request(self, owner_with_pets):
        """Medical advice request should return unsupported message."""
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("Should I change my dog's medicine dosage?")
        assert result.success is False
        assert result.task is None
        assert "Paw AI Planner only helps with scheduling" in result.clarification_message
        assert "veterinarian" in result.clarification_message

    def test_unsupported_food_request(self, owner_with_pets):
        """Nutrition advice request should return unsupported message."""
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("What food should I give Mochi?")
        assert result.success is False
        assert result.task is None
        assert "Paw AI Planner only helps with scheduling" in result.clarification_message

    def test_unsupported_medicine_request(self, owner_with_pets):
        """Medicine advice request should return unsupported message."""
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("What medicine should I give Luna?")
        assert result.success is False
        assert result.task is None
        assert "Paw AI Planner only helps with scheduling" in result.clarification_message


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

    def test_parse_conflict_with_suggestion_available(self, owner_with_pets):
        """When conflict exists and next slot is available, suggest the time."""
        mochi = owner_with_pets.get_pet("Mochi")
        mochi.add_task(Task(
            title="Morning Walk",
            duration_minutes=30,
            priority="high",
            time="09:00",
            pet_name="Mochi"
        ))
        
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("Feed Mochi at 09:00 for 20 minutes")  # Conflicts
        
        assert result.success is True
        assert result.conflict_detected is True
        assert len(result.conflicts) > 0
        assert result.suggested_time == "09:30"  # Next available after 09:00-09:30
        assert result.suggestion_message == "The next available slot is at 09:30."

    def test_parse_conflict_with_no_suggestion(self, owner_with_pets):
        """When conflict exists but no slot available, show no-slot message."""
        mochi = owner_with_pets.get_pet("Mochi")
        # Fill the day from 08:00 to 18:00
        mochi.add_task(Task(title="Task1", duration_minutes=60, time="08:00", pet_name="Mochi", priority="medium"))
        mochi.add_task(Task(title="Task2", duration_minutes=60, time="09:00", pet_name="Mochi", priority="medium"))
        mochi.add_task(Task(title="Task3", duration_minutes=60, time="10:00", pet_name="Mochi", priority="medium"))
        mochi.add_task(Task(title="Task4", duration_minutes=60, time="11:00", pet_name="Mochi", priority="medium"))
        mochi.add_task(Task(title="Task5", duration_minutes=60, time="12:00", pet_name="Mochi", priority="medium"))
        mochi.add_task(Task(title="Task6", duration_minutes=60, time="13:00", pet_name="Mochi", priority="medium"))
        mochi.add_task(Task(title="Task7", duration_minutes=60, time="14:00", pet_name="Mochi", priority="medium"))
        mochi.add_task(Task(title="Task8", duration_minutes=60, time="15:00", pet_name="Mochi", priority="medium"))
        mochi.add_task(Task(title="Task9", duration_minutes=60, time="16:00", pet_name="Mochi", priority="medium"))
        mochi.add_task(Task(title="Task10", duration_minutes=60, time="17:00", pet_name="Mochi", priority="medium"))  # 17:00-18:00
        
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("Groom Mochi at 08:00 for 30 minutes")  # Conflicts
        
        assert result.success is True
        assert result.conflict_detected is True
        assert len(result.conflicts) > 0
        assert result.suggested_time is None
        assert result.suggestion_message == "No available slots found for the rest of the day."

    def test_parse_no_conflict_no_suggestion(self, owner_with_pets):
        """When no conflict, no suggestion should be provided."""
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("Walk Mochi at 10:00 for 30 minutes")
        
        assert result.success is True
        assert result.conflict_detected is False
        assert result.suggested_time is None
        assert result.suggestion_message == ""

    def test_parse_failure_no_suggestion(self, owner_with_pets):
        """When parsing fails, no suggestion should be provided."""
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("Feed at 9 AM")  # Missing pet name
        
        assert result.success is False
        assert result.suggested_time is None
        assert result.suggestion_message == ""

    def test_suggested_time_does_not_overlap_existing_tasks(self, owner_with_pets):
        """Suggested time should not overlap with any existing task."""
        mochi = owner_with_pets.get_pet("Mochi")
        # Add tasks at specific times
        mochi.add_task(Task(
            title="Task A",
            duration_minutes=30,
            priority="medium",
            time="09:00",
            pet_name="Mochi"
        ))
        mochi.add_task(Task(
            title="Task B",
            duration_minutes=30,
            priority="medium",
            time="10:00",
            pet_name="Mochi"
        ))
        # Gap exists at 09:30-09:59 and 10:30+
        
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("Task C for Mochi at 09:00 for 20 minutes")  # Conflicts with Task A
        
        assert result.success is True
        assert result.conflict_detected is True
        assert result.suggested_time == "09:30"
        
        # Verify suggested time doesn't overlap with existing tasks by creating a task at suggested time
        suggested_task = Task(
            title=result.task.title,
            duration_minutes=result.task.duration_minutes,
            priority=result.task.priority,
            time=result.suggested_time,
            pet_name=result.task.pet_name
        )
        all_tasks = [suggested_task] + mochi.get_tasks()
        scheduler = Scheduler()
        conflicts_with_suggestion = scheduler.detect_conflicts(all_tasks)
        assert len(conflicts_with_suggestion) == 0, "Suggested time should not create new conflicts"

    def test_suggested_time_respects_requested_duration(self, owner_with_pets):
        """Suggested time should accommodate the full requested duration."""
        mochi = owner_with_pets.get_pet("Mochi")
        # Create a 30-min gap: 09:00-09:30 and 10:00-10:30
        mochi.add_task(Task(
            title="Morning Walk",
            duration_minutes=30,
            priority="high",
            time="09:00",
            pet_name="Mochi"
        ))
        mochi.add_task(Task(
            title="Afternoon Walk",
            duration_minutes=30,
            priority="high",
            time="10:00",
            pet_name="Mochi"
        ))
        
        planner = PawPalPlanner(owner_with_pets)
        # Request a 30-min slot starting at a conflict time
        result = planner.parse_request("Feed Mochi at 09:00 for 30 minutes")
        
        assert result.success is True
        assert result.conflict_detected is True
        assert result.suggested_time == "09:30"
        assert result.task.duration_minutes == 30
        
        # Verify that 09:30 + 30 minutes = 10:00, which should not overlap with Task at 10:00
        # (back-to-back is allowed)
        suggested_task = Task(
            title=result.task.title,
            duration_minutes=result.task.duration_minutes,
            priority=result.task.priority,
            time=result.suggested_time,
            pet_name=result.task.pet_name
        )
        all_tasks = [suggested_task] + mochi.get_tasks()
        scheduler = Scheduler()
        conflicts = scheduler.detect_conflicts(all_tasks)
        assert len(conflicts) == 0

    def test_suggested_time_near_day_cutoff(self, owner_with_pets):
        """Suggested time near day cutoff (18:00) should handle no-slot correctly."""
        mochi = owner_with_pets.get_pet("Mochi")
        # Fill schedule up to 17:00
        mochi.add_task(Task(
            title="Evening Task",
            duration_minutes=60,
            priority="medium",
            time="17:00",
            pet_name="Mochi"
        ))
        
        planner = PawPalPlanner(owner_with_pets)
        # Request a 30-min slot when only 0 min available before 18:00
        result = planner.parse_request("Late Task for Mochi at 17:00 for 30 minutes")
        
        assert result.success is True
        assert result.conflict_detected is True
        assert result.suggested_time is None  # No slot at or after 17:00 for 30 min
        assert result.suggestion_message == "No available slots found for the rest of the day."

    def test_suggested_time_with_multiple_conflicts(self, owner_with_pets):
        """Suggestion should skip over multiple conflicting tasks."""
        mochi = owner_with_pets.get_pet("Mochi")
        luna = owner_with_pets.get_pet("Luna")
        
        # Add multiple tasks blocking certain times
        mochi.add_task(Task(
            title="Walk",
            duration_minutes=30,
            priority="high",
            time="09:00",
            pet_name="Mochi"
        ))
        luna.add_task(Task(
            title="Vet Visit",
            duration_minutes=60,
            priority="high",
            time="09:30",
            pet_name="Luna"
        ))
        
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("Groom Mochi at 09:00 for 20 minutes")
        
        assert result.success is True
        assert result.conflict_detected is True
        # Should suggest a time after both conflicts
        assert result.suggested_time == "10:30"

    def test_parsing_failure_preserves_syntax_fields(self, owner_with_pets):
        """Parsing failure should have all syntax fields properly initialized."""
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("at 3 PM")  # Missing pet and task
        
        assert result.success is False
        assert result.task is None
        assert result.suggested_time is None
        assert result.suggestion_message == ""
        assert len(result.missing_fields) > 0
        assert len(result.clarification_message) > 0

    def test_functionality_1_parse_all_fields_unaffected(self, owner_with_pets):
        """Functionality 1: Parsing all required fields should work unchanged."""
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("Walk Mochi at 2:30 PM for 45 minutes, high priority, daily")
        
        assert result.success is True
        assert result.task is not None
        assert result.task.title == "Walk"
        assert result.task.pet_name == "Mochi"
        assert result.task.time == "14:30"
        assert result.task.duration_minutes == 45
        assert result.task.priority == "high"
        assert result.task.frequency == "daily"
        assert result.conflict_detected is False

    def test_functionality_2_conflict_detection_unaffected(self, owner_with_pets):
        """Functionality 2: Conflict detection should work unchanged."""
        mochi = owner_with_pets.get_pet("Mochi")
        mochi.add_task(Task(
            title="Existing Task",
            duration_minutes=30,
            priority="high",
            time="14:00",
            pet_name="Mochi"
        ))
        
        planner = PawPalPlanner(owner_with_pets)
        result = planner.parse_request("Competing Task for Mochi at 14:15 for 20 minutes")
        
        assert result.success is True
        assert result.conflict_detected is True
        assert len(result.conflicts) > 0
        assert "Existing Task" in result.conflicts[0]
        assert not result.task.pet_name or result.task.pet_name == "Mochi"


class TestRequestClassification:
    """Test request classification for Functionality 4 schedule explanation."""

    def test_classify_schedule_explanation_request_basic(self, owner_with_pets):
        """'Explain today's schedule' should classify as explain_schedule."""
        planner = PawPalPlanner(owner_with_pets)
        intent = planner.classify_request("Explain today's schedule")
        assert intent == "explain_schedule"

    def test_classify_schedule_explanation_what_schedule(self, owner_with_pets):
        """'What's my schedule today?' should classify as explain_schedule."""
        planner = PawPalPlanner(owner_with_pets)
        intent = planner.classify_request("What's my schedule today?")
        assert intent == "explain_schedule"

    def test_classify_schedule_explanation_summarize(self, owner_with_pets):
        """'Summarize the day' should classify as explain_schedule."""
        planner = PawPalPlanner(owner_with_pets)
        intent = planner.classify_request("Summarize the day")
        assert intent == "explain_schedule"

    def test_classify_schedule_explanation_show_plan(self, owner_with_pets):
        """'Show me my pet care plan for today' should classify as explain_schedule."""
        planner = PawPalPlanner(owner_with_pets)
        intent = planner.classify_request("Show me my pet care plan for today")
        assert intent == "explain_schedule"

    def test_classify_schedule_explanation_what_does(self, owner_with_pets):
        """'What does my schedule look like today?' should classify as explain_schedule."""
        planner = PawPalPlanner(owner_with_pets)
        intent = planner.classify_request("What does my schedule look like today?")
        assert intent == "explain_schedule"

    def test_classify_add_task_request_basic(self, owner_with_pets):
        """'Walk Mochi at 9 AM' should classify as add_task."""
        planner = PawPalPlanner(owner_with_pets)
        intent = planner.classify_request("Walk Mochi at 9 AM")
        assert intent == "add_task"

    def test_classify_add_task_with_specific_time(self, owner_with_pets):
        """Request with specific time like 'at 3 PM' should classify as add_task."""
        planner = PawPalPlanner(owner_with_pets)
        intent = planner.classify_request("Feed Luna at 3 PM")
        assert intent == "add_task"

    def test_classify_add_task_with_action_verb(self, owner_with_pets):
        """Request with action verb and pet should classify as add_task."""
        planner = PawPalPlanner(owner_with_pets)
        intent = planner.classify_request("Groom Mochi at 2 PM for 30 minutes")
        assert intent == "add_task"

    def test_classify_add_task_schedule_as_verb(self, owner_with_pets):
        """'Schedule a walk for Mochi at 4 PM' uses 'schedule' as action verb, not scope."""
        planner = PawPalPlanner(owner_with_pets)
        intent = planner.classify_request("Schedule a walk for Mochi at 4 PM")
        assert intent == "add_task"

    def test_classify_explanation_tell_me(self, owner_with_pets):
        """'Tell me about today's schedule' should classify as explain_schedule."""
        planner = PawPalPlanner(owner_with_pets)
        intent = planner.classify_request("Tell me about today's schedule")
        assert intent == "explain_schedule"

    def test_classify_explanation_recap(self, owner_with_pets):
        """'Can you recap my day?' should classify as explain_schedule."""
        planner = PawPalPlanner(owner_with_pets)
        intent = planner.classify_request("Can you recap my day?")
        assert intent == "explain_schedule"

    def test_classify_add_task_multiple_times_in_request(self, owner_with_pets):
        """Request with specific time should classify as add_task even without pet initially."""
        planner = PawPalPlanner(owner_with_pets)
        intent = planner.classify_request("at 10 AM")
        assert intent == "add_task"

    def test_classify_explain_schedule_no_specific_time(self, owner_with_pets):
        """'Explain my pet care plan today' with no specific time should explain."""
        planner = PawPalPlanner(owner_with_pets)
        intent = planner.classify_request("Explain my pet care plan today")
        assert intent == "explain_schedule"

    def test_classify_unsupported_weather_request(self, owner_with_pets):
        """'What is the weather today?' should classify as unsupported."""
        planner = PawPalPlanner(owner_with_pets)
        intent = planner.classify_request("What is the weather today?")
        assert intent == "unsupported"

    def test_classify_unsupported_food_request(self, owner_with_pets):
        """'What food should I give Mochi?' should classify as unsupported."""
        planner = PawPalPlanner(owner_with_pets)
        intent = planner.classify_request("What food should I give Mochi?")
        assert intent == "unsupported"

    def test_classify_unsupported_joke_request(self, owner_with_pets):
        """'Tell me a joke' should classify as unsupported."""
        planner = PawPalPlanner(owner_with_pets)
        intent = planner.classify_request("Tell me a joke")
        assert intent == "unsupported"

    def test_classify_unsupported_medicine_dosage(self, owner_with_pets):
        """'Should I change my dog's medicine dosage?' should classify as unsupported."""
        planner = PawPalPlanner(owner_with_pets)
        intent = planner.classify_request("Should I change my dog's medicine dosage?")
        assert intent == "unsupported"

    def test_classify_unsupported_food_for_mochi(self, owner_with_pets):
        """'What food should I give Mochi?' should classify as unsupported."""
        planner = PawPalPlanner(owner_with_pets)
        intent = planner.classify_request("What food should I give Mochi?")
        assert intent == "unsupported"

    def test_classify_unsupported_medicine_for_luna(self, owner_with_pets):
        """'What medicine should I give Luna?' should classify as unsupported."""
        planner = PawPalPlanner(owner_with_pets)
        intent = planner.classify_request("What medicine should I give Luna?")
        assert intent == "unsupported"


class TestScheduleExplanation:
    """Test schedule explanation generation for Functionality 4."""

    def test_explain_schedule_empty(self, owner_with_pets):
        """Empty schedule should return friendly message."""
        planner = PawPalPlanner(owner_with_pets)
        result = planner.explain_schedule()
        
        assert result.success is True
        assert result.is_empty is True
        assert result.task_count == 0
        assert "No tasks scheduled" in result.explanation or "clear" in result.explanation.lower()

    def test_explain_schedule_single_task(self, owner_with_pets):
        """Schedule with one task should include task details."""
        mochi = owner_with_pets.get_pet("Mochi")
        mochi.add_task(Task(
            title="Morning Walk",
            duration_minutes=30,
            priority="high",
            time="09:00",
            pet_name="Mochi"
        ))
        
        planner = PawPalPlanner(owner_with_pets)
        result = planner.explain_schedule()
        
        assert result.success is True
        assert result.is_empty is False
        assert result.task_count == 1
        assert "09:00" in result.explanation
        assert "Morning Walk" in result.explanation
        assert "Mochi" in result.explanation
        assert "30 min" in result.explanation
        assert "high" in result.explanation.lower()

    def test_explain_schedule_multiple_tasks_sorted(self, owner_with_pets):
        """Multiple tasks should be listed in time order."""
        mochi = owner_with_pets.get_pet("Mochi")
        luna = owner_with_pets.get_pet("Luna")
        
        mochi.add_task(Task(
            title="Walk",
            duration_minutes=30,
            priority="high",
            time="09:00",
            pet_name="Mochi"
        ))
        luna.add_task(Task(
            title="Feeding",
            duration_minutes=15,
            priority="medium",
            time="08:00",
            pet_name="Luna"
        ))
        mochi.add_task(Task(
            title="Groom",
            duration_minutes=45,
            priority="low",
            time="14:00",
            pet_name="Mochi"
        ))
        
        planner = PawPalPlanner(owner_with_pets)
        result = planner.explain_schedule()
        
        assert result.success is True
        assert result.task_count == 3
        
        lines = result.explanation.split("\n")
        explanation_text = result.explanation.lower()
        
        assert "08:00" in explanation_text
        assert "09:00" in explanation_text
        assert "14:00" in explanation_text
        
        idx_8 = result.explanation.find("08:00")
        idx_9 = result.explanation.find("09:00")
        idx_14 = result.explanation.find("14:00")
        
        assert idx_8 < idx_9 < idx_14

    def test_explain_schedule_shows_frequency(self, owner_with_pets):
        """Explanation should show recurring vs one-time tasks."""
        mochi = owner_with_pets.get_pet("Mochi")
        
        mochi.add_task(Task(
            title="Daily Walk",
            duration_minutes=30,
            priority="medium",
            time="09:00",
            frequency="daily",
            pet_name="Mochi"
        ))
        mochi.add_task(Task(
            title="One-time Groom",
            duration_minutes=45,
            priority="medium",
            time="14:00",
            frequency="once",
            pet_name="Mochi"
        ))
        
        planner = PawPalPlanner(owner_with_pets)
        result = planner.explain_schedule()
        
        assert result.success is True
        assert "repeats daily" in result.explanation.lower() or "daily" in result.explanation.lower()
        assert "one-time" in result.explanation.lower()

    def test_explain_schedule_shows_completion_status(self, owner_with_pets):
        """Explanation should show completion status of tasks."""
        mochi = owner_with_pets.get_pet("Mochi")
        
        task1 = Task(
            title="Walk",
            duration_minutes=30,
            priority="high",
            time="09:00",
            pet_name="Mochi"
        )
        task1.mark_complete()
        mochi.add_task(task1)
        
        mochi.add_task(Task(
            title="Feeding",
            duration_minutes=15,
            priority="medium",
            time="17:00",
            pet_name="Mochi"
        ))
        
        planner = PawPalPlanner(owner_with_pets)
        result = planner.explain_schedule()
        
        assert result.success is True
        assert "done" in result.explanation.lower()
        assert "pending" in result.explanation.lower()

    def test_explain_schedule_with_conflicts(self, owner_with_pets):
        """Explanation should include conflict warnings if present."""
        mochi = owner_with_pets.get_pet("Mochi")
        
        mochi.add_task(Task(
            title="Walk",
            duration_minutes=30,
            priority="high",
            time="09:00",
            pet_name="Mochi"
        ))
        mochi.add_task(Task(
            title="Feeding",
            duration_minutes=20,
            priority="medium",
            time="09:15",
            pet_name="Mochi"
        ))
        
        planner = PawPalPlanner(owner_with_pets)
        result = planner.explain_schedule()
        
        assert result.success is True
        assert len(result.conflict_warnings) > 0
        assert "conflict" in result.explanation.lower()

    def test_explain_schedule_no_conflicts_message(self, owner_with_pets):
        """Explanation should show 'no conflicts' message when schedule is clear."""
        mochi = owner_with_pets.get_pet("Mochi")
        
        mochi.add_task(Task(
            title="Walk",
            duration_minutes=30,
            priority="high",
            time="09:00",
            pet_name="Mochi"
        ))
        mochi.add_task(Task(
            title="Feeding",
            duration_minutes=15,
            priority="medium",
            time="10:00",
            pet_name="Mochi"
        ))
        
        planner = PawPalPlanner(owner_with_pets)
        result = planner.explain_schedule()
        
        assert result.success is True
        assert len(result.conflict_warnings) == 0
        assert "no conflicts" in result.explanation.lower()

    def test_explain_schedule_task_count_metadata(self, owner_with_pets):
        """ScheduleExplanationResult should include task count."""
        mochi = owner_with_pets.get_pet("Mochi")
        luna = owner_with_pets.get_pet("Luna")
        
        mochi.add_task(Task(title="Walk", duration_minutes=30, time="09:00", pet_name="Mochi", priority="medium"))
        luna.add_task(Task(title="Feed", duration_minutes=15, time="10:00", pet_name="Luna", priority="medium"))
        
        planner = PawPalPlanner(owner_with_pets)
        result = planner.explain_schedule()
        
        assert result.task_count == 2
        assert "2 tasks" in result.explanation.lower() or "2 task" in result.explanation.lower()
