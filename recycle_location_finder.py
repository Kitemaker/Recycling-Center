# -*- coding: utf-8 -*-
#
from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_model.ui import SimpleCard
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model.dialog.delegate_directive import DelegateDirective
from ask_sdk_model.dialog.elicit_slot_directive import ElicitSlotDirective
from ask_sdk_model.interfaces.alexa.presentation.apl import (
    RenderDocumentDirective, ExecuteCommandsDirective, SpeakItemCommand,
    AutoPageCommand, HighlightMode)
import urllib.request
from urllib.parse import urlencode
from bs4 import BeautifulSoup
from bs4.element import Tag
import os
import json

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
launch_text = "Welcome, How can I help you today? To find recycling center you can say \"find center for desktop\""
launch_reprompt_text = "Sorry I could not find information you are looking for.  You can say \'find recycling center\'"
sorry_text = "Sorry no match found for your input. Please try again, you can say \"find center for desktop\""
wrong_zip_code_text  = "  At this time our coverage is limited to North America. " +\
" Unfortunately we do not have any locations outside of this area. If you live outside of North America we recommend reaching out to your city government" +\
" to find out what recycling options are available near you."
invalid_zip_text = "Zip code is not valid please tell me the zip code again."
search_page  = "https://search.earth911.com/?"
item_slot = "Item"
zip_slot = "Zip"
result_list = 0
sb = SkillBuilder()
#sb = StandardSkillBuilder(table_name="energy-product-finder", auto_create_table=True)

def _load_apl_document(file_path):
    # type: (str) -> Dict[str, Any]
    """Load the apl json document at the path into a dict object."""
    with open(file_path) as f:
        return json.load(f)

launch_document = _load_apl_document("launch_apl_template.json")['document']
launch_datasources = _load_apl_document("launch_apl_template.json")['datasources']

@sb.request_handler(can_handle_func=is_request_type("LaunchRequest"))
def launch_request_handler(handler_input: HandlerInput):
    # Handler for Skill Launch

    handler_input.response_builder.speak(launch_text).set_should_end_session(False).ask(
        launch_reprompt_text).add_directive(
        RenderDocumentDirective(
                token="pagerToken",
                document=launch_document,
                datasources=launch_datasources
            )
    )
    return handler_input.response_builder.response


@sb.request_handler(can_handle_func=is_intent_name("LabelInfoIntent"))
def label_info_handler(handler_input: HandlerInput):
    speech = "The How2Recycle label is a voluntary, standardized labeling system that clearly communicates recycling instructions " +\
           "to the public. It involves a coalition of forward thinking brands who want their packaging to be recycled and are empowering " +\
            "consumers through smart packaging labels. A recycling Label has four parts. Part 1 tells How to Prepare Material for Recycling. " +\
            "Part 2 is an icon which tells you whether the item falls into one of four categories - Widely Recycled, Check Locally, Not Yet Recycled and  Store Drop-Off. " +\
            "Part 3 Tells you what type of material the packaging is made of. and Part 4 Tells you the specific packaging component that the label is referring to."
    launch_datasources['bodyTemplate2Data']['textContent']['primaryText']['text'] = ""
    handler_input.response_builder.speak(speech).set_should_end_session(False).ask(
        launch_reprompt_text).add_directive(
            RenderDocumentDirective(
                token="pagerToken",
                document=_load_apl_document("apl_pager_labels.json"),
                datasources={
                    'pagerTemplateData': {
                        'type': 'object',
                        'properties': {
                            'hintString': 'find recycling center'
                        },
                        'transformers': [
                            {
                                'inputPath': 'hintString',
                                'transformer': 'textToHint'
                            }
                        ]
                    }
                }
            )
        ).add_directive(
            ExecuteCommandsDirective(
                token="pagerToken",
                commands=[
                    AutoPageCommand(
                        component_id="pagerComponentId",
                        duration=5000)
                ]
            )
        )
    return handler_input.response_builder.response


