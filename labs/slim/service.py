"""Le service a ne pas casser.

Il ne fait presque rien, et c'est deliberе : le lab 4 porte sur la taille de
l'image, pas sur ce qu'elle contient. Ce qui compte est qu'apres chacune de vos
quatre modifications, /health reponde encore.

Il importe quand meme numpy, pandas et scikit-learn au demarrage. Sans cela,
vous pourriez retirer les dependances de l'image sans que rien ne casse -- et le
lab n'aurait plus de garde-fou.
"""
import numpy
import pandas
import sklearn
import uvicorn
from fastapi import FastAPI

app = FastAPI()


@app.get("/health")
def health():
    return {
        "status": "ok",
        "numpy": numpy.__version__,
        "pandas": pandas.__version__,
        "scikit_learn": sklearn.__version__,
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
