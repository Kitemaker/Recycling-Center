# -*- coding: utf-8 -*-
#
from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_model.ui import SimpleCard
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model.dialog.delegate_directive import DelegateDirective
from ask_sdk_model.dialog.elicit_slot_directive import ElicitSlotDirective


import urllib.request
from urllib.parse import urlencode
from bs4 import BeautifulSoup
from bs4.element import Tag
import os


######## Convert SSML to Card text ############
# This is for automatic conversion of ssml to text content on simple card
# You can create your own simple cards for each response, if this is not
# what you want to use.

from six import PY2
try:
    from HTMLParser import HTMLParser
except ImportError:
    from html.parser import HTMLParser


class SSMLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.full_str_list = []
        if not PY2:
            self.strict = False
            self.convert_charrefs = True

    def handle_data(self, d):
        self.full_str_list.append(d)

    def get_data(self):
        return ''.join(self.full_str_list)

################################################

skill_name = "Recycle Drop-Off Finder"
launch_text = "Welcome How Can I help you today? To find recycling center you can say Find recycling center for CFL")
launch_reprompt_text = "Sorry I could not find information you are looking for.  You can say \'find recycling center for Light Bulb\'"
sorry_text = "Sorry there is some problem in getting the data. Please try again"
wrong_zip_code_text  = "At this time our coverage is limited to North America. " +\
" Unfortunately we do not have any locations outside of this area. If you live outside of North America we recommend reaching out to your city government" +\
" to find out what recycling options are available near you."
invalid_zip_text = "Zip code is not valid please tell me the zip code again."
search_page  ="https://search.earth911.com/?"
item_slot = "Item"
zip_slot = "Zip"
result_list = 0
sb = SkillBuilder()
#sb = StandardSkillBuilder(table_name="energy-product-finder", auto_create_table=True)


@sb.request_handler(can_handle_func=is_request_type("LaunchRequest"))
def launch_request_handler(handler_input: HandlerInput):
    # Handler for Skill Launch

    handler_input.response_builder.speak(launch_text).set_should_end_session(False).ask(launch_reprompt_text)
    return handler_input.response_builder.response


@sb.request_handler(can_handle_func=is_intent_name("FindLocationIntent"))
def find_light_bulb_handler(handler_input: HandlerInput):
    # Check if a product category has already been recorded in session attributes
   
    slots = handler_input.request_envelope.request.intent.slots
    item_slot_val = ""
    zip_slot_val = ""
    speech = ""
    dialogstate = handler_input.request_envelope.request.dialog_state
    intent_request = handler_input.request_envelope.request.intent    
    zip_val_valid = True
    if dialogstate.value == "STARTED" or dialogstate.value == "IN_PROGRESS":              
        handler_input.response_builder.set_should_end_session(False)
        handler_input.response_builder.add_directive(DelegateDirective(updated_intent=intent_request))   

    else:
        
        if item_slot in slots and slots[item_slot].value is not None:
            try:
                item_slot_val = int(slots[item_slot].value)
                if len(str(item_slot_val)) != 5:
                    zip_val_valid = False                    
            except:
                zip_val_valid = False
            if zip_val_valid == False:
                print("wrong zip value")
                add_card(handler_input, speech)
                handler_input.response_builder.set_should_end_session(false).speak(invalid_zip_text)     
                handler_input.response_builder.ElicitSlotDirective(updated_intent=intent_request,slot_to_elicit=zip_slot))
           
           
        
        item_slot_val = slots[item_slot].value
        zip_slot_val = slots[zip_slot].value

        result_list = get_location(item_slot_val, zip_slot_val)
        if len(result_details) > 0:
            for i in range(1):
                for k, v in result_details[i].items():
                    print(str.format("{0} =>  {1}",k,v))
                    speech = speech + str.format("{0} is {1}",k,v)
                    handler_input.response_builder.set_should_end_session(True).speak(speech)
                    add_card(handler_input, speech)
        else:
            handler_input.response_builder.set_should_end_session(True).speak(sorry_text + wrong_zip_code_text)
            add_card(handler_input, sorry_text)            
            
    return handler_input.response_builder.response


