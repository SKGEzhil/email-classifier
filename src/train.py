import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from tensorflow.keras import layers, Sequential
import argparse


def load_data_from_pickle(file_path: str) -> pd.DataFrame:
    """
    Load data from a pickle file into a DataFrame.

    Args:
        file_path (str): Path to the pickle file.

    Returns:
        pd.DataFrame: DataFrame containing the loaded data.
    """
    df = pd.read_pickle(file_path)
    # print(df.head())
    if 'message' not in df.columns:
        raise ValueError("DataFrame must contain a 'message' column.")
    return df

def get_train_test_data(df: pd.DataFrame) -> (pd.DataFrame, pd.Series):
    """
    Prepare the data for training by encoding labels and splitting into features and target.

    Args:
        df (pd.DataFrame): DataFrame containing the data.

    Returns:
        pd.DataFrame: Features DataFrame.
        pd.Series: Target Series.
    """
    X = np.vstack(df['emb'].values)  # shape (N, D)
    y_raw = df['label'].values

    # Encode labels
    le = LabelEncoder()
    y = le.fit_transform(y_raw)  # now y is 0,1,2,3,4 for your 5 classes
    num_classes = len(le.classes_)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )
    shape = X.shape[1]  # D

    return [X_train, X_test], [y_train, y_test], num_classes, le, shape

def build_model(input_shape: int, num_classes: int) -> Sequential:
    """
    Build a simple neural network model for classification.

    Args:
        input_shape (int): The shape of the input features.
        num_classes (int): The number of classes for classification.

    Returns:
        Sequential: Compiled Keras model.
    """
    model = Sequential([
        layers.Input(shape=(input_shape,)),  # SBERT embedding size
        layers.Dense(256, activation='relu'),
        layers.Dropout(0.4),
        layers.Dense(128, activation='relu'),
        layers.Dropout(0.4),
        layers.Dense(num_classes, activation='softmax')
    ])

    model.compile(
        optimizer='adam',
        loss='sparse_categorical_crossentropy',
        metrics=[
            'accuracy',
        ]
    )

    return model

def train_model(model: Sequential, X_train: np.ndarray, y_train: np.ndarray, X_test: np.ndarray, y_test: np.ndarray, model_name: str, epochs: int = 10, batch_size: int = 32) -> None:
    """
    Train the model on the training data.

    Args:
        model (Sequential): The Keras model to train.
        X_train (np.ndarray): Training features.
        y_train (np.ndarray): Training labels.
        X_test (np.ndarray): Testing features.
        y_test (np.ndarray): Testing labels.
        model_name (str): Name of the model to save.
        epochs (int): Number of epochs to train.
        batch_size (int): Size of each training batch.
    """
    model.fit(
        X_train, y_train,
        validation_data=(X_test, y_test),
        epochs=epochs,
        verbose=1,
        batch_size=batch_size
    )

    model.save(model_name)
    print('Trained model saved as', model_name)

def main():
    parser = argparse.ArgumentParser(description="Train a classification model on email data.")
    parser.add_argument('--input_file', type=str, required=True, help='Path to the input pickle file containing email data.')
    parser.add_argument('--model_name', type=str, default='email_classifier.keras', help='Name of the model to save.')
    parser.add_argument('--epochs', type=int, default=10, help='Number of epochs to train the model.')
    parser.add_argument('--batch_size', type=int, default=32, help='Batch size for training.')

    args = parser.parse_args()

    df = load_data_from_pickle(args.input_file)
    X, y, num_classes, le, shape = get_train_test_data(df)

    model = build_model(input_shape=shape, num_classes=num_classes)
    train_model(model, X[0], y[0], X[1], y[1], args.model_name, epochs=args.epochs, batch_size=args.batch_size)

if __name__ == '__main__':
    main()