import openai
from Ragger.context import contextGenerator
from Ragger.index import Index
import os
from openai_usage_logger import usageLogger
from Ragger.llms import claudeLlm

default_system_prompt = """ """


class chatEngine:
    def __init__(
        self,
        index_name: str,
        assistant: str = "general purpose",
        system_prompt: str = default_system_prompt,
        use_history: bool = False,
    ) -> None:
        self.index_instance = Index(index_name)
        self.llm = claudeLlm()
        self.context_query = contextGenerator(self.index_instance, assistant, self.llm)
        self.history = []
        self.use_history = use_history
        self.system_prompt = system_prompt

    def generate_response(self, user_question: str, hyde=True) -> str:

        context_text = self.context_query.generate_context(user_question, hyde)
        file_name = "context.txt"
        with open(file_name, "w", encoding="utf-8") as file:
            file.write(context_text)
        messages = []
        # messages.append({"role": "system", "content": self.system_prompt})
        if len(self.history) == 2:
            messages.append({"role": "user", "content": self.history[0]})
            messages.append({"role": "assistant", "content": self.history[1]})
        messages.append(
            {
                "role": "user",
                "content": context_text + f"\nUser question:\n {user_question}",
            }
        )

        # response = openai.chat.completions.create(
        #     model=os.environ["MODEL_NAME"],
        #     messages=messages,
        #     temperature=0,
        #     seed=12345,
        # )
        response = self.llm.create_response(messages, self.system_prompt)
        usageLogger().log(response, "generate_response")
        if self.use_history:
            self.history = []
            self.history.append(f"User question:\n {user_question}")
            self.history.append(response.choices[0].message.content)
        return response.choices[0].message.content
