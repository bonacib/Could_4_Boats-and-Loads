from flask import Blueprint, request
from google.cloud import datastore
import json
import constants

http = "http://127.0.0.1:8080"

client = datastore.Client()

bp = Blueprint('load', __name__, url_prefix='/loads')

@bp.route('', methods=['POST','GET'])
def loads_get_post():
    if request.method == 'POST':
        content = request.get_json()
        #make new entity - make a new key and provide type of key (this is a string of boats keys)
        #inspect jsons for name, type, length,
        if len(content) < 3:
            return (json.dumps({"Error" : "The request object is missing at least one of the required attributes"}),400)
        
        new_load = datastore.entity.Entity(key=client.key(constants.loads))
        #define new boat based on content passed in
        new_load.update({"volume": content["volume"], "carrier": None , "item": content["item"], 
                        "creation_date": content["creation_date"], "self": http + "/loads/"})

        #put new boat entity into databse
        client.put(new_load)

        new_load.update({"id" : new_load.key.id, "volume": content["volume"], "carrier": None, "item": content["item"], 
                        "creation_date": content["creation_date"], "self": http + "/loads/"+ str(new_load.key.id)})

        client.put(new_load)
        print("newLoad", new_load)

        #make a dictionary to return the results in the body neatly
        load_dict = {"id": new_load.key.id, "volume": content["volume"], "carrier": None, "item": content["item"], 
                        "creation_date": content["creation_date"], "self": new_load["self"]}
        #not sure why test fails here....
        print("dict", load_dict)
        
        return (json.dumps(load_dict), 201)

    elif request.method == 'GET':
        query = client.query(kind=constants.loads)
        q_limit = int(request.args.get('limit', '3'))
        q_offset = int(request.args.get('offset', '0'))
        l_iterator = query.fetch(limit= q_limit, offset=q_offset)
        pages = l_iterator.pages
        results = list(next(pages))
        if l_iterator.next_page_token:
            next_offset = q_offset + q_limit
            next_url = request.base_url + "?limit=" + str(q_limit) + "&offset=" + str(next_offset)
        else:
            next_url = None
        for e in results:
            e["id"] = e.key.id
        output = {"loads": results}
        if next_url:
            output["next"] = next_url
        return json.dumps(output)


@bp.route('/<id>', methods=['PUT','DELETE', 'GET'])
def loads_put_delete(id):
    if request.method == 'PUT':
        content = request.get_json()
        load_key = client.key(constants.loads, int(id))
        load = client.get(key=load_key)
        load.update({"name": content["name"]})
        client.put(load)
        return ('',200)
    elif request.method == 'DELETE':
        load_key = client.key(constants.loads, int(id))
        if client.get(key=load_key) == None:
            return (json.dumps({"Error" : "No load with this load_id exists"}), 404)
        load = client.get(key=load_key)

        #remove load from boat
        boat_id = load["carrier"]["id"]

        boat_key = client.key(constants.boats, int(boat_id))
        boat = client.get(key=boat_key)
        boat['loads'].remove({"id":load.id, "self": http + "/loads/" + str(id)})
        client.put(boat)    

        #delete the load
        client.delete(load_key)
        return ('',204)
    elif request.method == 'GET':
        load_key = client.key(constants.loads, int(id))
        #is the ID real?
        if client.get(key=load_key) == None:
            return (json.dumps({"Error" : "No load with this load_id exists"}), 404)
        load = client.get(key=load_key)
        load_dict = {"id" : load.key.id, "volume": load["volume"], "carrier": load["carrier"], "item": load["item"], 
                        "creation_date": load["creation_date"], "self": load["self"]}
        return (json.dumps(load_dict),200)
    else:
        return 'Method not recogonized'