# import uvicorn
from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import JSONResponse
import db_helper, gen_helper

app = FastAPI()

inprogress_orders = {}

#endpoint
@app.post("/")    
async def handle_request(request: Request):
    payload = await request.json()

    # TAKING KEY INFO FROM PAYLOAD(DIAGNOSTIC INFO)
    intent = payload['queryResult']['intent']['displayName']
    parameters = payload['queryResult']['parameters']
    output_contexts = payload['queryResult']['outputContexts']

    # EXTRACTING AN SESSION ID FROM OUTPUT_CONTEXT
    session_id = gen_helper.extract_session_id(output_contexts[0]["name"])

    # FLOW STARTS FROM HERE
    intent_handle_request = {
        "track.order-context:ongoing-tracking" : track_order,
        "item.add-context:ongoing-order" : add_to_order,
        "complete-order-input-context:ongoing-order" : complete_order,
        "item.remove-context:ongoing-order" : remove_from_order
    }
    
    return intent_handle_request[intent](parameters=parameters, session_id=session_id)

#REMOVING ORDER
def remove_from_order(parameters: dict, session_id: str):
    food_items = parameters["food-item"]
    food_quantity = parameters["number"]

    if len(food_quantity) != len(food_items):
        fullfillment_text = "please specify the number of item you want to remove and item should be from the order you have done"
    else:
        if session_id not in inprogress_orders.keys():
            fullfillment_text = "you haven't started order yet"
        else:
            food_items_to_be_removed = dict(zip(food_items,food_quantity))

            for food_item, food_quantity in food_items_to_be_removed.items():
                if(inprogress_orders[session_id][food_item] == food_quantity):
                    del inprogress_orders[session_id][food_item]
                else:
                    inprogress_orders[session_id][food_item] -= food_quantity
                fullfillment_text = f"{food_item} removed from order"
        
    return JSONResponse(content={
        # "inprogress_order " : inprogress_orders,
        "fulfillmentText": f"{fullfillment_text}, {inprogress_orders}"
    }) 


    # food_quantity = parameters["number"]

    # food_items_to_be_removed = dict(zip)


# AFTER COMPLETING ORDER
def complete_order(parameters: dict, session_id: str):
    if session_id not in inprogress_orders.keys():
        fullfillment_text = "I'm having a trouble finding your order. sorry! can you place a new order"
    else:
        order = inprogress_orders[session_id]
        order_id = save_to_db(order)


        if order_id == -1:
            fullfillment_text = "sorry I could not process your order due to backend error, Please place a new order again"
        else:
            order_total = db_helper.get_total_order_price(order_id=order_id)
            fullfillment_text = f"awesome. we have placed your order "\
                                f"here is your ordr id #{order_id}"\
                                f"your order total is {order_total} which you can pay at the counter"

        del inprogress_orders[session_id]

    return JSONResponse(content={
        # "inprogress_order " : inprogress_orders,
        "fulfillmentText": fullfillment_text
    })   
        
def save_to_db(order: dict):
    next_order_id = db_helper.get_next_order_id()

    for food_item, quantity_of_food in order.items():
        rcode = db_helper.insert_order_item(
            food_item,
            quantity_of_food,
            next_order_id
        )

        if rcode == -1:
            return -1

    db_helper.insert_order_tracking(next_order_id, "in progress")

    return next_order_id

# ADDING AN ORDER
def add_to_order(parameters: dict, session_id: str):
    food_items = parameters["food-item"]
    food_quantity = parameters["number"]

    if len(food_items) != len(food_quantity):
        fullfillment_text = "please specify quantity number of specified food item"
    else:
        food_dict = dict(zip(food_items,food_quantity))

        if session_id not in inprogress_orders.keys():
            inprogress_orders[session_id] = food_dict
            fullfillment_text = "order added"
        else:
            for food_item, quantity_of_item in food_dict.items():
                if food_item not in inprogress_orders[session_id].keys():
                    inprogress_orders[session_id].update({food_item : quantity_of_item})
                else:
                    inprogress_orders[session_id][food_item] += quantity_of_item

        order_str = gen_helper.get_str_from_food_dict(food_dict=inprogress_orders[session_id])
        fullfillment_text = f"so far you have {order_str}, do you want anything else?"

    return JSONResponse(content={
        # "inprogress_order " : inprogress_orders,
        "fulfillmentText": fullfillment_text
    })

# TRACKING AN ORDER WHICH NEEDS HELP FROM DATABASE
def track_order(parameters: dict, session_id: str):

    order_id = parameters['number'][0]
    order_status = db_helper.get_order_status(order_id)
    
    if order_status:
        fulfillment_text = f"The order status for order id: {order_id} is: {order_status}"
    else:
        fulfillment_text = f"no order found with order id: {order_id}"

    return JSONResponse(content={
        "fulfillmentText": f"Received =={fulfillment_text}"
    })
    
  

#  at last, the bottom of the file/module
# if __name__ == "__main__":
#     gen_helper.extract_session_id("projects/jeera-chatbot-for-food-de-n9nf/agent/sessions/93b5eb59-9613-f312-1ae0-dc8b2baf1ea6/contexts/ongoing-order")