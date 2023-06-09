#Bailey Bonaci
#Code started from CLOUD APPLICATION DEVELOPMENT (CS_493_400_S2023) materials

from flask import Blueprint, request
from google.cloud import datastore
import json
import constants

http = "http://127.0.0.1:8080"

client = datastore.Client()

bp = Blueprint('boat', __name__, url_prefix='/boats')

@bp.route('', methods=['POST','GET'])
def boats_get_post():
    if request.method == 'POST':
        content = request.get_json()    
        if len(content) < 3:
            return (json.dumps({"Error" : "The request object is missing at least one of the required attributes"}),400)
        
        new_boat = datastore.entity.Entity(key=client.key(constants.boats))
        #define new boat based on content passed in
        new_boat.update({"name": content["name"], "type": content["type"], "length": content["length"], 
                        "loads": [], "self": http + "/boats/"})
        #put new boat entity into databse
        client.put(new_boat)

        #update entry with self - need ID for self so this has to be done 2 times
        new_boat.update({"id" : new_boat.key.id, "name": content["name"], "type": content["type"], "length": content["length"], 
                    "loads": [], "self": http + "/boats/" + str(new_boat.key.id)})  
        client.put(new_boat)
        #make a dictionary to return the results in the body neatly
        boat_dict = {"id" : new_boat.key.id, "name" : new_boat["name"], "type" : new_boat["type"], 
                     "length" : new_boat["length"], "loads" : new_boat["loads"], 
                     "self": new_boat["self"]}
        return (json.dumps(boat_dict), 201)
    elif request.method == 'GET':
        query = client.query(kind=constants.boats)
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
        output = {"boats": results}
        if next_url:
            output["next"] = next_url
        return json.dumps(output)
    else:
        return 'Method not recogonized'

@bp.route('/<id>', methods=['PUT','DELETE', 'GET'])
def boats_put_delete(id):
    if request.method == 'PUT':
        content = request.get_json()
        # boat_key = client.key(constants.boats, int(id))
        # boat = client.get(key=boat_key)
        # boat.update({"name": content["name"], "description": content["description"],
        #   "price": content["price"]})
        # client.put(boat)
        # return ('',200)
    elif request.method == 'DELETE':
        boat_key = client.key(constants.boats, int(id))
        if client.get(key=boat_key) == None:
            return (json.dumps({"Error" : "No boat with this boat_id exists"}), 404)
        #THIS NEEDS WORK - THIS IS WHERE YOU LEFT OFF
        
        boat = client.get(key=boat_key)
        #and unload any loads assiciated
        for item in boat['loads']:
            item_id = item["id"]
            load_key = client.key(constants.loads, int(item_id))
            load = client.get(key=load_key)
            load['carrier'] = None
            client.put(load)        

        # delete boat
        client.delete(boat_key)
        return ('',204)
    elif request.method == 'GET':
        boat_key = client.key(constants.boats, int(id))
        #is the ID real?
        if client.get(key=boat_key) == None:
            return (json.dumps({"Error" : "No boat with this boat_id exists"}), 404)
        boat = client.get(key=boat_key)
        boat_dict = {"id" : boat.key.id, "name" : boat["name"], "type" : boat["type"], 
                     "length" : boat["length"], "loads" : boat["loads"], 
                     "self": boat["self"]}
        print("this is the boat", boat, "this is the boat dict", boat_dict)
        return (json.dumps(boat_dict),200)
    else:
        return 'Method not recogonized'

@bp.route('/<bid>/loads/<lid>', methods=['PUT','DELETE'])
def add_delete_reservation(bid,lid):
    if request.method == 'PUT':
        boat_key = client.key(constants.boats, int(bid))
        load_key = client.key(constants.loads, int(lid))

        #check if boat and load exist
        if client.get(key=boat_key) == None or client.get(key=load_key) == None:
            return (json.dumps({"Error" : "The specified boat and/or load does not exist"}), 404)
        
        
        load = client.get(key=load_key)
        #check if load is already else where
        if load['carrier'] != None:
            return (json.dumps({"Error" : "The load is already loaded on another boat"}), 403)
        
        #load not on other boat
        #get the boat
        boat = client.get(key=boat_key)
        
        boat['loads'].append({"id":load.id, "self": http + "/loads/" + str(load.id)})

        client.put(boat)

        #update the load with the carrier
        load['carrier'] = ({ "id" : str(boat.id), "name": boat["name"], "self": http + "/boats/" + str(boat.id)})
        client.put(load)

        return('',204)
    if request.method == 'DELETE':
        #get Keys
        boat_key = client.key(constants.boats, int(bid))
        load_key = client.key(constants.loads, int(lid))

        #check if boat and load exist
        if client.get(key=boat_key) == None or client.get(key=load_key) == None:
            return (json.dumps({"Error" : "No boat with this boat_id is loaded with the load with this load_id"}), 404)
        
        
        load = client.get(key=load_key)
        #check if load is already removed
        if load['carrier'] == None:
            return (json.dumps({"Error" : "No boat with this boat_id is loaded with the load with this load_id"}), 404)
        
        #find the carrier boat
        boat = client.get(key=boat_key)
        
        print("boat loads before removal", boat['loads'])
        boat['loads'].remove({"id":load.id, "self": http + "/loads/" + str(load.id)})
        print("boat loads after removal", boat['loads'])

        client.put(boat)

        #update the load to have no carrier
        load['carrier'] = None
        client.put(load)
        return('',204)

@bp.route('/<id>/loads', methods=['GET'])
def get_reservations(id):
    boat_key = client.key(constants.boats, int(id))
    if client.get(key=boat_key) == None:
            return (json.dumps({"Error" : "No boat with this boat_id exists"}), 404)
    boat = client.get(key=boat_key)
    load_ids  = []
    for load in boat['loads']:
        #get all the ids of the loads
        load_ids.append(load["id"])
    list_loads = []
    for load_id in load_ids:
        print("Round: ", load_id)
        load_key = client.key(constants.loads, int(load_id))
        load = client.get(key=load_key)
        list_loads.append({"id": load["id"], "volume": load["volume"],  "item": load["item"], 
                        "creation_date": load["creation_date"], "self": load["self"]})
    results_dict = {}
    results_dict["loads"] = list_loads
    #then with all the ids display the contents of the loads
    return results_dict
    