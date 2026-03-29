from pawpal_system import Task, Pet, Owner, Scheduler


PRIORITY_LABEL = {"high": "🔴 high", "medium": "🟡 med ", "low": "🟢 low "}


def print_tasks(tasks, label=""):
    if label:
        print(f"\n  {label}")
    if not tasks:
        print("    (none)")
        return
    for t in tasks:
        status = "✓ done" if t.completed else "· todo"
        recur  = f"repeats {t.frequency}" if t.is_recurring() else "once"
        pri    = PRIORITY_LABEL.get(t.priority, t.priority)
        print(f"    {t.time}  {pri}  [{status}]  {t.title:<22}  {t.pet_name} — {recur}, {t.date}")


def main():
    scheduler = Scheduler()

    # ------------------------------------------------------------------ #
    # Setup
    # ------------------------------------------------------------------ #
    owner = Owner(name="Alex")

    mochi = Pet(name="Mochi", species="Dog", age=3)
    luna  = Pet(name="Luna",  species="Cat", age=5)

    # Tasks added deliberately out of chronological order
    mochi.add_task(Task(title="Evening Walk",    duration_minutes=30, priority="medium", time="18:00", frequency="daily", date="2026-03-29"))
    mochi.add_task(Task(title="Morning Walk",    duration_minutes=30, priority="high",   time="07:30", frequency="daily", date="2026-03-29"))
    mochi.add_task(Task(title="Midday Check",    duration_minutes=10, priority="low",    time="12:00",                    date="2026-03-29"))

    luna.add_task(Task(title="Feed Breakfast",   duration_minutes=5,  priority="high",   time="08:00",                    date="2026-03-29"))
    luna.add_task(Task(title="Vet Appointment",  duration_minutes=60, priority="high",   time="07:45", frequency="once",  date="2026-03-29"))
    luna.add_task(Task(title="Clean Litter",     duration_minutes=10, priority="medium", time="09:30", frequency="daily", date="2026-03-29"))

    owner.add_pet(mochi)
    owner.add_pet(luna)

    # ------------------------------------------------------------------ #
    # 1. Sorting
    # ------------------------------------------------------------------ #
    print("\n" + "=" * 55)
    print("1. SORTING — tasks printed in time order")
    print("=" * 55)
    print("   (added order: Evening Walk, Morning Walk, Midday Check,")
    print("    Feed Breakfast, Vet Appointment, Clean Litter)")

    schedule = scheduler.build_daily_schedule(owner)
    print_tasks(schedule, "Sorted schedule:")

    # ------------------------------------------------------------------ #
    # 2. Conflict detection  (run before any completions to keep it clean)
    # ------------------------------------------------------------------ #
    print("\n" + "=" * 55)
    print("2. CONFLICT DETECTION")
    print("=" * 55)
    print("   Morning Walk   07:30–08:00  (Mochi, 30 min)")
    print("   Vet Appointment 07:45–08:45  (Luna, 60 min)  ← overlaps Morning Walk")
    print("   Vet Appointment 07:45–08:45  (Luna, 60 min)  ← also overlaps Feed Breakfast at 08:00")

    conflicts = scheduler.detect_conflicts(schedule)
    print()
    if conflicts:
        for warning in conflicts:
            print(f"  ⚠  {warning}")
    else:
        print("  ✓  No conflicts found.")

    # ------------------------------------------------------------------ #
    # 3. Filtering
    # ------------------------------------------------------------------ #
    print("\n" + "=" * 55)
    print("3. FILTERING")
    print("=" * 55)

    # Mark one task done so status filtering is interesting
    mochi.complete_task("Morning Walk")

    all_tasks = scheduler.build_daily_schedule(owner)

    print_tasks(
        scheduler.filter_tasks(all_tasks, pet_name="Mochi"),
        "Filter by pet — Mochi only:",
    )
    print_tasks(
        scheduler.filter_tasks(all_tasks, pet_name="Luna"),
        "Filter by pet — Luna only:",
    )
    print_tasks(
        scheduler.filter_tasks(all_tasks, completed=True),
        "Filter by status — completed:",
    )
    print_tasks(
        scheduler.filter_tasks(all_tasks, completed=False, pet_name="Mochi"),
        "Filter by status + pet — Mochi, pending only:",
    )

    # ------------------------------------------------------------------ #
    # 4. Recurring tasks
    # ------------------------------------------------------------------ #
    print("\n" + "=" * 55)
    print("4. RECURRING TASKS")
    print("=" * 55)

    print("\nBefore completing 'Clean Litter' (daily):")
    print_tasks(luna.get_tasks())

    luna.complete_task("Clean Litter")

    print("\nAfter completing 'Clean Litter':")
    print("  → original marked DONE, next occurrence auto-created for 2026-03-30")
    print_tasks(luna.get_tasks())

    print()

    # ------------------------------------------------------------------ #
    # 5. Next available slot
    # ------------------------------------------------------------------ #
    print("\n" + "=" * 55)
    print("5. NEXT AVAILABLE SLOT")
    print("=" * 55)

    # Use the original schedule (before completing Morning Walk)
    original_schedule = scheduler.build_daily_schedule(owner)
    for mins in (20, 60, 90):
        slot = scheduler.find_next_available_slot(original_schedule, duration_minutes=mins)
        result = slot if slot else "no slot available"
        print(f"  {mins:>3}-min task → first open slot: {result}")

    print()


if __name__ == "__main__":
    main()
