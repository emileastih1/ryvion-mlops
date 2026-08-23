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
    cylinders: float
    displacement: float
    horsepower: float | None = None
    weight: float
    acceleration: float
    model_year: float = Field(alias="model year")

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