@sb.request_handler(can_handle_func=is_intent_name("HowToRecycleIntent"))
def how_to_recycle_handler(handler_input: HandlerInput):
    # Check if a product category has already been recorded in session attributes
    slots = handler_input.request_envelope.request.intent.slots

    if item_slot in slots:
        item_slot_val = slots[item_slot].value
    else:
        item_slot_val = None

    speech = ""
    dialogstate = handler_input.request_envelope.request.dialog_state
    intent_request = handler_input.request_envelope.request.intent
    zip_val_valid = True

    if dialogstate.value != "COMPLETED" and (item_slot_val is None):
        handler_input.response_builder.set_should_end_session(False)
        handler_input.response_builder.add_directive(DelegateDirective(updated_intent=intent_request))

        return handler_input.response_builder.response

    else:
        print(str.format("Getting data with values item = {0}", item_slot_val))
        speech = get_recycling_info(item_slot_val)

        if speech == "":
            speech = "Sorry, I could not find the information you are looking for. Please try again"
            handler_input.response_builder.set_should_end_session(False)
        else:
            handler_input.response_builder.set_should_end_session(True)

        info_document = _load_apl_document("apl_how_to_recycle.json")['document']
        info_datasources = _load_apl_document("apl_how_to_recycle.json")['datasources']
        handler_input.response_builder.speak(speech).add_directive(
                RenderDocumentDirective(
                    token="pagerToken",
                    document=info_document,
                    datasources=info_datasources
                )
            )

    return handler_input.response_builder.response

def get_recycling_info(item):
    data = ""
    speech_text = str()
    with open("how_to_recycle_info.json") as f:
        data = json.load(f)['recycle']

    for value in data:
        print(value)
        if item.lower() in value['item']:
            speech_text = ','.join(value['data']['tips'])
            break
    return speech_text



@sb.request_handler(can_handle_func=is_intent_name("FindLocationIntent"))
def find_location_handler(handler_input: HandlerInput):

    # Check if a product category has already been recorded in session attributes   
    slots = handler_input.request_envelope.request.intent.slots
    
    if item_slot in slots:
        item_slot_val = slots[item_slot].value
    if zip_slot in slots:
        zip_slot_val = slots[zip_slot].value
    
    speech = ""
    dialogstate = handler_input.request_envelope.request.dialog_state
    intent_request = handler_input.request_envelope.request.intent    
    zip_val_valid = True
        
    if dialogstate.value != "COMPLETED" and (item_slot_val is None or zip_slot_val is None):
        handler_input.response_builder.set_should_end_session(False)
        handler_input.response_builder.add_directive(DelegateDirective(updated_intent=intent_request))

        return handler_input.response_builder.response

    else:                        
        print(str.format("Getting data with values item ={0} and zip = {1}", item_slot_val, zip_slot_val ))

        result_list = get_location(item_slot_val, zip_slot_val)
        print("Got " + str(len(result_list)) + "results, Preparing results")

        try:
            launch_datasources['bodyTemplate2Data']['image']['sources'][0]['url'] = 'https://s3.amazonaws.com/aws-sumerian-ar/APL/location_pin_hi_res_512.png'
            launch_datasources['bodyTemplate2Data']['image']['sources'][1]['url'] = 'https://s3.amazonaws.com/aws-sumerian-ar/APL/location_pin_hi_res_512.png'
        except:
            print('error while loading images of location')
        if len(result_list) > 0:
            for k, v in result_list[0].items():
                print(str.format("{0} =>  {1}",k,v))
                speech = speech + str.format(" {0} is  {1}, ",k,v)
                launch_datasources['bodyTemplate2Data']['textContent']['primaryText']['text'] = speech
            handler_input.response_builder.set_should_end_session(True).speak(speech).add_directive(
                RenderDocumentDirective(
                    token="pagerToken",
                    document=launch_document,
                    datasources=launch_datasources
                )
            )
        else:
            launch_datasources['bodyTemplate2Data']['textContent']['primaryText']['text'] = sorry_text
            handler_input.response_builder.set_should_end_session(False).speak(sorry_text).add_directive(
                RenderDocumentDirective(
                    token="pagerToken",
                    document=launch_document,
                    datasources=launch_datasources
                )
            )
            
    return handler_input.response_builder.response


