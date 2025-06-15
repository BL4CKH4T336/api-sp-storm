from flask import Flask, request, jsonify
import re

app = Flask(__name__)

@app.route('/gate=stripe4/keydarkwaslost/cc=<path:cc>')
def check_card(cc):
    # Always return static response
    return jsonify({
        "cc": cc,
        "response": "Soon",
        "status": "Declined"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
