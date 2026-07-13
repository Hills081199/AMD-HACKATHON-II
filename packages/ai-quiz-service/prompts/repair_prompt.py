import json


class RepairPromptBuilder:
    @staticmethod
    def create_prompt(
        title: str,
        content: str,
        question: dict,
        review_issue: dict,
    ) -> str:

        return f"""
You are an expert educational assessment designer.

Your task is NOT to generate an entire quiz.

Your task is to improve ONE question that failed quality review.

==================================================
Learning Topic
==================================================

{title}

==================================================
Learning Content
==================================================

{content}

==================================================
Question To Repair
==================================================

{json.dumps(question, indent=2)}

==================================================
Reviewer Feedback
==================================================

{json.dumps(review_issue, indent=2)}

==================================================
Instructions
==================================================

- Rewrite ONLY this question.

- Keep the same question type.

- Keep the same learning objective.

- Keep the same difficulty unless the reviewer requested a change.

- Keep the same Bloom level unless the reviewer requested a change.

- If the reviewer reports:
    • incorrect answer → fix only the answer
    • weak distractors → improve only distractors
    • grammar → fix wording
    • explanation → rewrite explanation
    • duplicate → create a different question covering the same concept
    • rubric → generate an appropriate grading rubric

- Do NOT invent facts.

- Use ONLY the provided learning material.

- Return ONLY the repaired Question object.

- Do NOT return the entire quiz.
"""