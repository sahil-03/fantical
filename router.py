import numpy as np 
from openai import OpenAI
from dotenv import load_dotenv
from typing import List
from typing import Any

class EmbeddingHandler(): 
    def __init__(self, key): 
        # load_dotenv()
        self.model = "text-embedding-3-small"
        self.client = OpenAI(api_key=key)
    
    def get_embedding(self, text: str) -> Any: 
        text = text.replace("\n", " ")
        return self.client.embeddings.create(input=[text], model=self.model).data[0].embedding
 
    def cosine_similarity(self, A: List[float], B: List[float]) -> float: 
        return np.dot(A, B) / (np.linalg.norm(A) * np.linalg.norm(B))
    
    def add_embedding(self, member: str, message: str) -> None: 
        self.member_chat_embeddings[member].append(self.get_embedding(message))

    
class MessageRouter(EmbeddingHandler): 
    def __init__(self, group_chat_members, key):
        super().__init__(key)
        self.member_chat_embeddings = {member: [] for member in group_chat_members}

    def message_router(self, sender: str, message: str) -> str:
        message_embedding = self.get_embedding(message)
        relevancy_scores = {member: self.calculate_relevancy(member, message_embedding) for member in self.member_chat_embeddings.keys() if member != sender}
        sorted_scores = sorted(relevancy_scores.items(), key=lambda x:x[1], reverse=True)
        return sorted_scores[0][0]

    def calculate_relevancy(self, member: str, message_embedding: str) -> float:
        similarity_scores = [self.cosine_similarity(message_embedding, e) for e in self.member_chat_embeddings[member]]
        weights = [0.5 ** i for i in range(len(similarity_scores))]
        weighted_average_score = sum(w * s for w, s in zip(weights, similarity_scores)) / sum(weights)
        return weighted_average_score