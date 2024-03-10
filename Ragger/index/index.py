import os
import pickle
from typing import List

import numpy as np
import openai
import faiss


class Index:
    def __init__(self, index_path: str) -> None:
        """
        Initializes the object with the provided index path.

        Parameters:
            index_path (str): The path to the index file.

        Returns:
            None
        """
        self.index_path = index_path
        if os.path.exists(f'{index_path}.index'):
            self.index = faiss.read_index(f'{index_path}.index')
            self.ind_to_file = pickle.load(open(f"{index_path}.pickle", "rb"))
        else:
            self.index = None
            self.ind_to_file = {}

# Function to get embedding vector from OpenAI API
    def get_embedding(self, text: str | list[str]) -> np.ndarray | None:
        """
        Function to generate embeddings for the given text using OpenAI's text-embedding-3-small model.

        Args:
            text (str or list[str]): The input text or list of texts for which embeddings are to be generated.

        Returns:
            numpy.ndarray or None: The embeddings for the input text, or None if an error occurs.
        """
        if isinstance(text, str):
            text = [text]
        try:
            response = openai.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            embeddings = np.stack([np.array(item.embedding) for item in response.data])
            return embeddings
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

# Function to iterate through text files in a folder
    def process_text_files(self, folder_path: str) -> None:
        """
        Process text files in the specified folder path, extract embeddings, and build an index.

        Args:
            folder_path (str): The path to the folder containing the text files.

        Returns:
            None
        """
        list_dir = os.listdir(folder_path)
        ind_insert = len(self.ind_to_file)
        for ind, filename in enumerate(list_dir):
            if filename[0] == '.':
                continue
            with open(os.path.join(folder_path, filename), 'r') as file:
                text = file.read()
                embedding = self.get_embedding(text)
                if not self.index:
                    self.index = faiss.IndexFlatIP(len(embedding[0]))
                if embedding is not None:
                        self.index.add(np.array([embedding[0]]))
                        self.ind_to_file[ind_insert] = os.path.join(folder_path, filename)
                        ind_insert += 1
                print(f"Indexed {filename} ({(ind+1)/len(list_dir)*100:.2f}%)")
        faiss.write_index(self.index, f"{self.index_path}.index")
        with open(f'{self.index_path}.pickle', 'wb') as handle:
            pickle.dump(self.ind_to_file, handle, protocol=pickle.HIGHEST_PROTOCOL)

        
        
    def get_context(self, query: str | list[str], k=5) -> List[str]:
        """
        Retrieve context based on the input query(s) and optional parameter k.
        
        :param query: the input query(s)
        :param k: the number of nearest neighbors to retrieve per query (default is 5)
        :return: a list of retrieved context files based on the query (up to k * len(query) results)
        """
        embeddings = self.get_embedding(query)
        _, I = self.index.search(embeddings, k)
      
        array_1d_unique = np.unique(I.flatten())
        ret = [os.path.join(os.path.dirname(self.index_path), self.ind_to_file[f]) for f in array_1d_unique]
        return ret
    
        
        