from __future__ import annotations

from pathlib import Path

import joblib
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from .ml_data_prep import build_training_dataframe


BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "models_bin"
MODEL_PATH = MODEL_DIR / "absence_model.joblib"


def train_absence_model() -> dict:
    df = build_training_dataframe()
    if df.empty:
        raise ValueError("Aucune donnée exploitable pour entraîner le modèle.")

    feature_columns = [
        "department",
        "day_of_week",
        "month",
        "age_days",
        "tenure_days",
        "tardies_last_30d",
        "absences_last_30d",
        "leaves_last_30d",
        "attendance_rate_last_30d",
        "on_approved_leave",
    ]
    target_column = "label_absent_or_late"

    X = df[feature_columns]
    y = df[target_column]

    if y.nunique() < 2:
        raise ValueError("Le dataset ne contient pas assez de classes pour entraîner un classifieur.")

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    categorical_features = ["department"]
    numeric_features = [column for column in feature_columns if column not in categorical_features]

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "cat",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("encoder", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                categorical_features,
            ),
            (
                "num",
                Pipeline(steps=[("imputer", SimpleImputer(strategy="median"))]),
                numeric_features,
            ),
        ]
    )

    model = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            (
                "classifier",
                RandomForestClassifier(
                    n_estimators=200,
                    max_depth=10,
                    min_samples_leaf=2,
                    random_state=42,
                    class_weight="balanced",
                ),
            ),
        ]
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    y_score = model.predict_proba(X_test)[:, 1]

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    artifact = {
        "model": model,
        "feature_columns": feature_columns,
        "training_rows": len(df),
    }
    joblib.dump(artifact, MODEL_PATH)

    return {
        "model_path": str(MODEL_PATH),
        "training_rows": len(df),
        "test_rows": len(X_test),
        "positive_rate": float(y.mean()),
        "roc_auc": float(roc_auc_score(y_test, y_score)),
        "classification_report": classification_report(y_test, y_pred, output_dict=True),
    }
