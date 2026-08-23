"""Un service minimal, dont le seul travail est de rester en vie.

Il tient la place du conteneur de service que vous construirez au lab 5. Ce
qui compte ici n'est pas ce qu'il repond, c'est qu'il tourne : un conteneur
arrete n'a plus de processus, donc plus rien a observer.

Il n'utilise que la bibliotheque standard -- aucune dependance a installer,
donc aucun telechargement pendant le lab.
"""
import os
import socket
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = 8000


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = "ryvion-lab pid={} host={}\n".format(os.getpid(), socket.gethostname())
        self.send_response(200 if self.path in ("/", "/healthz") else 404)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(body.encode())

    def log_message(self, *args):
        pass  # pas de bruit dans `docker logs` : on veut pouvoir lire l'absence


if __name__ == "__main__":
    print("service demarre, pid={}".format(os.getpid()), flush=True)
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
