from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import joblib
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from app.services.recommendation.ml.feature_builder import get_feature_schema
from app.services.recommendation.ml.synthetic_data import (
    generate_fake_quests,
    generate_fake_users,
    generate_synthetic_dataset,
    save_dataset,
)
from app.services.recommendation.ml.training_pipeline import train_logistic_regression

DEFAULT_ARTIFACT_DIR = Path(__file__).resolve().parents[1] / "ml_artifacts"
DEFAULT_DATASET_PATH = DEFAULT_ARTIFACT_DIR / "training_dataset.csv"
DEFAULT_MODEL_PATH = DEFAULT_ARTIFACT_DIR / "model.pkl"
DEFAULT_SCHEMA_PATH = DEFAULT_ARTIFACT_DIR / "feature_schema.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train Logistic Regression ranker")
    parser.add_argument("--users", type=int, default=200, help="Number of synthetic users")
    parser.add_argument("--quests", type=int, default=300, help="Number of synthetic quests")
    parser.add_argument("--samples-per-user", type=int, default=40, help="Samples per user")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--artifact-dir", type=str, default=str(DEFAULT_ARTIFACT_DIR))
    parser.add_argument("--regenerate", action="store_true", help="Regenerate dataset CSV")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    artifact_dir = Path(args.artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)

    dataset_path = artifact_dir / "training_dataset.csv"
    model_path = artifact_dir / "model.pkl"
    schema_path = artifact_dir / "feature_schema.json"

    if args.regenerate or not dataset_path.exists():
        users = generate_fake_users(args.users, seed=args.seed)
        quests = generate_fake_quests(args.quests, seed=args.seed)
        df = generate_synthetic_dataset(users, quests, samples_per_user=args.samples_per_user, seed=args.seed)
        save_dataset(df, str(dataset_path))
    else:
        df = pd.read_csv(dataset_path)

    feature_order = get_feature_schema()
    model, metrics = train_logistic_regression(df, feature_order=feature_order)

    joblib.dump(model, model_path)
    schema_path.write_text(json.dumps(feature_order, ensure_ascii=False, indent=2), encoding="utf-8")

    print("Training complete")
    print(f"Accuracy: {metrics['accuracy']:.4f}")
    print(f"Precision: {metrics['precision']:.4f}")
    print(f"Recall: {metrics['recall']:.4f}")
    print(f"Model saved: {model_path}")
    print(f"Schema saved: {schema_path}")


if __name__ == "__main__":
    main()
