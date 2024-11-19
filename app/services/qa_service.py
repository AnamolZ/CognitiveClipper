from sentence_transformers import SentenceTransformer
from numpy import dot
from numpy.linalg import norm

class QABot:
    def __init__(self, model):
        self.model = model

    def generateAnswer(self, query, relevantData):
        if not relevantData:
            return "No relevant data found."
        scores = [score for score, _ in relevantData]
        maxScore = max(scores) if scores else 1
        normalizedScores = [score / maxScore for score in scores]
        return "\n\n".join(f"**Passage {i + 1} (Score: {normalizedScores[i]:.2f}):** {text}" 
                           for i, (_, text) in enumerate(relevantData))

    def answerQuery(self, query, localData):
        relevantData = self.fetchRelevantData(query, localData)
        return self.generateAnswer(query, relevantData)

    def fetchRelevantData(self, query, localData, topK=5):
        queryEmbedding = self.model.encode(query, convert_to_tensor=True).tolist()
        scoresAndTexts = []
        for text in localData:
            textEmbedding = self.model.encode(text, convert_to_tensor=True).tolist()
            score = self.computeSimilarity(queryEmbedding, textEmbedding)
            scoresAndTexts.append((score, text))
        sortedScoresAndTexts = sorted(scoresAndTexts, key=lambda x: x[0], reverse=True)
        return sortedScoresAndTexts[:topK]

    def computeSimilarity(self, queryEmbedding, textEmbedding):
        return dot(queryEmbedding, textEmbedding) / (norm(queryEmbedding) * norm(textEmbedding))
