# -*- coding: utf-8 -*-
#
import ask_sdk_model.context

import ask_sdk_model.device
from ask_sdk_model.interfaces.system import system_state
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

skill_name = "Recycle Center Finder"
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
map_api_key = os.environ['MAP_API_KEY']
map_query = 'https://maps.googleapis.com/maps/api/staticmap?zoom=13&size=900x800&maptype=roadmap' +\
            '&markers=color:blue%7Clabel:S%7C40.702147,-74.015794&markers=color:green%7Clabel:G%7C40.711614,-74.012318' +\
            '&markers=color:red%7Clabel:C%7C40.718217,-73.998284&key=' + map_api_key

sb = SkillBuilder()
#sb = StandardSkillBuilder(table_name="energy-product-finder", auto_create_table=True)

def load_apl_document(file_path):
    # type: (str) -> Dict[str, Any]
    """Load the apl json document at the path into a dict object."""
    with open(file_path) as f:
        return json.load(f)

@sb.request_handler(can_handle_func=is_request_type("LaunchRequest"))
def launch_request_handler(handler_input: HandlerInput):

    # Handler for Skill Launch
    apl_doc = load_apl_document("apl_launch_recycling_center.json")
    handler_input.response_builder.speak(launch_text).set_should_end_session(False).ask(launch_reprompt_text)
    print('is_apl_supported = {0}'.format(is_apl_supported(handler_input)))
    if is_apl_supported(handler_input):
        handler_input.response_builder.add_directive(
            RenderDocumentDirective(
                token="pagerToken",
                document=apl_doc['document'],
                datasources=apl_doc['dataSources']
            )
        )

    return handler_input.response_builder.response


