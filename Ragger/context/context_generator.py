import math
import os
import openai
from Ragger.context.context_query_builder import contextQueryBuilder

from Ragger.index import Index

from openai_usage_logger import usageLogger


class contextGenerator:
    def __init__(self, index: Index, assistant: str, llm: object) -> None:
        self.context_query_builder = contextQueryBuilder(llm, assistant)
        self.index = index
        self.assistant = assistant
        self.llm = llm
        self.is_helpful_query = '''
        You are an Assistant responsible for helping detect whether the retrieved document contains information that is helpful for answering the user's question. For a given input, you need to output a single word: "Yes", "No" or "Maybe" indicating the retrieved document is helpful for answering the query.
        A document is considered helpful even if there is only one sentance in the document that is helpful.
        
        Query: How does a building's defense value increase when an attack occurs?
        Document: """When an attack occurs, the party must perform a defense check for each building targeted by the attack. For each defense check, draw a card from the town guard deck and add its bonus to Frosthaven’s total defense value (along with any modifiers from the event)."""
        Relevant: Yes

        Query: What is the effect of ward on an attack?
        Document: """Upgrading Buildings: When the Craftsman or certain other buildings are upgraded, move the listed items from the unavailable supply to the corresponding available supply (either purchasable items or craftable items, depending on the building)."""
        Relevant: No
        
        Query: What is the effect of poison on an attack?
        Document: """the figure is healed.\n\n[Poison Icon] Poison: All attacks targeting the figure gain “+1 [Attack Icon].” Poison is removed when the figure is healed but, unlike wound/brittle/bane, poison prevents the heal from increasing the figure’s current hit point value.\n\n[Immobilize Icon] Immobilize: The figure cannot perform any move abilities. Immobilize is removed at the end of the figure’s next turn.\n\n[Disarm Icon] Disarm: The figure cannot perform any attack abilities. Disarm is removed at the end of the figure’s next turn.\n\n[Frosthaven Identifier] [Impair Icon] Impair: Impair can only be gained by characters. The character cannot use or trigger any items, but bonuses previously gained from items are still active. Impair is removed at the end of the character’s next turn.\n\n[Stun Icon] Stun: The figure cannot perform any abilities or use or trigger any items, but bonuses previously gained are still active. Stun is removed at the end of the figure’s next turn. At the start of the round, stunned characters still must select two cards to play (or declare a long rest), but the cards will be discarded with no effect if stun is not removed by some other means before the end of their turn. Long resting still occurs normally for stunned characters.\n\n[Muddle Icon] Muddle: The figure gains disadvantage on all of their attacks. Muddle is removed at the end of the figure’s next turn.\n\n[Curse Icon] Curse: The figure must shuffle a curse card into their attack modifier deck. If the figure does not use an attack modifier deck, curse has no effect. When a curse card is drawn, it acts as a [Miss Icon] modifier and is returned to the supply once resolved, instead of placed in the discard pile. There are 10 curse cards with the [Star Icon] icon, which can only be added to character and ally decks, and 10 curse cards with the [Monster Icon] icon, which can only be added to the monster deck. If there are no applicable curse cards available, curse has no effect. Immunity to curse prevents a figure from adding a curse card to their deck, but does not prevent a drawn curse card from taking effect."""
        Relevant: Yes

        '''

    def generate_context(self, user_question: str, hyde: bool = True) -> str:
        """
        Generate context based on the given user question.

        Args:
            user_question (str): The user's question for context relevance filtering and re-ranking.

        Returns:
            str: The generated context text based on the user question.
        """
        queries = self.context_query_builder.build_search_query(user_question, hyde)
        return self._generate_context(queries["queries"], user_question)

    def _generate_context(self, queries: list[str], user_question="") -> str:
        """
        Generate context based on the given queries and user question.

        Args:
            queries (list[str]): The list of queries for context generation.
            user_question (str): The user's question for context relevance filtering and re-ranking.

        Returns:
            str: The generated context text based on the queries and user question.
        """

        if len(queries) == 0:
            return ""

        context = self.index.get_context(queries)
        context_text = "Context:\n"
        helpful = []
        nothelpful = []
        for con_ind, filename in enumerate(context):
            with open(f"{filename}", "r") as file:
                curr_context = file.read()
                summary_context = self.is_helpful(curr_context, user_question)
                # summary_context = self.is_helpful(curr_context, "")
                if summary_context:
                    context_text += f"Context {con_ind}:\n" + curr_context + "\n"
                    helpful.append(filename)
                else:
                    nothelpful.append(filename)

        print(f"helpful: {helpful}, nothelpful: {nothelpful}")
        return context_text

    def is_helpful(self, context: str, user_question: str) -> bool:

        if user_question == "":
            return True

        query_prompt = '''
        Query: {query}
        Document: """{document}"""
        Relevant:
        '''

        # response = openai.chat.completions.create(
        #     model=os.environ["MODEL_NAME"],
        #     messages=[
        #         {"role": "system", "content": self.is_helpful_query},
        #         {"role": "user", "content": query_prompt.format(query=user_question, document=context)}
        #     ],
        #     temperature=0,
        #     seed=12345,
        #     logprobs=True,
        #     max_tokens=1,
        #     logit_bias={3363: 1, 1400: 1},
        # )
        # usageLogger().log(response, 'is_helpful')
        # ret = math.e**(response.choices[0].logprobs.content[0].logprob) > 0.5 and response.choices[0].message.content == 'Yes'
        # return ret

        response = self.llm.create_response(
            messeges=[
                {
                    "role": "user",
                    "content": query_prompt.format(
                        query=user_question, document=context
                    ),
                }
            ],
            system_prompt=self.is_helpful_query,
            max_tokens=1,
        )
        print(response.choices[0].message.content)
        return response.choices[0].message.content != "No"
