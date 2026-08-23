# Lab 2 — Voir l'isolation, provoquer la limite

**§3 · Conteneurisation et Docker — 20 minutes**

> **Objectif.** Constater le namespace PID depuis les deux côtés, puis provoquer
> vous-même un OOMKill et lire ce que le noyau en dit — c'est-à-dire presque rien.

---

## Avant de commencer

| | |
|---|---|
| **Prérequis** | Docker Desktop démarré · `python:3.11-slim` déjà téléchargé (lab 1) |
| **Branche** | `lab/isolation` |
| **Livrable** | Une capture du code de sortie **137**, et une phrase sur l'absence de logs |

```bash
git checkout lab/isolation
docker build -t ryvion-lab:obs -f labs/isolation/Dockerfile .
```

La construction prend quelques secondes : l'image de base est déjà sur votre
machine depuis le lab 1, et le seul ajout est `procps`.

> **Pourquoi ajouter `procps` ?** Parce que les images `-slim` ne contiennent
> pas `ps`. Ce n'est pas un oubli : un outil de diagnostic n'a rien à faire dans
> une image de production. Nous l'ajoutons ici parce que ce lab consiste
> précisément à regarder des processus — et l'image de service que vous
> construirez au lab 5, elle, ne l'aura pas. Nous verrons en 3.6 comment
> observer un conteneur qui ne contient aucun outil.

---

# Temps 1 — Le namespace PID · 8 minutes

## Étape 1 — Démarrer quelque chose qui reste en vie

```bash
docker run -d --name obs -p 8000:8000 ryvion-lab:obs
```

Un conteneur arrêté n'a plus de processus, donc plus rien à observer. Celui-ci
tient la place du service que vous construirez au lab 5.

## Étape 2 — Regarder depuis l'intérieur

```bash
docker exec obs ps -eo pid,comm
```

```
    PID COMMAND
      1 python
      7 ps
```

Deux processus, et le vôtre porte le **PID 1**. Dans un système Linux, le PID 1
est le processus d'amorçage : celui dont tous les autres descendent.

## Étape 3 — Regarder depuis l'extérieur

```bash
docker top obs
```

```
UID     PID     PPID    C   STIME   TTY   TIME       CMD
root    99940   99917   16  09:30   ?     00:00:00   python service.py
```

Le nombre sera différent chez vous, et il sera grand.

## Étape 4 — La question

**Combien de processus `python` tournent sur votre machine ?**

**Un.** Pas deux. Rien n'a été copié, rien n'a été virtualisé. Le même processus
porte deux numéros parce qu'il est vu à travers deux fenêtres différentes.

C'est le namespace `pid`, et c'est tout ce que c'est : un mensonge cohérent sur
ce que le processus voit.

Vérifiez qu'il ment aussi sur le nom de la machine :

```bash
docker exec obs hostname
```

Vous obtenez l'identifiant du conteneur, pas le nom de votre PC. C'est le
namespace `uts`, exactement le même mécanisme appliqué à autre chose.

## Étape 5 — Retirer le mensonge

Une option de `docker run` suffit à désactiver le namespace PID :

```bash
docker run --rm --pid=host ryvion-lab:obs ps -eo pid,comm
```

```
    PID COMMAND
      1 initd
     23 initd
     45 sh
     46 login
     77 bash
      …
```

**15 processus au lieu de 2.** L'isolation n'était pas une propriété du
conteneur : c'était une option, et vous venez de l'enlever.

> **Deux choses à remarquer.**
>
> - Le PID 1 n'est plus le vôtre. Il appartient au système qui héberge
>   réellement les conteneurs.
> - Ce ne sont pas les processus de votre Windows. Ce sont ceux de la **machine
>   virtuelle Linux** que Docker Desktop fait tourner — voir 3.2, dernière
>   diapositive. Vous ne voyez pas votre PC : vous voyez son hôte Linux.

---

# Temps 2 — Les cgroups · 12 minutes

Les namespaces décident de ce que le processus **voit**. Les cgroups décident de
ce qu'il **consomme**. Ce sont deux mécanismes distincts, et les confondre est
l'erreur la plus fréquente.

## Étape 6 — Ce que le noyau enregistre

```bash
docker run --rm --memory=256m --cpus=0.5 ryvion-lab:obs \
  sh -c 'cat /sys/fs/cgroup/memory.max; cat /sys/fs/cgroup/cpu.max'
```

```
268435456
50000 100000
```

- `268435456` octets, c'est exactement **256 Mio**.
- `50000 100000`, c'est **50 ms de CPU par tranche de 100 ms** — soit la moitié
  d'un cœur.

Ce ne sont pas des options de Docker. **Ce sont deux fichiers du noyau.** Docker
les écrit, le noyau les applique. Vous venez de lire ce qu'il a écrit.

## Étape 7 — Sentir la limite CPU

Lancez le même calcul trois fois, avec trois plafonds :

```bash
docker run --rm --cpus=1.0  ryvion-lab:obs python -c "import time; t=time.perf_counter(); x=0
for i in range(12_000_000): x+=i*i
print('%.2f s' % (time.perf_counter()-t))"
```

Puis la même chose avec `--cpus=0.5`, puis `--cpus=0.25`.

| `--cpus` | durée observée |
|---|---|
| 1.0 | ~0,66 s |
| 0.5 | ~1,26 s |
| 0.25 | ~2,50 s |

**On divise le CPU par deux, le temps double.** La limite n'est pas une
suggestion.

## Étape 8 — Provoquer l'OOMKill

`hog.py` alloue 10 Mo à la fois et l'annonce à chaque fois. Donnez-lui 64 Mo :

