import pandas as pd
import torch
from sentence_transformers import SentenceTransformer
from torch import Tensor
import argparse

def load_data(file_path: str) -> pd.DataFrame:
    """
    Load data from a CSV file into a DataFrame.

    Args:
        file_path (str): Path to the CSV file.

    Returns:
        pd.DataFrame: DataFrame containing the loaded data.
    """
    df = pd.read_csv(file_path)
    if 'message' not in df.columns:
        raise ValueError("DataFrame must contain a 'message' column.")
    return df

def get_embeddings(df: pd.DataFrame, model_name: str = "all-MiniLM-L6-v2") -> Tensor:
    """
    Generate embeddings for the 'text' column in the DataFrame using a specified SentenceTransformer model.

    Args:
        df (pd.DataFrame): DataFrame containing a 'text' column.
        model_name (str): Name of the SentenceTransformer model to use.

    Returns:
        pd.DataFrame: DataFrame with an additional 'embeddings' column containing the embeddings.
    """
    model = SentenceTransformer(model_name)
    embeddings = model.encode(
        df['message'].tolist(),
        show_progress_bar=True,
        convert_to_tensor=True
    )
    return embeddings

def save_embeddings(embeddings: Tensor, file_path: str) -> None:
    """
    Save the embeddings to a file.

    Args:
        embeddings (Tensor): The embeddings to save.
        file_path (str): The path where the embeddings will be saved.
    """
    torch.save(embeddings, file_path)

def main():
    parser = argparse.ArgumentParser(description="Generate embeddings for email messages.")
    parser.add_argument('--input_file', type=str, required=True, help='Path to the input CSV file containing email messages.')
    parser.add_argument('--output_file', type=str, required=True, help='Path to save the generated embeddings.')
    parser.add_argument('--model_name', type=str, default='all-MiniLM-L6-v2', help='Name of the SentenceTransformer model to use.')

    args = parser.parse_args()

    df = load_data(args.input_file)
    embeddings = get_embeddings(df, args.model_name)
    save_embeddings(embeddings, args.output_file)

if __name__ == "__main__":
    main()