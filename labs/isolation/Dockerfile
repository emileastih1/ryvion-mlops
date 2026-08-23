# L'image du lab 2. Elle n'a rien de remarquable, et c'est voulu : tout ce que
# vous allez observer vient du noyau, pas de l'image.
#
# Une seule chose merite un commentaire, et c'est `procps`. Les images `-slim`
# ne contiennent pas `ps` : il n'y a aucune raison d'embarquer un outil de
# diagnostic dans une image de production. Nous l'ajoutons ici parce que ce lab
# consiste precisement a regarder des processus -- et 3.6 expliquera pourquoi
# l'image de service, elle, ne l'aura pas.
#
#   docker build -t ryvion-lab:obs -f labs/isolation/Dockerfile .

FROM python:3.11-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends procps \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY labs/isolation/service.py labs/isolation/hog.py ./

EXPOSE 8000

# Forme exec : python est PID 1 et recoit lui-meme les signaux, plutot que de
# les recevoir a travers un shell qui les avalerait.
CMD ["python", "service.py"]
