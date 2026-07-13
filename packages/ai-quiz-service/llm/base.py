from abc import ABC, abstractmethod
from typing import Type, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class BaseLLMClient(ABC):

    @abstractmethod
    def generate(
        self,
        prompt: str,
        response_schema: Type[T],
    ) -> T:
        pass