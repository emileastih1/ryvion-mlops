"""Entraine le modele de consommation, et laisse MLflow tout enregistrer.

Cherchez la ligne `mlflow.sklearn.autolog()`. Il n'y a rien d'autre : pas de
log_param, pas de log_metric, pas de set_tracking_uri. C'est elle qui produit
l'experience complete que vous ouvrirez a l'etape 4.

    python -m src.train
"""
from pathlib import Path

import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

DATA = Path(__file__).resolve().parents[1] / "data" / "auto-mpg.csv"

FEATURES = [
    "cylinders",
    "displacement",
    "horsepower",
    "weight",
    "acceleration",
    "model year",
]
TARGET = "mpg"


def load_data(path=DATA):
    """Lit le CSV et remet les `?` de `horsepower` a leur place : des trous.

    Le remplissage, lui, n'est pas fait ici -- il est appris dans le pipeline,
    donc transporte avec le modele. C'est la difference entre un pretraitement
    et une fuite de donnees.
    """
    df = pd.read_csv(path)
    df["horsepower"] = pd.to_numeric(df["horsepower"], errors="coerce")
    return df


def build_pipeline():
    numeric = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="mean")),
            ("scaler", StandardScaler()),
        ]
    )
    pre = ColumnTransformer([("num", numeric, FEATURES)], remainder="drop")
    return Pipeline([("pre", pre), ("model", LinearRegression())])


def main():
    mlflow.sklearn.autolog()

    df = load_data()
    X = df[FEATURES]
    y = df[TARGET]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    with mlflow.start_run():
        pipe = build_pipeline()
        pipe.fit(X_train, y_train)

        preds = pipe.predict(X_test)
        print("{} lignes chargees".format(len(df)))
        print("MSE : {:.4f}".format(mean_squared_error(y_test, preds)))
        print("R2  : {:.4f}".format(r2_score(y_test, preds)))
        print("run_id : {}".format(mlflow.active_run().info.run_id))


if __name__ == "__main__":
    main()
