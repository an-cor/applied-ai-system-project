import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler

PRIORITY_EMOJI = {"high": "🔴 High", "medium": "🟡 Medium", "low": "🟢 Low"}

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# Keep one Owner alive for the whole session
if "owner" not in st.session_state:
    st.session_state.owner = None

# ── Owner setup ──────────────────────────────────────────────────────────────
st.subheader("👤 Owner Info")
owner_name = st.text_input("Your name", value="Jordan")

if st.button("Set Owner"):
    st.session_state.owner = Owner(name=owner_name)
    st.success(f"Owner set: {owner_name}")

if st.session_state.owner is None:
    st.info("Enter your name and click 'Set Owner' to get started.")
    st.stop()

owner: Owner = st.session_state.owner

st.divider()

# ── Add a pet ────────────────────────────────────────────────────────────────
st.subheader("🐾 Add a Pet")
col1, col2 = st.columns(2)
with col1:
    pet_name = st.text_input("Pet name", value="Mochi")
with col2:
    species = st.selectbox("Species", ["dog", "cat", "bird", "other"])

if st.button("Add Pet"):
    if owner.get_pet(pet_name):
        st.warning(f"{pet_name} is already in your list.")
    else:
        owner.add_pet(Pet(name=pet_name, species=species))
        st.success(f"Added {pet_name} ({species})!")

if owner.pets:
    st.markdown("**Your pets:**")
    for pet in owner.pets:
        st.write(f"- {pet.name} ({pet.species})")
else:
    st.info("No pets yet — add one above.")
    st.stop()

st.divider()

# ── Add a task ───────────────────────────────────────────────────────────────
st.subheader("📋 Add a Task")

pet_names = [p.name for p in owner.pets]
selected_pet_name = st.selectbox("Select pet", pet_names)

col1, col2, col3 = st.columns(3)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
with col3:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

task_time = st.text_input("Time (HH:MM)", value="08:00")
frequency = st.selectbox("Frequency", ["once", "daily", "weekly"])

if st.button("Add Task"):
    pet = owner.get_pet(selected_pet_name)
    task = Task(
        title=task_title,
        duration_minutes=int(duration),
        priority=priority,
        time=task_time,
        frequency=frequency,
    )
    pet.add_task(task)
    st.success(f"Task '{task_title}' added to {selected_pet_name} at {task_time}.")

all_tasks = owner.get_all_tasks()
if all_tasks:
    st.markdown("**Current tasks:**")
    st.dataframe(
        [
            {
                "Pet": t.pet_name,
                "Task": t.title,
                "Time": t.time,
                "Min": t.duration_minutes,
                "Priority": PRIORITY_EMOJI.get(t.priority, t.priority),
                "Frequency": t.frequency,
            }
            for t in all_tasks
        ],
        use_container_width=True,
        hide_index=True,
        column_config={
            "Min": st.column_config.NumberColumn("Min", width="small"),
            "Time": st.column_config.TextColumn("Time", width="small"),
        },
    )
else:
    st.info("No tasks yet — add one above.")

st.divider()

# ── Generate schedule ─────────────────────────────────────────────────────────
st.subheader("🗓️ Build Schedule")

if st.button("Generate Schedule"):
    scheduler = Scheduler()
    schedule = scheduler.build_daily_schedule(owner)

    if not schedule:
        st.info("No tasks to schedule yet.")
    else:
        # Conflict warnings
        conflicts = scheduler.detect_conflicts(schedule)
        if conflicts:
            st.markdown("**⚠️ Schedule Conflicts Detected:**")
            for conflict in conflicts:
                st.warning(conflict)
        else:
            st.success("No conflicts detected — your schedule looks great!")

        # Schedule table
        st.markdown("**Your Schedule for Today:**")
        st.dataframe(
            [
                {
                    "Time": t.time,
                    "Pet": t.pet_name,
                    "Task": t.title,
                    "Min": t.duration_minutes,
                    "Priority": PRIORITY_EMOJI.get(t.priority, t.priority),
                    "Frequency": t.frequency.capitalize(),
                    "Status": "✅ Done" if t.completed else "🕐 Pending",
                }
                for t in schedule
            ],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Time": st.column_config.TextColumn("Time", width="small"),
                "Min": st.column_config.NumberColumn("Min", width="small"),
                "Status": st.column_config.TextColumn("Status", width="small"),
            },
        )

        # Plain-English breakdown
        with st.expander("📝 Schedule Breakdown"):
            for line in scheduler.explain_schedule(schedule):
                st.write(f"• {line}")
