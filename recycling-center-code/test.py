import urllib.request
from urllib.parse import urlencode
from bs4 import BeautifulSoup
from bs4.element import Tag
import os
import json
import requests
def get_location(item_data, zip):
    print('entered in the function')
    search_page  = "https://search.earth911.com/?"
    speech_out = "Sorry there is some problem in finding the location"
    title, distance, contact, address = str() ,str() ,str() ,str()
    try:

        values = {'what' : item_data, 'where' : zip, 'list_filter' : 'all', 'max_distance': '50' }

        data = urlencode(values)
        req = urllib.request.Request(search_page + data)
        response = urllib.request.urlopen(req, timeout=60)
        page_out = response.read()
        soup = BeautifulSoup(page_out ,'html.parser')
        print("Got Response")
        result_details = list()

        for item in  soup.select('.result-list'):
            for result in  item.find_all('li'):
                try:
                    title, distance, contact, phone = "Not Avialble", "Not Avialble", "Not Avialble", "Not Avialble"
                    address, addr1, addr2, addr3 = "" ,"" ,"" ,""

                    if result.find(attrs={'class' :'title'}).get_text() is not None:
                        title = result.find(attrs={'class' :'title'}).get_text()

                    if result.find('span', attrs = {'class' :'distance'}).get_text() is not None:
                        distance  = result.find('span', attrs = {'class' :'distance'}).get_text()

                    if  result.find(attrs={'class' :'contact'}) is not None:
                        contact = result.find(attrs={'class' :'contact'})

                        if  contact.find( attrs = {'class' :'phone'}).get_text() is not None:
                            phone = contact.find( attrs = {'class' :'phone'}).get_text()

                        if  contact.find( attrs = {'class' :'address1'}).get_text() is not None:
                            addr1 = contact.find( attrs = {'class' :'address1'}).get_text()
                        if  contact.find( attrs = {'class' :'address2'}).get_text() is not None:
                            addr2 = contact.find( attrs = {'class' :'address2'}).get_text()
                        if  contact.find( attrs = {'class' :'address3'}).get_text() is not None:
                            addr2 = contact.find( attrs = {'class' :'address3'}).get_text()

                    address = addr1 + addr2 + addr3
                    if address == "":
                        address = "Not Available"

                    loc_data = {'Nearby Center Name' :title, 'Distance': distance, 'Phone': phone, 'Address': address.strip() }
                    result_details.append(loc_data)

                except Exception as exc:
                    print("error in finding location details {0}".format(exc))
    except Exception as exc:
        print("Error while getting information from earth911 with following exception : {0}".format(exc))


    print(str.format("Total result found {0}" ,len(result_details)))
    return result_details



def get_info(item_data):
    print('entered in the function')
    search_page  = "https://earth911.com/recycling-guide/how-to-recycle-glass-bottles-jars/"
    speech_out = "Sorry there is some problem in finding the location"
    title, distance, contact, address = str() ,str() ,str() ,str()
    try:


        req = urllib.request.Request(search_page)
        response = urllib.request.urlopen(req, timeout=60)
        page_out = response.read()
        soup = BeautifulSoup(page_out ,'html.parser')
        print("Got Response")
        result_details = list()

        for item in  soup.select('.result-list'):
            for result in  item.find_all('li'):
                try:
                    title, distance, contact, phone = "Not Avialble", "Not Avialble", "Not Avialble", "Not Avialble"
                    address, addr1, addr2, addr3 = "" ,"" ,"" ,""

                    if result.find(attrs={'class' :'title'}).get_text() is not None:
                        title = result.find(attrs={'class' :'title'}).get_text()

                    if result.find('span', attrs = {'class' :'distance'}).get_text() is not None:
                        distance  = result.find('span', attrs = {'class' :'distance'}).get_text()

                    if  result.find(attrs={'class' :'contact'}) is not None:
                        contact = result.find(attrs={'class' :'contact'})

                        if  contact.find( attrs = {'class' :'phone'}).get_text() is not None:
                            phone = contact.find( attrs = {'class' :'phone'}).get_text()

                        if  contact.find( attrs = {'class' :'address1'}).get_text() is not None:
                            addr1 = contact.find( attrs = {'class' :'address1'}).get_text()
                        if  contact.find( attrs = {'class' :'address2'}).get_text() is not None:
                            addr2 = contact.find( attrs = {'class' :'address2'}).get_text()
                        if  contact.find( attrs = {'class' :'address3'}).get_text() is not None:
                            addr2 = contact.find( attrs = {'class' :'address3'}).get_text()

                    address = addr1 + addr2 + addr3
                    if address == "":
                        address = "Not Available"

                    loc_data = {'Nearby Center Name' :title, 'Distance': distance, 'Phone': phone, 'Address': address.strip() }
                    result_details.append(loc_data)

                except Exception as exc:
                    print("error in finding location details {0}".format(exc))
    except Exception as exc:
        print("Error while getting information from earth911 with following exception : {0}".format(exc))


    print(str.format("Total result found {0}" ,len(result_details)))
    return result_details



def get_recycling_info(item):
    data = ""
    speech_text = str()
    with open("how_to_recycle_info.json") as f:
        data = json.load(f)['recycle']
        print(data)
    for value in data:
        if value['item'].lower() == item.lower():
            speech_text = ','.join(value['data']['tips'])
    return speech_text
data = get_location('CFL','50123')
#data = get_recycling_info('metal')
#search_text = data[1]['Nearby Center Name'] + "," + data[0]['Address'] + " , USA"
search_text =  data[0]['Address'] + " , USA"
query = 'https://maps.googleapis.com/maps/api/staticmap?zoom=13&size=600x300&maptype=roadmap&markers=color:blue%7Clabel:S%7C40.702147,-74.015794&markers=color:green%7Clabel:G%7C40.711614,-74.012318&markers=color:red%7Clabel:C%7C40.718217,-73.998284&key=AIzaSyDKfFQStruF8z9wuvuTiv_74OL-vaC0cIU'
param = dict()
param['center'] = search_text
query = query.replace('SEARCH_TEXT_MAP', "search_text")
from  urllib.parse import urlencode
new_param = urllib.parse.urlencode(param)
res = requests.get(query,params=new_param)
print(res)