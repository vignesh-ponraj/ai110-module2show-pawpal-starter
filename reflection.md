# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- My initial UML design focused on a small set of classes that map directly to the main user actions: managing pets, creating care tasks, and generating/viewing a daily plan. I aimed for a simple, modular structure with clear separation between data objects and planning logic.
- The classes and responsibilities were:
- Owner: stores owner information and available time, and manages the owner's pet list.
- Pet: stores pet profile details (name, species, notes) and links each pet to its care tasks.
- CareTask: represents individual care activities with key scheduling attributes (duration, priority, preferred time window, required status).
- DailyPlan: represents one day's schedule, stores scheduled tasks plus unscheduled tasks, and provides summary/completion-related behaviors.
- ScheduledTask: represents a CareTask placed at a specific time in the day and tracks task status (planned/completed/skipped).
- Scheduler: acts as the service/engine class that selects tasks based on constraints, orders them, assigns times, and produces a DailyPlan.

**b. Design changes**

- Yes. During implementation, I simplified and tightened the model so it was easier to implement correctly and better aligned with persistence needs.
- One major change was improving relationship clarity for storage and lookups. I added explicit IDs to connect records cleanly (for example, owner_id on CareTask and plan_id on ScheduledTask) so plans, tasks, and pets can be queried without relying only on nested in-memory objects.
- I also changed completion tracking from task_id to scheduled_task_id in DailyPlan. This avoids ambiguity when working with scheduled items and gives each planned item a unique identity for updates.
- Another change was replacing string-based time fields with typed time values. This reduces parsing errors and makes scheduling logic (ordering and overlap checks) more reliable.
- Finally, I removed the stored total_minutes field from DailyPlan and moved toward calculating total minutes from scheduled tasks. This avoids data drift and keeps plan summaries consistent with the actual scheduled items.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- My scheduler considers several constraints: owner daily available minutes, whether a task is required_today, task priority (high/medium/low), and preferred start time for ordering. It also validates owner-pet-task relationships before generating a plan, and it detects overlapping scheduled tasks as warnings.
- I prioritized constraints by practical impact on a real day plan. First, the schedule must fit within available time. Second, required tasks should be included before optional tasks. Third, higher-priority tasks should be favored over lower-priority tasks. Preferred time windows are used as an ordering signal so earlier tasks are placed first when possible.

**b. Tradeoffs**

- One key tradeoff is using a simple greedy strategy (required + priority + duration ordering) instead of a globally optimal scheduling algorithm. This means the plan may not always be mathematically optimal across all combinations of tasks.
- This tradeoff is reasonable for this scenario because it keeps the logic easy to understand, test, and debug while still producing practical schedules quickly. For a course project and early product version, predictable behavior and maintainability are more valuable than optimization complexity.

---

## 3. AI Collaboration

**a. How you used AI**

- I used AI throughout the workflow: first for design brainstorming (class responsibilities and relationships), then for implementation support (dataclass stubs, scheduling logic, recurrence, and conflict detection), and finally for UI integration and test-writing. I also used AI for small refactors such as improving method signatures and keeping relationships consistent as the design evolved.
- The most helpful prompts were specific and task-focused, such as asking for a class diagram from agreed requirements, requesting targeted code changes (for example, add filtering by status or pet name), and asking to verify behavior with tests. Prompts that included constraints (for example, keep it simple, do not crash on conflicts) produced the best results.

**b. Judgment and verification**

- One important moment was deciding not to keep a more complex design that introduced extra abstraction early (for example, a separate constraint object and heavier planning structure). Instead, I simplified to a smaller class set that better matched the project scope.
- I evaluated AI suggestions by checking whether they fit the assignment goals, whether the relationships stayed clear, and whether the behavior could be tested quickly. I verified changes by running the app and test suite after each meaningful update.

---

## 4. Testing and Verification

**a. What you tested**

- I tested core scheduling and model behaviors: task completion status changes, adding tasks to a pet, filtering tasks by status and pet name, recurrence creation for daily tasks, and conflict detection warnings for overlapping time blocks.
- These tests were important because they cover the highest-risk behavior in this project: state transitions, relationship consistency, and schedule quality signals. They also protect key user-facing features shown in the terminal and Streamlit UI.

**b. Confidence**

- I am moderately high confidence (about 4/5) that the scheduler works correctly for the implemented scope. The current tests pass and cover the main workflows.
- With more time, I would test additional edge cases: weekly recurrence boundaries, invalid or missing time windows, duplicate IDs, very small available-minute budgets, large mixed task sets, and scenarios with many overlapping tasks across multiple pets.

---

## 5. Reflection

**a. What went well**

- I am most satisfied with the end-to-end integration: backend classes, scheduling logic, tests, and Streamlit UI now work together. The project moved from a starter template to a working planning system with sorting, filtering, recurrence, and conflict warnings.

**b. What you would improve**

- In a next iteration, I would improve the planner with stronger optimization (not just greedy selection), richer time-window constraints, and clearer distinction between task templates and generated occurrences. I would also expand the UI for editing/deleting tasks and viewing plan history.

**c. Key takeaway**

- A key takeaway is that starting simple and validating each step is more effective than over-designing early. AI is most valuable when used iteratively with clear constraints, while human judgment is essential for choosing the right level of complexity and verifying correctness.
