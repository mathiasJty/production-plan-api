from flask import Flask, request, jsonify

import json
import logging
from production_plan import production_plan

app = Flask(__name__)


@app.route("/productionplan", methods=["POST"])
def planification():
    if request.method == 'POST':
        try:
            payload = request.get_json()
            result = production_plan(payload)
            return jsonify({'status': 'success', 'result': result})
        except json.decoder.JSONDecodeError as e:
            logging.error(e)
            return jsonify({'status': 'error', 'message': 'Invalid JSON payload'}), 400
        except Exception as e:
            logging.error(e)
            return jsonify({'status': 'error', 'message': 'An error occured'}), 500


if __name__ == '__main__':
    app.run(port=8888)
