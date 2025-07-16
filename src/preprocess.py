import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer, util
import torch
import yaml
from pathlib import Path
from typing import Dict, List, Union
import argparse

def load_embeddings(file_path: str = "../data/processed/email_embeddings.pt") -> torch.Tensor:
    """
    Load embeddings from a file.

    Args:
        file_path (str): Path to the file containing embeddings.

    Returns:
        torch.Tensor: Loaded embeddings.
    """
    return torch.load(file_path)


def load_raw_prototypes(
        path: str = "config/prototypes.yaml"
) -> Dict[str, List[str]]:
    """
    Load label→example‑texts mapping from a YAML or JSON file.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Could not find prototypes file at {path}")
    if p.suffix in {".yaml", ".yml"}:
        return yaml.safe_load(p.read_text())
    elif p.suffix == ".json":
        import json
        return json.loads(p.read_text())
    else:
        raise ValueError("Unsupported format: use .yaml/.yml or .json")


def build_prototypes(
        raw_prototypes: Dict[str, List[str]],
        model_name: str = "all-MiniLM-L6-v2",
) -> Dict[str, torch.Tensor]:
    """
    Given a dict of label→example texts, compute the mean SBERT embedding
    for each label.
    """
    model: SentenceTransformer = SentenceTransformer(model_name)
    return {
        label: torch.tensor(np.mean(
            model.encode(texts, convert_to_tensor=False), axis=0
        ))
        for label, texts in raw_prototypes.items()
    }


def label_embeddings(
        embeddings: Union[torch.Tensor, np.ndarray],
        prototypes: Dict[str, torch.Tensor],
        threshold: float = 0.4
) -> List[str]:
    """
    For each embedding in `embeddings`, compute its cosine similarity
    to each prototype and pick the best label (or 'other' if below threshold).
    """
    # ensure embeddings is a Tensor
    embs = embeddings if isinstance(embeddings, torch.Tensor) else torch.tensor(embeddings)

    labels = []
    for emb in embs:
        # compute all sims for this one embedding
        scores = {
            label: util.cos_sim(emb, proto).item()
            for label, proto in prototypes.items()
        }
        best_label, best_score = max(scores.items(), key=lambda kv: kv[1])
        labels.append(best_label if best_score > threshold else "other")
    return labels


def label_data(df: pd.DataFrame, embeddings: torch.Tensor) -> pd.DataFrame:
    raw_prototypes = load_raw_prototypes()
    prototypes = build_prototypes(raw_prototypes)
    labels = label_embeddings(embeddings, prototypes, threshold=0.4)

    df['label'] = labels
    return df


def preprocess_data(df: pd.DataFrame, embeddings: torch.Tensor) -> pd.DataFrame:
    """
    Preprocess the DataFrame by ensuring it has a 'message' column.

    Args:
        df (pd.DataFrame): DataFrame to preprocess.
        embeddings (torch.Tensor): Embeddings to associate with the DataFrame.

    Returns:
        pd.DataFrame: Preprocessed DataFrame.
    """
    if 'message' not in df.columns:
        raise ValueError("DataFrame must contain a 'message' column.")

    df['emb'] = embeddings.tolist() if isinstance(embeddings, torch.Tensor) else embeddings

    selected = ['academics', 'talks', 'internship', 'club', 'other']
    new_df = df[df['label'].isin(selected)].copy()

    # pick 1000 academics
    acad_sample = new_df[new_df['label'] == 'academics'] \
        .sample(n=1000, random_state=42)

    # pick 1000 others
    other_sample = new_df[new_df['label'] == 'other'] \
        .sample(n=1000, random_state=42)

    # keep *all* the remaining labels (club, internship, talks, etc.)
    rest = new_df[~new_df['label'].isin(['academics', 'other'])]

    # combine & reshuffle
    downsamp_df = pd.concat([acad_sample, other_sample, rest],
                            ignore_index=True) \
        .sample(frac=1, random_state=42) \
        .reset_index(drop=True)

    return downsamp_df

def save_preprocessed_data(df: pd.DataFrame, file_path: str = "../data/processed/processed_data.pkl") -> None:
    """
    Save the preprocessed DataFrame to a CSV file.

    Args:
        df (pd.DataFrame): DataFrame to save.
        file_path (str): Path to save the preprocessed DataFrame.
    """
    df.to_pickle(file_path)
    print(f"Preprocessed data saved to {file_path}")


def main():
    parser = argparse.ArgumentParser(description="Preprocess email data and generate labels.")
    parser.add_argument('--input_file', type=str, required=True, help='Path to the input CSV file containing email messages.')
    parser.add_argument('--output_file', type=str, default='../data/processed/processed_data.pkl', help='Path to save the preprocessed data.')

    args = parser.parse_args()

    # Load the raw data
    df = pd.read_csv(args.input_file)

    # Load embeddings
    embeddings = load_embeddings()

    labeled_df = label_data(df, embeddings)
    processed_data = preprocess_data(labeled_df, embeddings)

    print(processed_data.groupby('label').size())

    # Save the preprocessed and labeled data
    save_preprocessed_data(processed_data, args.output_file)

if __name__ == "__main__":
    main()