# DEPRECATED — ML Pipeline — Recommendation V2 (Cold Start)

This synthetic ML pipeline is kept only as historical/future-reference material.
The MVP/demo recommendation runtime is now explainable rule-based ranking and
does not load `model.pkl` or use synthetic training output.

## Mục tiêu

- Tạo pipeline ML nhẹ (Logistic Regression) chạy được khi chưa có user thật.
- Dữ liệu đầu vào là synthetic, dễ thay thế bằng logs thực tế về sau.

## Cấu trúc file

```
be/
  app/services/recommendation/ml/
    __init__.py
    feature_builder.py
    synthetic_data.py
    training_pipeline.py
    ml_ranker.py
  scripts/
    train_model.py
  ml_artifacts/
    training_dataset.csv
    model.pkl
    feature_schema.json
```

## Quy trình Offline Training (Synthetic)

1. Sinh dataset synthetic → `training_dataset.csv`.
2. Train Logistic Regression.
3. Lưu artifacts `model.pkl` + `feature_schema.json`.

Chạy lệnh:

```powershell
cd d:/DATN/be
python scripts/train_model.py --regenerate
```

Tuỳ chọn:

```powershell
python scripts/train_model.py --users 300 --quests 400 --samples-per-user 50 --seed 123
```

## Feature Consistency

- `feature_builder.py` là nguồn sự thật (feature schema + encoding).
- Training và inference đều gọi cùng một hàm `build_feature_snapshot`.

## Online Inference

- `ml_ranker.py` load model và schema từ `ml_artifacts/`.
- `RecommendationService` gọi ranker để lấy $P(complete)$.
- Nếu không tìm thấy model → fallback về rule-based.

## Integration Points (FastAPI)

- `app/services/recommendation/recommendation_service.py`
  - Tạo candidate (rule-based) → rule score → ML score → final score → rerank.
  - Log `features_snapshot`, `rule_score`, `ml_score`, `final_score` vào `recommendation_logs`.

## Thay thế bằng dữ liệu thực (roadmap)

- Thay synthetic dataset bằng export từ `recommendation_logs`.
- Giữ nguyên `feature_builder.py` và pipeline training.
- Cập nhật job scheduled để retrain định kỳ (hàng tuần/hàng tháng).
