import re

def extract_session_id(session_str: str):
    match = re.search(r"/sessions/(.*?)/contexts/",session_str)

    if match:
        extracted_string = match.group(1)
        return extracted_string

def get_str_from_food_dict(food_dict: dict):
    return " ".join([f"{int(val)} {key}" for key,val in food_dict.items()])


if __name__ == "__main__":
    extracted_string = extract_session_id("projects/jeera-chatbot-for-food-de-n9nf/agent/sessions/93b5eb59-9613-f312-1ae0-dc8b2baf1ea6/contexts/ongoing-order")
    print(extracted_string)