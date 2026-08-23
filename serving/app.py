"""L'API qui sert le modele produit par `src/train.py`.

Deux choses a reperer avant d'ecrire votre Dockerfile, et elles sont ici :

  * MODEL_PATH -- le chemin du dossier de modele MLflow a charger ;
  * le port 8000 -- celui sur lequel uvicorn ecoute.
"""
import os

import mlflow.pyfunc
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel, Field

MODEL_PATH = os.environ.get("MODEL_PATH", "/app/serving/model")

app = FastAPI(title="ryvion-serving", version="0.1.0")
_model = None


class Voiture(BaseModel):
    """Le format d'entree, et il n'est pas choisi au hasard.

    Les types suivent la signature que MLflow a deduite du jeu
    d'entrainement : `cylinders`, `weight` et `model year` y sont des entiers,
    les trois autres des reels. MLflow refuse de convertir un reel en entier a
    l'entree -- il considere, a juste titre, que c'est une perte silencieuse.
    Declarer `int` ici plutot que `float` est donc ce qui fait tenir le
    contrat entre l'entrainement et le service.
    """

    cylinders: int
    displacement: float
    horsepower: float | None = None
    weight: int
    acceleration: float
    model_year: int = Field(alias="model year")

    model_config = {"populate_by_name": True}


@app.on_event("startup")
def _load():
    global _model
    _model = mlflow.pyfunc.load_model(MODEL_PATH)


@app.get("/healthz")
def healthz():
    return {"status": "ok", "model_loaded": _model is not None}


@app.post("/predict")
def predict(voiture: Voiture):
    row = {
        "cylinders": voiture.cylinders,
        "displacement": voiture.displacement,
        "horsepower": voiture.horsepower,
        "weight": voiture.weight,
        "acceleration": voiture.acceleration,
        "model year": voiture.model_year,
    }
    prediction = _model.predict(pd.DataFrame([row]))
    return {"mpg": float(prediction[0])}
