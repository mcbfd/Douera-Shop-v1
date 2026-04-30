import sys
import os

# Ajouter le dossier parent au path pour importer api
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.index import app
from flask import send_from_directory

# Servir les fichiers statiques depuis la racine
@app.route('/')
def serve_index():
    return send_from_directory('../', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('../', path)

if __name__ == '__main__':
    print("Démarrage du serveur unifié (Local + API Consistency)...")
    app.run(host='0.0.0.0', port=5001, debug=True)
