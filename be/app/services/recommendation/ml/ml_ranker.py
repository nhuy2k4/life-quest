from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib
import numpy as np

from app.services.recommendation.ml.feature_builder import get_feature_schema, vectorize_features

DEFAULT_ARTIFACT_DIR = Path(__file__).resolve().parents[4] / "ml_artifacts"
DEFAULT_MODEL_PATH = DEFAULT_ARTIFACT_DIR / "model.pkl"
DEFAULT_SCHEMA_PATH = DEFAULT_ARTIFACT_DIR / "feature_schema.json"


class MLRanker:
    def __init__(
        self,
        model_path: str | Path | None = None,
        feature_schema_path: str | Path | None = None,
    ) -> None:
        self.model_path = Path(model_path) if model_path else DEFAULT_MODEL_PATH
        self.feature_schema_path = Path(feature_schema_path) if feature_schema_path else DEFAULT_SCHEMA_PATH
        self.model: Any | None = None
        self.feature_order: list[str] | None = None

    def load(self) -> bool:
        if not self.model_path.exists():
            return False
        self.model = joblib.load(self.model_path)
        if self.feature_schema_path.exists():
            self.feature_order = json.loads(self.feature_schema_path.read_text(encoding="utf-8"))
        else:
            self.feature_order = get_feature_schema()
        return True

    def is_ready(self) -> bool:
        return self.model is not None

    def score(self, feature_snapshot: dict[str, float]) -> float | None:
        if self.model is None:
            if not self.load():
                return None
        feature_order = self.feature_order or get_feature_schema()
        vector = np.array([vectorize_features(feature_snapshot, feature_order)])
        proba = self.model.predict_proba(vector)[0][1]
        return float(proba)


@lru_cache(maxsize=1)
def get_ml_ranker(
    model_path: str | Path | None = None,
    feature_schema_path: str | Path | None = None,
) -> MLRanker:
    ranker = MLRanker(model_path=model_path, feature_schema_path=feature_schema_path)
    ranker.load()
    return ranker
