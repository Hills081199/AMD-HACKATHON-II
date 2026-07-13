from typing import Type, TypeVar

from google import genai
from google.genai import types
from pydantic import BaseModel

from config.settings import settings
from llm.base import BaseLLMClient
from llm.exceptions import GeminiGenerationError

T = TypeVar("T", bound=BaseModel)


class GeminiClient(BaseLLMClient):
    """
    Generic Gemini client responsible only
    for communicating with the Gemini API.
    """

    def __init__(self):
        self.client = genai.Client(
            api_key=settings.GEMINI_API_KEY
        )

    def generate(
        self,
        prompt: str,
        response_schema: Type[T],
    ) -> T:

        response = self.client.models.generate_content(
            model=settings.MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=settings.TEMPERATURE,
                max_output_tokens=settings.MAX_OUTPUT_TOKENS,
                response_mime_type="application/json",
                response_schema=response_schema,
            ),
        )

        # ---------------- DEBUG ----------------

        print("\n" + "=" * 80)
        print("GEMINI RAW RESPONSE")
        print("=" * 80)

        print("\nTEXT:\n")
        print(response.text)

        print("\nPARSED:\n")
        print(response.parsed)

        print("\nCANDIDATES:\n")
        print(response.candidates)

        print("\nFINISH REASON:\n")
        if response.candidates:
            print(response.candidates[0].finish_reason)

        print("=" * 80)

        # ---------------------------------------

        if response.parsed is None:
            raise GeminiGenerationError(
                f"Gemini returned an invalid structured response.\n\nRaw response:\n{response.text}"
            )

        return response.parsed