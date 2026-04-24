# Model Card — Paw AI Planner

## Model Name
Paw AI Planner

## Project Type
Deterministic AI-assisted pet care scheduler built on top of PawPal+.

## Intended Users
Pet owners, caregivers, and students learning rule-based planning systems.

## Primary Use Cases
- Create pet care tasks from natural language.
- Detect scheduling conflicts.
- Suggest better task times.
- Explain proposed schedules.
- Clarify vague requests instead of guessing.
- Guard against unsupported requests.

## How It Works
Paw AI Planner uses deterministic local logic and pattern-based parsing to interpret user requests. It applies rule-based scheduling, conflict detection, and clarification flows without calling any external AI API.

## Data / Inputs
- Natural-language pet care requests.
- Task metadata such as time windows and priorities.
- Existing schedule items.

## Outputs
- Structured pet care tasks.
- Proposed schedule slots.
- Conflict warnings.
- Clarification prompts for vague requests.
- Unsupported request responses.

## Evaluation
The system is tested with 120 automated tests covering parsing, schedule generation, conflict detection, clarification handling, unsupported request guardrails, and regression testing for new features.

## Strengths
- Clear rule-based behavior with no external AI dependency.
- Predictable scheduling logic.
- Explicit clarification for vague requests.
- Support for guardrails around unsupported veterinary or nutrition advice.

## Limitations
- Not a trained foundation model; it is deterministic and local.
- No multi-pet parsing.
- No natural-language editing of existing tasks.
- Focused on one-day planning rather than long-term schedules.
- Pattern-based parsing may favor English phrasing.

## Risks / Misuse Considerations
- Should not be relied on for medical or nutrition advice.
- Users should verify schedule suggestions before applying them.
- Unsupported requests are blocked to reduce unsafe guidance.

## Fairness / Bias Considerations
- The parser is pattern-based and may work best with English-style input.
- It is not designed to provide culturally-aware or multilingual scheduling behavior.

## Human Oversight
Humans remain in control: suggestions are proposed, not auto-applied. Conflicting tasks are blocked unless the user changes the request.

## What I Learned
Building this project emphasized the value of balancing natural-language flexibility with deterministic reliability. It also reinforced the importance of guardrails and clarification prompts in AI-assisted planning.

## Future Improvements
- Add multi-pet request handling.
- Enable natural-language editing of scheduled tasks.
- Expand beyond one-day planning.
- Add optional calendar export and reminders.
- Improve parser coverage for more diverse phrasing.
- Build stronger multilingual support.