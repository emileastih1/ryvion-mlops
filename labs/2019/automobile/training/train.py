"""Entraine le modele de regression MPG.

Archive MLOpsPython, 2019. Ce fichier est une piece a conviction : il n'a pas
ete modifie depuis, et c'est tout l'interet du lab. Ne le modernisez pas.
"""
import os

import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

HERE = os.path.dirname(__file__)
DATA_PATH = os.path.join(HERE, "..", "..", "data", "auto-mpg.csv")

FEATURES = [
    "cylinders",
    "displacement",
    "horsepower",
    "weight",
    "acceleration",
    "model year",
]
TARGET = "mpg"


def load_data(path=DATA_PATH):
    df = pd.read_csv(path)
    df = df[df["horsepower"] != "?"]
    df["horsepower"] = df["horsepower"].astype(float)
    return df


def train_model(df):
    X = df[FEATURES]
    y = df[TARGET]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    reg = LinearRegression(normalize=True)
    reg.fit(X_train, y_train)

    preds = reg.predict(X_test)
    return reg, {
        "mse": mean_squared_error(y_test, preds),
        "r2": r2_score(y_test, preds),
    }


def main():
    df = load_data()
    print("{} lignes chargees".format(len(df)))
    reg, metrics = train_model(df)
    print("MSE : {:.4f}".format(metrics["mse"]))
    print("R2  : {:.4f}".format(metrics["r2"]))


if __name__ == "__main__":
    main()
