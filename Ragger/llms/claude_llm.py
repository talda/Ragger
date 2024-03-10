import anthropic
import tenacity

from Ragger.llms.base_llm import LanguageModel, is_rate_limit_error


def openai_response_clone(dictionary):
    class DynamicClass:
        def __init__(self, data):
            for key, value in data.items():
                if isinstance(value, dict):
                    value = openai_response_clone(value)
                setattr(self, key, value)

    return DynamicClass(dictionary)


class claudeLlm(LanguageModel):
    def __init__(self) -> None:
        super().__init__()
        self.client = anthropic.Anthropic()

    @tenacity.retry(
        wait=tenacity.wait_random_exponential(multiplier=1, min=2, max=60),
        retry=tenacity.retry_if_exception(is_rate_limit_error),
    )
    def create_response(
        self, messeges: list[str], system_prompt: str, max_tokens: int = 4096
    ):
        message = self.client.messages.create(
            model="claude-3-sonnet-20240229",
            # model='claude-3-opus-20240229',
            max_tokens=max_tokens,
            temperature=0.0,
            system=system_prompt,
            messages=messeges,
        )

        response = {}
        message_content = openai_response_clone(
            {"message": {"content": message.content[0].text}}
        )
        response["choices"] = [message_content]
        response["usage"] = {
            "completion_tokens": message.usage.output_tokens,
            "prompt_tokens": message.usage.input_tokens,
        }
        response["model"] = message.model
        response = openai_response_clone(response)
        return response