```bash
docker run --name essai --memory=64m ryvion-lab:obs python hog.py
```

Le conteneur s'arrête brutalement. Regardez où :

```bash
docker logs essai | tail -3
```

Vous verrez qu'il est allé jusqu'à **environ 120 Mo** — bien au-delà des 64
demandés. Gardez cette anomalie de côté, nous y revenons à l'étape 10.

## Étape 9 — Lire le certificat de décès

```bash
docker inspect --format '{{.State.ExitCode}}' essai
docker inspect --format '{{.State.OOMKilled}}' essai
docker inspect --format '{{.State.Error}}' essai
```

```
137
true
```

La troisième commande n'affiche **rien du tout**. Docker n'a aucun message
d'erreur à vous donner, parce qu'il n'y en a pas eu.

**137 = 128 + 9.** La convention Unix veut qu'un processus tué par le signal *n*
sorte avec le code 128 + *n*. Le signal 9 est `SIGKILL` : celui qu'un processus
ne peut ni intercepter, ni ignorer, ni retarder.

> **C'est le point du lab.** Le conteneur n'a pas planté — il a été **tué**.
> Relisez `docker logs` : la dernière ligne est parfaitement normale, puis plus
> rien. Aucune exception, aucun `MemoryError`, aucun message d'arrêt. Le
> processus a disparu entre deux lignes.
>
> Une application ne peut pas journaliser sa propre mort par `SIGKILL`. Si vous
> cherchez la cause dans les logs applicatifs, vous ne la trouverez jamais :
> elle est dans l'état du conteneur, pas dans sa sortie.

**Retenez le nombre 137.** Il reviendra au §4, devant un Pod qui redémarre en
boucle sans une ligne d'erreur dans ses logs.

## Étape 10 — L'anomalie de l'étape 8

Pourquoi le conteneur est-il monté à 120 Mo avec une limite de 64 ?

Parce que `--memory` ne plafonne pas la mémoire. Il plafonne la **mémoire
vive**, et Docker autorise par défaut autant de **swap** en plus — soit le
double au total. Vérifiez :

```bash
docker run --name essai2 --memory=64m --memory-swap=64m ryvion-lab:obs python hog.py
docker logs essai2 | tail -2
```

Cette fois, il meurt vers **50 Mo**.

> Vous avez écrit `--memory=64m` et obtenu une limite effective de 128 Mo. Le
> paramètre ne mentait pas : il ne disait simplement pas ce que vous avez cru
> lire. C'est la même leçon qu'au lab 1, appliquée aux limites plutôt qu'aux
> versions — **ce qui n'est pas déclaré explicitement prend une valeur par
> défaut que personne n'a choisie.**

---

## Nettoyage

```bash
docker rm -f obs essai essai2
```

---

## Livrable

1. **Une capture du code de sortie 137** — la sortie de
   `docker inspect --format '{{.State.ExitCode}}' essai` suffit.
2. **Une phrase sur l'absence de logs** : pourquoi l'application n'a-t-elle rien
   écrit en mourant ?

---

## Aide-mémoire des commandes

| # | Commande |
|---|---|
| 0 | `docker build -t ryvion-lab:obs -f labs/isolation/Dockerfile .` |
| 1 | `docker run -d --name obs -p 8000:8000 ryvion-lab:obs` |
| 2 | `docker exec obs ps -eo pid,comm` |
| 3 | `docker top obs` |
| 5 | `docker run --rm --pid=host ryvion-lab:obs ps -eo pid,comm` |
| 6 | `docker run --rm --memory=256m --cpus=0.5 ryvion-lab:obs sh -c 'cat /sys/fs/cgroup/memory.max'` |
| 8 | `docker run --name essai --memory=64m ryvion-lab:obs python hog.py` |
| 9 | `docker inspect --format '{{.State.ExitCode}}' essai` |
| — | `docker rm -f obs essai essai2` |

---

## Si quelque chose ne marche pas

| Ce que vous voyez | Ce qui se passe |
|---|---|
| `Conflict. The container name "/obs" is already in use` | Un conteneur du même nom existe déjà. `docker rm -f obs`, puis relancez. |
| `ps: command not found` | Vous avez lancé la commande sur une autre image que `ryvion-lab:obs`. Les images `-slim` n'ont pas `ps`. |
| `Error response from daemon: ... port is already allocated` | Le port 8000 est pris. Remplacez `-p 8000:8000` par `-p 8001:8000`, ou retirez l'option : ce lab ne s'en sert pas. |
| `docker logs essai` est vide | Le conteneur n'a pas démarré. `docker inspect --format '{{.State.Error}}' essai` vous dira pourquoi. |
| Le conteneur ne meurt pas à l'étape 8 | Votre machine autorise plus de swap. Passez directement à l'étape 10 avec `--memory-swap`. |

---

## Si vous avez fini en avance

- Refaites l'étape 2 **sans `ps`** :
  `docker exec obs cat /proc/1/comm`, puis `docker exec obs ls /proc`. Vous
  n'avez besoin d'aucun outil installé — le noyau expose tout dans un système de
  fichiers. C'est ainsi qu'on observe une image de production qui ne contient
  rien.
- Lancez `docker stats obs` dans un second terminal pendant l'étape 7. D'où
  Docker tire-t-il ces chiffres, à votre avis ?
- Relancez l'étape 8 avec `--memory=512m`. Le conteneur meurt **encore** — mais
  à quel chiffre exactement ? Vérifiez que ce chiffre confirme la règle que vous
  venez de découvrir à l'étape 10. Puis trouvez la valeur de `--memory` qu'il
  faudrait pour que `hog.py` aille jusqu'au bout de ses 2 000 Mo.
