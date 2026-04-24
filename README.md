# Paw AI Planner

Paw AI Planner is an AI-assisted pet care scheduling system built on top of the original PawPal+ project. Users can describe tasks in plain English, and the system converts those requests into structured scheduling actions, detects conflicts, suggests better times, and explains daily plans clearly.

## Overview

Paw AI Planner brings natural-language task creation to a deterministic pet care scheduler using local logic with no external AI API dependency. The assistant verifies required details, prevents overlapping bookings, recommends alternate time slots, and summarizes the daily plan in plain English.

## Original Project: PawPal+

PawPal+ was a rule-based Streamlit scheduler for pet owners that managed pets, tasks, priorities, and recurring care routines. Paw AI Planner extends that foundation with natural-language input and a lightweight explanation layer while keeping the scheduler backend as the source of truth.

## Key AI Features

- Natural-language task creation from requests like "Walk Mochi at 9 AM"
- Conflict detection that blocks overlapping tasks and explains the issue
- Next-available-time suggestions when a requested slot is unavailable
- Plain-English daily schedule explanations and request classification

## System Architecture

The system separates the AI interpretation layer from the deterministic scheduling backend:

- UI layer handles natural-language input and shows confirmations, warnings, and summaries
- AI planner interprets intent, extracts schedule fields, and checks for ambiguity
- Scheduler backend manages pets, tasks, recurrence, ordering, and conflict logic
- Guardrails validate pet names, required fields, and unsupported requests

![System Architecture](assets/system_architecture.png)

## Sample Interactions

1. Add a task:

```
User: "Walk Luna at 9 AM for 30 minutes"
System: "Task created! Walk for Luna at 09:00 (30 min, medium priority)"
```

2. Detect conflict and suggest a time:

```
User: "Schedule grooming for Max at 5 PM"
System: "Schedule conflict detected. Max feeding overlaps 17:00. The next available slot is at 17:30."
```

3. Explain schedule:

```
User: "Explain today's schedule"
System: "Your schedule for today: 09:00 — Walk (Luna, 30 min, medium priority). 14:00 — Medication (Mochi, 10 min, high priority)."
```

## Setup Instructions

```bash
git clone <repo-url>
cd applied-ai-system-project
python -m venv .venv
source .venv/bin/activate
# Windows users: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Reliability and Testing

- 120 passing tests across AI planner and scheduler behavior
- Automated regression testing validates changes against existing functionality
- Natural-language task parsing and ambiguity handling
- Conflict detection and next-available-slot suggestions
- Daily schedule generation and plain-English explanations
- Guardrails for missing fields, unsupported requests, and pet name matching

## Design Decisions / Tradeoffs

- Deterministic scheduler remains the source of truth for task ordering and conflict logic
- Natural-language requests are interpreted, but task creation only proceeds when required details are present
- Suggestions are offered, not auto-applied, to keep user control explicit
- Scope is intentionally narrow to focus on reliable scheduling rather than general pet-care advice

## Limitations

- Natural-language parsing supports task creation, not editing existing tasks
- Multi-pet requests are not currently supported; use separate requests per pet
- The app does not answer veterinary or nutritional advice
- Timeline and recurrence logic are limited to one-day planning and standard recurring patterns

## Demo

Loom walkthrough link: TODO
Screenshots are included in the repo.

## Reflection

Paw AI Planner demonstrates a practical AI interface layered on a reliable scheduler backend. The project prioritizes clear behavior, explainable output, and realistic guardrails over open-ended chatbot-style responses, making it suitable for a portfolio submission. It also reflects a careful balance between natural-language flexibility and reliable rule-based scheduling.
