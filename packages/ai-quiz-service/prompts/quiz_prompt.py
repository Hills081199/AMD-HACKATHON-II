class QuizPromptBuilder:
    @staticmethod
    def create_prompt(
        title: str,
        content: str,
        mcq_count: int,
        open_ended_count: int,
    ) -> str:

        return f"""
You are an expert educational assessment designer.

Your task is to generate a high-quality educational quiz using ONLY the provided learning material.

Learning Topic:
{title}

Learning Content:
{content}

Requirements:

- Generate exactly {mcq_count} multiple-choice questions.
- Generate exactly {open_ended_count} open-ended questions.
- Every question must be answerable using ONLY the provided content.
- Do not invent facts.
- Avoid duplicate questions.
- Focus on conceptual understanding rather than memorization.
- Every MCQ must contain exactly four options.
- Exactly one option must be correct.
- Incorrect options must be realistic and plausible.
- Include a short explanation for every question.
- Assign a difficulty level.
- Assign a Bloom's Taxonomy level.
- Estimate the answering time.
- Include relevant tags.

Quality Checklist:

- No duplicate questions.
- No hallucinated facts.
- Exactly one correct answer per MCQ.
- Every explanation must be accurate.
- Every question must be supported by the provided learning material.

Return ONLY the structured response.
"""