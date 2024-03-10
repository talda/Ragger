import json
import os
import time
import openai
import threading

from openai_usage_logger import usageLogger


class contextQueryBuilder:
    def __init__(self, llm, assistant="general purpose") -> None:
        self.db_search_query = f"""Your task is to formulate as many search queries as needed for {assistant}, to assist in responding to the user's question. The search is only in {assistant} database.
        break the user query into search queries. output should be in a json: {{"queries": ["query1", "query2", "query3"]}}
        """

        self.hyde_query = f"""Your task is to generate hypothetic {assistant} section that is relevant to the given subject. Sections are never longer than 100 text tokens.
        output should be in a json: {{"context_text": <hypothetic_section>}}
        """

        self.llm = llm

    def build_search_query(self, user_question: str, hyde: bool = True) -> json:
        """
        Build context search queries based on the user question

        Args:
            user_query (str): The user input for the search query.
            hyde (bool, optional): A flag to indicate whether to build a hyde query. Defaults to True.

        Returns:
            json: The built search query in JSON format.
        """
        if hyde:
            return self.build_hyde_query(user_question)
        else:
            return self.build_query(user_question)

    def build_query(self, user_question: str) -> json:
        """
        Breaks down users question in to multiple databse search queries, and returns the JSON content.
        """
        # response = openai.chat.completions.create(
        #   model=os.environ["MODEL_NAME"],
        #   seed=12345,
        #   temperature=0,
        #   response_format={ "type": "json_object" },
        #   messages=[
        #     {"role": "system", "content": self.db_search_query},
        #     {"role": "user", "content": user_question}
        #   ]
        # )
        response = self.llm.create_response(
            [
                {"role": "user", "content": user_question},
                {"role": "assistant", "content": '{"queries": ['},
            ],
            self.db_search_query,
        )
        usageLogger().log(response, "build_query")
        json_content = json.loads('{"queries": [' + response.choices[0].message.content)

        print(json_content)
        return json_content

    def build_hyde_query(self, user_question: str) -> json:
        """
        Breaks down users question in to multiple databse search queries, and generates an hypothetical answer section to each query and returns the JSON content.
        """

        queries = self.build_query(user_question)
        return_json = {"queries": []}

        def call_openai(query):
            # response = openai.chat.completions.create(
            #     model=os.environ["MODEL_NAME"],
            #     seed=12345,
            #     temperature=0,
            #     response_format={ "type": "json_object" },
            #     messages=[
            #         {"role": "system", "content": self.hyde_query},
            #         {"role": "user", "content": f'Subject: {query}'}
            #     ]
            # )
            response = self.llm.create_response(
                [
                    {"role": "user", "content": f"Subject: {query}"},
                    {"role": "assistant", "content": '{"context_text": "'},
                ],
                self.hyde_query,
            )
            usageLogger().log(response, "build_hyde_query")

            # Properly escape the string and construct the JSON
            json_content = json.loads(
                json.dumps({"context_text": response.choices[0].message.content})
            )
            return_json["queries"].append(json_content["context_text"])

        threads = []
        for query in queries["queries"]:
            thread = threading.Thread(target=call_openai, args=(query,))
            thread.start()
            threads.append(thread)
            time.sleep(0.5)

        thread = threading.Thread(target=call_openai, args=(user_question,))
        thread.start()
        threads.append(thread)

        for thread in threads:
            thread.join()

        print(return_json)
        return return_json
