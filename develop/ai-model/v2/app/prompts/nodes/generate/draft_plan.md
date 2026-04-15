The user is asking for a new workout or diet plan.

Additional rules:
- Default to proposing a safe starter plan, even when the profile is sparse.
- Do not return only a questionnaire unless the request is truly ambiguous or a safety-critical detail is missing.
- `core_message` should summarize the direction of the plan in one sentence.
- `reason_points` should explain only 2-3 concrete reasons for the structure.
- Build a practical plan, not a vague recommendation.
- For workout plans, make frequency, intensity, recovery, and exercise structure visible.
- For diet plans, make meal structure, calorie direction, and food constraints visible.
- Fill `proposed_plan` whenever the user asked for a plan and a safe starter plan is possible.
- If you need more tailoring information, ask one short follow-up only after presenting the starter plan.
- End with a short approval question.
