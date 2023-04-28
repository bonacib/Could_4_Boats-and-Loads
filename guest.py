from flask import Blueprint, request
from google.cloud import datastore
import json
import constants

client = datastore.Client()

bp = Blueprint('guest', __name__, url_prefix='/guests')

@bp.route('', methods=['POST','GET'])
def guests_get_post():
    if request.method == 'POST':
        content = request.get_json()
        new_guest = datastore.entity.Entity(key=client.key(constants.guests))
        new_guest.update({"name": content["name"]})
        client.put(new_guest)
        return str(new_guest.key.id)
    elif request.method == 'GET':
        query = client.query(kind=constants.guests)
        q_limit = int(request.args.get('limit', '2'))
        q_offset = int(request.args.get('offset', '0'))
        g_iterator = query.fetch(limit= q_limit, offset=q_offset)
        pages = g_iterator.pages
        results = list(next(pages))
        if g_iterator.next_page_token:
            next_offset = q_offset + q_limit
            next_url = request.base_url + "?limit=" + str(q_limit) + "&offset=" + str(next_offset)
        else:
            next_url = None
        for e in results:
            e["id"] = e.key.id
        output = {"guests": results}
        if next_url:
            output["next"] = next_url
        return json.dumps(output)


@bp.route('/<id>', methods=['PUT','DELETE'])
def guests_put_delete(id):
    if request.method == 'PUT':
        content = request.get_json()
        guest_key = client.key(constants.guests, int(id))
        guest = client.get(key=guest_key)
        guest.update({"name": content["name"]})
        client.put(guest)
        return ('',200)
    elif request.method == 'DELETE':
        key = client.key(constants.guests, int(id))
        client.delete(key)
        return ('',200)
    else:
        return 'Method not recogonized'