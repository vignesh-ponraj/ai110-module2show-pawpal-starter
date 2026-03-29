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

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
