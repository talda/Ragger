import os
import tenacity
from Ragger.llms.base_llm import LanguageModel, is_rate_limit_error


class OpenAIGPT(LanguageModel):
    def __init__(self) -> None:
        super().__init__()
        import openai

        self.client = openai.OpenAI()

    @tenacity.retry(
        wait=tenacity.wait_random_exponential(multiplier=1, min=2, max=60),
        retry=tenacity.retry_if_exception(is_rate_limit_error),
    )
    def create_response(
        self, messages: list[str], system_prompt: str, max_tokens: int = 4096
    ) -> str:
        response = self.client.Completion.create(
            model=os.environ["MODEL_NAME"],
            prompt=system_prompt,
            max_tokens=max_tokens,
            user_messages=messages,
        )
        return response