@sb.request_handler(can_handle_func=is_intent_name("LabelInfoIntent"))
def label_info_handler(handler_input: HandlerInput):
    print('entered into LabelInfoIntent')

    speech = "The How2Recycle label is a voluntary, standardized labeling system that clearly communicates recycling instructions " +\
           "to the public. It involves a coalition of forward thinking brands who want their packaging to be recycled and are empowering " +\
            "consumers through smart packaging labels. A recycling Label has four parts. Part 1 tells How to Prepare Material for Recycling. " +\
            "Part 2 is an icon which tells you whether the item falls into one of four categories - Widely Recycled, Check Locally, Not Yet Recycled and  Store Drop-Off. " +\
            "Part 3 Tells you what type of material the packaging is made of. and Part 4 Tells you the specific packaging component that the label is referring to."
    if is_apl_supported(handler_input):
        speech = speech + " Information about parts of label are displayed. To go back, you can say go home. To quit you can say Stop"
        handler_input.response_builder.speak(speech).set_should_end_session(False).ask(
            launch_reprompt_text).add_directive(
                RenderDocumentDirective(
                    token="pagerToken",
                    document=load_apl_document("apl_pager_labels.json")['document'],
                    datasources= load_apl_document("apl_pager_labels.json")['dataSources']
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
    else:
        handler_input.response_builder.speak(speech).set_should_end_session(True).ask(launch_reprompt_text)

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
            handler_input.response_builder.set_should_end_session(True)
        else:
            handler_input.response_builder.set_should_end_session(False)
            speech = speech + ' . You can ask for more information by saying how to recycle or say Stop to quit'

        info_document = load_apl_document("apl_how_to_recycle.json")['document']
        info_datasources = load_apl_document("apl_how_to_recycle.json")['dataSources']
        if is_apl_supported(handler_input):
            handler_input.response_builder.speak(speech).add_directive(
                    RenderDocumentDirective(
                        token="pagerToken",
                        document=info_document,
                        datasources=info_datasources
                    )
                )
        else:
            handler_input.response_builder.speak(speech)

    return handler_input.response_builder.response

def get_recycling_info(item):
    data = ""
    speech_text = str()
    with open("how_to_recycle_info.json") as f:
        data = json.load(f)['recycle']

    for value in data:
        if item.lower() in value['item']:
            speech_text = ',  '.join(value['data']['tips'])
            break
    return speech_text


def is_apl_supported(handler_input):

    if  handler_input.request_envelope.context.system.device.supported_interfaces.alexa_presentation_apl is None:
        return False
    else:
        return True

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
        location_datasources = load_apl_document('apl_location_recycling_center.json')['dataSources']
        location_document = load_apl_document('apl_location_recycling_center.json')['document']

        if len(result_list) > 0:
            # try to get the map of location using Map API

            try:

                value = urlencode({'center': result_list[0]['Nearby center name'] + ", " + result_list[0]['Address'] + ', USA'})

                print(map_query + '&' + value)
                location_datasources['bodyTemplate2Data']['image']['sources'][0]['url'] = map_query + '&' + value
                location_datasources['bodyTemplate2Data']['image']['sources'][1]['url'] = map_query + '&' + value
            except:
                location_datasources['bodyTemplate2Data']['image']['sources'][0]['url'] = ""    # No picture for Echo Spot
                location_datasources['bodyTemplate2Data']['image']['sources'][1]['url'] = 'https://s3.amazonaws.com/aws-sumerian-ar/APL/location_pin_hi_res_512.png'
                print('error while loading images of location')
            for k, v in result_list[0].items():
                print(str.format("{0} =>  {1}",k,v))
                speech = speech + str.format(" {0} is  {1}, ",k,v)
                location_datasources['bodyTemplate2Data']['textContent']['primaryText']['text'] = speech

            if is_apl_supported(handler_input):
                handler_input.response_builder.set_should_end_session(True).speak(speech).add_directive(
                    RenderDocumentDirective(
                        token="pagerToken",
                        document=location_document,
                        datasources=location_datasources
                    )
                )
            else:
                handler_input.response_builder.set_should_end_session(True).speak(speech)

        else:
            location_datasources['bodyTemplate2Data']['textContent']['primaryText']['text'] = sorry_text
            if is_apl_supported(handler_input):
                handler_input.response_builder.set_should_end_session(True).speak(sorry_text).add_directive(
                    RenderDocumentDirective(
                        token="pagerToken",
                        document=location_document,
                        datasources=location_datasources
                    )
                )
            else:
                handler_input.response_builder.set_should_end_session(True).speak(sorry_text)

            
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

                    loc_data = {'Nearby center name':title, 'Distance': distance, 'Phone': phone, 'Address': address.strip() }
                    result_details.append(loc_data)

                except Exception as exc:
                    print("error in finding location details {0}".format(exc))
    except Exception as exc:
            print("Error while getting information from earth911 with following exception : {0}".format(exc))


    print(str.format("Total result found {0}",len(result_details)))
    return result_details

@sb.request_handler(can_handle_func=is_request_type("Alexa.Presentation.APL.UserEvent"))
def alexa_user_event_request_handler(handler_input: HandlerInput):
    # Handler for Skill Launch
    arguments = handler_input.request_envelope.request.arguments
    request_type = handler_input.request_envelope.request.object_type


    if len(arguments) >= 3:
        item_selected = arguments[0]
        item_ordinal =  arguments[1]
        item_title = arguments[2]

    if item_selected == "LogoItem":
        navigate_home_handler(handler_input)
        return handler_input.response_builder.response

    if item_selected == 'HowToRecycleList':

        data_source = load_apl_document('apl_how_to_recycle_single_item.json')['dataSources']
        data_source['bodyTemplate2Data']['textContent']['title']['text'] = "How to Recycle {0}".format(item_title)
        data_source['bodyTemplate2Data']['textContent']['subtitle']['text'] = "Preparation tips before recycle"

        try:
            Items_data_how_to_recycle = load_apl_document('apl_how_to_recycle.json')['dataSources']['listTemplate1ListData']['listPage']['listItems']
            for item in Items_data_how_to_recycle:
                if item['textContent']['primaryText']['text'] ==  item_title:
                    # plane background for echo spot
                    data_source['bodyTemplate2Data']['image']['sources'][0]['url'] = "https://s3.amazonaws.com/aws-apl-contest/recyclingcenter/Image_Dark_Green.png"
                    data_source['bodyTemplate2Data']['image']['sources'][1]['url'] = item['image']['sources'][0]['url']
        except:
            print('error while fetching image in how to recycle')
        recycling_tips = get_recycling_info(item_title)
        data_source['bodyTemplate2Data']['textContent']['primaryText']['text'] = recycling_tips
        if is_apl_supported(handler_input):
            handler_input.response_builder.speak(recycling_tips).set_should_end_session(
                True).add_directive(
                RenderDocumentDirective(
                    token="listToken",
                    document=load_apl_document("apl_how_to_recycle_single_item.json")['document'],
                    datasources=data_source
                )
            )
        else:
            handler_input.response_builder.speak(recycling_tips).set_should_end_session(True)


    return handler_input.response_builder.response

def navigate_home_handler(handler_input):
    speech_text = "To start again you can say Find recycling center for cell phone"
    apl_supported = handler_input.request_envelope.context.system.device.supported_interfaces.alexa_presentation_apl
    print('apl_supported = {0}'.format(apl_supported))
    handler_input.response_builder.speak(speech_text).set_should_end_session(False)
    if is_apl_supported(handler_input):
        handler_input.response_builder.add_directive(
            RenderDocumentDirective(
                token="listToken",
                document=load_apl_document("apl_launch_recycling_center.json")['document'],
                datasources=load_apl_document("apl_launch_recycling_center.json")['dataSources']
            )
        )

@sb.request_handler(
    can_handle_func=lambda input :
        is_intent_name("AMAZON.NavigateHomeIntent")(input) or
        is_intent_name("HomeIntent")(input))
def launch_request_handler(handler_input):
    navigate_home_handler(handler_input)
    return handler_input.response_builder.response
      
@sb.request_handler(can_handle_func=is_intent_name("AMAZON.HelpIntent"))
def help_intent_handler(handler_input):
    # Handler for Help Intent
    help_text = "I can find recycling center for near your location. To start you can say Find recycling center for cell phone"
    apl_doc = load_apl_document("apl_launch_recycling_center.json")
    launch_datasources = apl_doc['dataSources']
    launch_datasources['bodyTemplate2Data']['textContent']['primaryText']['text'] = help_text
    if is_apl_supported(handler_input):
        handler_input.response_builder.speak(help_text).set_should_end_session(True).ask(help_text).add_directive(
                    RenderDocumentDirective(
                        token="pagerToken",
                        document=apl_doc['document'],
                        datasources=launch_datasources
                    )
                )
    else:
        handler_input.response_builder.speak(help_text).set_should_end_session(True).ask(help_text)

    return handler_input.response_builder.response


@sb.request_handler(
    can_handle_func=lambda input:
        is_intent_name("AMAZON.CancelIntent")(input) or
        is_intent_name("AMAZON.StopIntent")(input))
def cancel_and_stop_intent_handler(handler_input):
    # Single handler for Cancel and Stop Intent
    speech_text = "Goodbye!"
    apl_doc = load_apl_document("apl_launch_recycling_center.json")
    launch_datasources = apl_doc['dataSources']
    launch_datasources['bodyTemplate2Data']['textContent']['primaryText']['text'] = speech_text
    if is_apl_supported(handler_input):
        handler_input.response_builder.speak(speech_text).response.add_directive(
            RenderDocumentDirective(
                token="home",
                document=apl_doc['document'],
                datasources=launch_datasources
            )
        )
    else:
        handler_input.response_builder.speak(speech_text)
    return


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


# @sb.global_response_interceptor()
# def log_response(handler_input, response):
#     # Log response from alexa service
#     print("Alexa Response: {}\n".format(response))


# @sb.global_request_interceptor()
# def log_request(handler_input):
#     # Log request to alexa service
#     print("Alexa Request: {}\n".format(handler_input.request_envelope.request))


@sb.exception_handler(can_handle_func=lambda i, e: True)
def all_exception_handler(handler_input, exception):
    # Catch all exception handler, log exception and
    # respond with custom message
    print("Encountered following exception: {0}".format(exception))
    return handler_input.response_builder.response


# Handler to be provided in lambda console.
handler = sb.lambda_handler()
