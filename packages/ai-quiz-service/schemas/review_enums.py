from enum import Enum


class ReviewSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ReviewCategory(str, Enum):
    GROUNDING = "grounding"
    CORRECT_ANSWER = "correct_answer"
    DISTRACTORS = "distractors"
    DUPLICATE = "duplicate"
    DIFFICULTY = "difficulty"
    BLOOM_LEVEL = "bloom_level"
    EXPLANATION = "explanation"
    RUBRIC = "rubric"
    GRAMMAR = "grammar"