def get_location(item, zip):    
    speech_out = "Sorry there is some problem in finding the location"
    text_out = speech_out
    title, distance, contact, address,materias_accepted = str(),str(),str(),str(),str()
    try:
        if item is None:
            item = ""
        if zip is None:
            zip = ""
        values = {'what' : item, 'where' : zip, 'list_filter' : 'all', 'max_distance': '50' } 

        data = urlencode(values)
        req = urllib.request.Request(search_page + data)
        response = urllib.request.urlopen(req)
        page_out = response.read()
        soup = BeautifulSoup(page_out,'html.parser')
        address = ""
        result_details = list()
        speak_details = str()  
        count = 0
        for item in  soup.select('.result-list'):
            for result in  item.find_all('li'):
                try:
                    title = result.find(attrs={'class':'title'}).get_text()
                    distance  = result.find('span', attrs = {'class':'distance'}).get_text()
                    contact = result.find(attrs={'class':'contact'})
                    phone = contact.find( attrs = {'class':'phone'}).get_text()
                    materias_accepted = result.find(attrs={'class':'result-materials'}).text
                    materias_accepted = materias_accepted.replace("Materials accepted:", "")        
                    
                    for adr in contact.find_all('p'):
                        address = address + " " + adr.get_text()
                        loc_data = {'Name':title,
                                    'Distance': distance,
                                    'Phone':phone,
                                    'Address': address,
                                    'Materials accepted': materias_accepted.replace("Materials accepted", "")}
                        result_details.append(loc_data)

                except Exception as exc:
                    print("error in finding location details {}".fomrat(exc )       


        print(str.format("Total result found {0}",len(result_details)))
        return result_details

      
@sb.request_handler(can_handle_func=is_intent_name("AMAZON.HelpIntent"))
def help_intent_handler(handler_input):
    # Handler for Help Intent
    help_text = "I can find recycling center for items near your location. To start you can say Find recycling center for Cell Phones near 78456"
    handler_input.response_builder.speak(help_text).ask(help_text)
    return handler_input.response_builder.response


@sb.request_handler(
    can_handle_func=lambda input:
        is_intent_name("AMAZON.CancelIntent")(input) or
        is_intent_name("AMAZON.StopIntent")(input))
def cancel_and_stop_intent_handler(handler_input):
    # Single handler for Cancel and Stop Intent
    speech_text = "Goodbye!"

    return handler_input.response_builder.speak(speech_text).response


@sb.request_handler(can_handle_func=is_request_type("SessionEndedRequest"))
def session_ended_request_handler(handler_input):
    # Handler for Session End
    return handler_input.response_builder.response



@sb.request_handler(can_handle_func=is_intent_name("AMAZON.FallbackIntent"))
def fallback_handler(handler_input):
    # AMAZON.FallbackIntent is only available in en-US locale.
    # This handler will not be triggered except in that locale,
    # so it is safe to deploy on any locale
    speech = (
        "The {} skill can't help you with that.  "
        "You can tell me item and zip code by saying, "
        "Find recycling point for CFL near 79456").format(skill_name)
    reprompt = ("Please tell me the item item and zip code")
    handler_input.response_builder.speak(speech).ask(reprompt)
    return handler_input.response_builder.response


def convert_speech_to_text(ssml_speech):
    # convert ssml speech to text, by removing html tags
    s = SSMLStripper()
    s.feed(ssml_speech)
    return s.get_data()


@sb.global_response_interceptor()
def add_card(handler_input, response):
    # Add a card by translating ssml text to card content
    response.card = SimpleCard(
        title=skill_name,
        content=convert_speech_to_text(response.output_speech.ssml))


@sb.global_response_interceptor()
def log_response(handler_input, response):
    # Log response from alexa service
    print("Alexa Response: {}\n".format(response))


@sb.global_request_interceptor()
def log_request(handler_input):
    # Log request to alexa service
    print("Alexa Request: {}\n".format(handler_input.request_envelope.request))


@sb.exception_handler(can_handle_func=lambda i, e: True)
def all_exception_handler(handler_input, exception):
    # Catch all exception handler, log exception and
    # respond with custom message
    print("Encountered following exception: {}".format(exception))
    return handler_input.response_builder.response


# Handler to be provided in lambda console.
handler = sb.lambda_handler()