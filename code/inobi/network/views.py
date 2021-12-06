from inobi.network import route
from flask import request, jsonify
from flask_cors import cross_origin
import json
from inobi.network.config import ipdr_buffer, cdr_buffer


# Store reports in buffer, which will get emptied and uploaded at regular intervals
@route('/v1/ipdr', methods=['POST'])
@cross_origin()
def ipdr_report():
    if not request.is_json:
        return "Request was not JSON, try setting Content-Type to application/json", 400

    json_string = json.dumps(request.json)

    ipdr_buffer.add_item(json_string)
    return "Success", 200


@route('/v1/get_reports', methods=['GET'])
@cross_origin()
def get_all():
    ipdr = ipdr_buffer.get_all()
    cdr = cdr_buffer.get_all()
    rv = {
        "ipdr": [json.loads(a) for a in ipdr],
        "cdr": [json.loads(b) for b in cdr]
    }
    return jsonify(rv)


@route('/v1/cdr', methods=['POST'])
@cross_origin()
def cdr_report():
    if not request.is_json:
        return "Request was not JSON, try setting Content-Type to application/json", 400

    json_string = json.dumps(request.json)

    cdr_buffer.add_item(json_string)

    return "Success", 200

