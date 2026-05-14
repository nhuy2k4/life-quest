from __future__ import annotations

from typing import Any

import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score
from sklearn.model_selection import train_test_split

from app.services.recommendation.ml.feature_builder import get_feature_schema, vectorize_features


def build_feature_matrix(df: pd.DataFrame, feature_order: list[str] | None = None) -> list[list[float]]:
    order = feature_order or get_feature_schema()
    return [
        vectorize_features(row.to_dict(), order)
        for _, row in df.iterrows()
    ]


def train_logistic_regression(
    df: pd.DataFrame,
    feature_order: list[str] | None = None,
    test_size: float = 0.2,
    random_state: int = 42,
) -> tuple[LogisticRegression, dict[str, float]]:
    order = feature_order or get_feature_schema()
    X = build_feature_matrix(df, order)
    y = df["label"].astype(int).tolist()

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=random_state,
        stratify=y,
    )

    model = LogisticRegression(
        max_iter=300,
        class_weight="balanced",
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    metrics = {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision": float(precision_score(y_test, y_pred, zero_division=0)),
        "recall": float(recall_score(y_test, y_pred, zero_division=0)),
    }
    return model, metrics