def get_location(item_data, zip):
    print('entered in the function')
    search_page  = "https://search.earth911.com/?"   
    speech_out = "Sorry there is some problem in finding the location"    
    title, distance, contact, address = str(),str(),str(),str()
    try:
        
        values = {'what' : item_data, 'where' : zip, 'list_filter' : 'all', 'max_distance': '50' } 

        data = urlencode(values)
        req = urllib.request.Request(search_page + data)
        response = urllib.request.urlopen(req, timeout=60)
        page_out = response.read()
        soup = BeautifulSoup(page_out,'html.parser')
        print("Got Response")
        result_details = list()   
        
        for item in  soup.select('.result-list'):
            for result in  item.find_all('li'):
                try:
                    title, distance, contact, phone = "Not Avialble", "Not Avialble", "Not Avialble", "Not Avialble"
                    address, addr1, addr2, addr3 = "","","",""

                    if result.find(attrs={'class':'title'}).get_text() is not None:
                        title = result.find(attrs={'class':'title'}).get_text()

                    if result.find('span', attrs = {'class':'distance'}).get_text() is not None:
                        distance  = result.find('span', attrs = {'class':'distance'}).get_text()

                    if  result.find(attrs={'class':'contact'}) is not None:
                        contact = result.find(attrs={'class':'contact'})

                        if  contact.find( attrs = {'class':'phone'}).get_text() is not None:
                            phone = contact.find( attrs = {'class':'phone'}).get_text()

                        if  contact.find( attrs = {'class':'address1'}).get_text() is not None:
                            addr1 = contact.find( attrs = {'class':'address1'}).get_text()
                        if  contact.find( attrs = {'class':'address2'}).get_text() is not None:
                            addr2 = contact.find( attrs = {'class':'address2'}).get_text()      
                        if  contact.find( attrs = {'class':'address3'}).get_text() is not None:
                            addr2 = contact.find( attrs = {'class':'address3'}).get_text()                   
                    
                    address = addr1 + addr2 + addr3
                    if address == "":
                        address = "Not Available"

                    loc_data = {'Nearby Center Name':title, 'Distance': distance, 'Phone': phone, 'Address': address.strip() }
                    result_details.append(loc_data)

                except Exception as exc:
                    print("error in finding location details {0}".format(exc))
    except Exception as exc:
            print("Error while getting information from earth911 with following exception : {0}".format(exc))


    print(str.format("Total result found {0}",len(result_details)))
    return result_details

      
@sb.request_handler(can_handle_func=is_intent_name("AMAZON.HelpIntent"))
def help_intent_handler(handler_input):
    # Handler for Help Intent
    help_text = "I can find recycling center for items near your location. To start you can say Find recycling center for cell phone"
    launch_datasources['bodyTemplate2Data']['textContent']['primaryText']['text'] = help_text
    handler_input.response_builder.speak(help_text).ask(help_text).add_directive(
                RenderDocumentDirective(
                    token="pagerToken",
                    document=launch_document,
                    datasources=launch_datasources
                )
            )
    return handler_input.response_builder.response


@sb.request_handler(
    can_handle_func=lambda input:
        is_intent_name("AMAZON.CancelIntent")(input) or
        is_intent_name("AMAZON.StopIntent")(input))
def cancel_and_stop_intent_handler(handler_input):
    # Single handler for Cancel and Stop Intent
    speech_text = "Goodbye!"
    launch_datasources['bodyTemplate2Data']['textContent']['primaryText']['text'] = speech_text
    return handler_input.response_builder.speak(speech_text).response.add_directive(
                RenderDocumentDirective(
                    token="pagerToken",
                    document=launch_document,
                    datasources=launch_datasources
                )
            )


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
        "The {0} skill can't help you with that.  "
        "You can tell me item and zip code by saying, "
        "Find recycling center for CFL").format(skill_name)
    reprompt = "You can tell me item and zip code by saying, find recycling center for CFL"
    handler_input.response_builder.speak(speech).ask(reprompt)
    return handler_input.response_builder.response


def convert_speech_to_text(ssml_speech):
    # convert ssml speech to text, by removing html tags
    s = SSMLStripper()
    s.feed(ssml_speech)
    return s.get_data()


# @sb.global_response_interceptor()
# def add_card(handler_input, response):
#     # Add a card by translating ssml text to card content
#     response.card = SimpleCard(
#         title=skill_name,
#         content=convert_speech_to_text(response.output_speech.ssml))


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
    print("Encountered following exception: {0}".format(exception))
    return handler_input.response_builder.response


# Handler to be provided in lambda console.
handler = sb.lambda_handler()
