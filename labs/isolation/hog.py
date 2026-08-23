"""Alloue de la memoire, 10 Mo a la fois, et le dit a chaque fois.

Aucune subtilite : la seule chose interessante est l'endroit ou il s'arrete,
et le fait qu'il ne dise rien en s'arretant.
"""
import sys

if __name__ == "__main__":
    blocs = []
    for i in range(1, 201):
        blocs.append(bytearray(10 * 1024 * 1024))
        print("alloue {} Mo".format(i * 10), flush=True)
    print("termine sans avoir ete tue -- la limite etait trop haute", flush=True)
    sys.exit(0)
