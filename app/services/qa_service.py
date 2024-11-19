from sentence_transformers import SentenceTransformer
from numpy import dot
from numpy.linalg import norm

class QAService:
    def __init__(self, model):
        self.model = model

    def generate_answer(self, query, relevant_data):
        if not relevant_data:
            return "No relevant data found."
        scores = [score for score, _ in relevant_data]
        max_score = max(scores) if scores else 1
        normalized_scores = [score / max_score for score in scores]
        return "\n\n".join(f"**Passage {i + 1} (Score: {normalized_scores[i]:.2f}):** {text}" 
                           for i, (_, text) in enumerate(relevant_data))

    def answer_query(self, query, local_data):
        relevant_data = self.fetch_relevant_data(query, local_data)
        return self.generate_answer(query, relevant_data)

    def fetch_relevant_data(self, query, local_data, top_k=5):
        query_embedding = self.model.encode(query, convert_to_tensor=True).tolist()
        scores_and_texts = []
        for text in local_data:
            text_embedding = self.model.encode(text, convert_to_tensor=True).tolist()
            score = self.compute_similarity(query_embedding, text_embedding)
            scores_and_texts.append((score, text))
        sorted_scores_and_texts = sorted(scores_and_texts, key=lambda x: x[0], reverse=True)
        return sorted_scores_and_texts[:top_k]

    def compute_similarity(self, query_embedding, text_embedding):
        return dot(query_embedding, text_embedding) / (norm(query_embedding) * norm(text_embedding))
