import torch
import numpy as np
from sentence_transformers import SentenceTransformer
from tensorflow.keras.models import load_model

model = load_model('../models/model_v1.keras')

def get_embeddings(text: str) -> torch.Tensor:
    """
    Generate embeddings for a given text using a pre-trained SentenceTransformer model.

    Args:
        text (str): The input text to generate embeddings for.

    Returns:
        torch.Tensor: The generated embeddings.
    """
    sentence_model = SentenceTransformer("all-MiniLM-L6-v2")
    embedding = sentence_model.encode(text)
    embedding = embedding.reshape(1, -1)
    return embedding

def predict(text: str) -> int:
    """
    Predict the label for the given text using a pre-trained model.

    Args:
        text (str): The input text to classify.

    Returns:
        str: The predicted label.
    """
    embedding = get_embeddings(text)
    prediction = model.predict(embedding)
    pred_idx = int(np.argmax(prediction[0]))  # → 3

    return pred_idx