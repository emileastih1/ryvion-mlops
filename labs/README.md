# Lab 1 — Autopsie d'un dépôt mort

**§3 · Conteneurisation et Docker — 20 minutes**

> **Objectif.** Reproduire la panne de 2019 dans un conteneur, constater qu'il n'y
> change rien, puis la réparer — de deux façons différentes, qui n'enseignent pas
> la même chose.

---

## Avant de commencer

| | |
|---|---|
| **Prérequis** | Docker Desktop démarré · votre fork de `ryvion-mlops` |
| **Branche** | `lab/2019-archive` |
| **Livrable** | La ligne que vous avez modifiée, et **une phrase** expliquant pourquoi elle suffit |

**À faire la veille, pas pendant le lab** — les deux images de base pèsent environ
250 Mo à elles deux, et vingt-cinq téléchargements simultanés ne passent pas :

```bash
docker pull python:3.11-slim
docker pull python:3.7-slim
```

Puis :

```bash
git checkout lab/2019-archive
```

---

## Ce que vous avez sous la main

```
labs/
├── Dockerfile.naif                     ce qu'on écrit spontanément — n'épingle rien
└── 2019/
    ├── automobile/training/train.py    le code de 2019, non modifié
    ├── requirements.txt                deux lignes, aucune version
    ├── data/auto-mpg.csv               398 voitures
    └── RESULTATS-2019.txt              lisez-le à la fin, pas avant
```

---

## Temps 1 — Reproduire la panne · 10 min

Le dépôt de 2019 est là, intact. Le réflexe raisonnable, en 2026, est de le
conteneuriser : si « ça marche sur ma machine » est le problème, l'image est la
solution. Écrivons-la naïvement — c'est-à-dire comme on l'écrit vraiment.

```bash
docker build -t autopsie:naif -f labs/Dockerfile.naif .
docker run --rm autopsie:naif
```

**Attendez-vous à un échec.** Lisez-le en entier, il est précis :

```
  File "/app/automobile/training/train.py", line 41, in train_model
    reg = LinearRegression(normalize=True)
TypeError: LinearRegression.__init__() got an unexpected keyword argument 'normalize'
```

### Les trois questions à vous poser avant de corriger

1. **Combien de lignes de code ce dépôt a-t-il perdues depuis 2019 ?** Zéro. Le
   fichier est celui de l'époque, à l'octet près — son en-tête le dit, et rien
   dans la trace d'erreur ne pointe vers une modification.
2. **Alors qu'est-ce qui a changé ?** Ouvrez `labs/2019/requirements.txt`. Il
   contient deux mots et aucun chiffre. Le conteneur a fidèlement installé *ce
   qui était disponible le jour du build* — soit, aujourd'hui, une version de
   scikit-learn où le paramètre `normalize` n'existe plus.
3. **Le conteneur vous a-t-il protégé de quoi que ce soit ?** Non. Il a reproduit
   la panne à l'identique, sur n'importe quelle machine, ce qui est d'ailleurs
   sa promesse — il reproduit. Il ne choisit pas ce qu'il reproduit.

> **Le point du lab est ici.** Conteneuriser ne rend pas reproductible.
> Conteneuriser rend *explicite* — et un environnement explicite mais non épinglé
> dérive exactement comme un environnement implicite. La différence, c'est que
> maintenant, c'est écrit dans un fichier, donc réparable.

---

## Temps 2 — Réparation A : épingler le passé · 5 min

Première réponse possible : ne pas toucher au code, restituer l'environnement.

Dans `labs/2019/requirements.txt`, épinglez la version de 2019 :

```diff
  pandas
- scikit-learn
+ scikit-learn==0.21.3
```

Reconstruisez :

```bash
docker build -t autopsie:naif -f labs/Dockerfile.naif .
```

**Cela échoue aussi**, en une dizaine de secondes, et l'erreur est ailleurs :

```
ERROR: Could not build wheels for scikit-learn
```

Il n'existe pas de *wheel* scikit-learn 0.21.3 pour Python 3.11 — cette version
est antérieure de quatre ans. `pip` tente donc de la compiler, et l'image ne
contient aucun compilateur.

Alors épinglez aussi l'image de base, dans `labs/Dockerfile.naif` :

```diff
- FROM python:3.11-slim
+ FROM python:3.7-slim
```

Reconstruisez, exécutez. **Cette fois le modèle s'entraîne.**

> **Ce que vous venez d'apprendre :** l'image de base est une dépendance, au même
> titre que les paquets. Un `requirements.txt` parfaitement épinglé au-dessus d'un
> `FROM` qui ne l'est pas ne garantit rien.

Regardez aussi ce qui s'affiche : neuf `DeprecationWarning` venant de **numpy**.
Vous avez épinglé les deux paquets que vous aviez écrits ; numpy, que personne
n'a jamais nommé, est arrivé quand même — et a bougé de son côté.

Comptez vous-même ce qu'il y a réellement dans l'image :

```bash
docker run --rm --entrypoint pip autopsie:naif list
```

Ignorez `pip`, `setuptools` et `wheel` — l'outillage d'installation est toujours
présent. Il reste **8** paquets. Vous en aviez déclaré **2**.

Les six autres sont des dépendances transitives : elles sont arrivées parce que
pandas et scikit-learn en avaient besoin, et **rien dans votre dépôt ne dit
quelle version elles doivent avoir**. C'est toute la différence entre un fichier
de dépendances et un *lock file* — et c'est pour cela que votre réparation, aussi
correcte soit-elle, ne fige encore qu'une partie de l'environnement.

---

## Temps 3 — Réparation B : avancer · 5 min

Revenez à l'état initial :

```bash
git checkout labs/
```

Deuxième réponse possible : garder l'environnement d'aujourd'hui et corriger la
ligne que la trace d'erreur désigne. Dans `labs/2019/automobile/training/train.py`,
ligne 41 :

```diff
- reg = LinearRegression(normalize=True)
+ reg = LinearRegression()
```

Reconstruisez, exécutez. **Cela fonctionne.**

### Et maintenant, la vraie question

Vous venez de supprimer un paramètre d'un modèle pour faire taire une erreur.
**Est-ce toujours le même modèle ?**

Vous ne pouvez pas répondre en regardant votre terminal. Vous ne pouvez y
répondre qu'en comparant à ce que le modèle valait *avant*.

Ouvrez maintenant `labs/2019/RESULTATS-2019.txt`, et comparez.

---

## Livrable

Une capture ou un extrait montrant :

1. **La ligne que vous avez modifiée** (réparation A ou B, au choix).
2. **Une phrase** expliquant pourquoi elle suffit — et, si vous pensez qu'elle ne
   suffit pas, dites pourquoi. C'est une réponse acceptable, et parfois la bonne.

---

## Pour aller plus loin, si vous avez fini en avance

- Comparez `labs/2019/automobile/training/train.py` avec `automobile/` sur la
  branche `main`. Cherchez ce qui est arrivé à la ligne `df[df["horsepower"] != "?"]`,
  et pourquoi elle a disparu.
- Reconstruisez `autopsie:naif` une deuxième fois sans rien changer, et
  chronométrez. D'où vient l'écart ? C'est le sujet du lab 3.
