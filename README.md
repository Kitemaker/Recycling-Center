# Recycling Center using Alexa Presentation language
## Inspiration
With over 350 materials and 100,000+ listings, earth911.com maintain one of North America's most extensive recycling databases. Sometime it is difficult to find the place where we can send the item to recycle and save the environment.
earth911.com provides extensive search engine to find recycling drop-off center for numerous type of materials. 
If someone wants to drop the material for recycling first question is where to drop-off the material so that is could be safely and efficiently recycled.
Also **[link] www.How2Recycle.info** provides a standardized labeling system that clearly communicates recycling instructions to the public. It involves a coalition of forward thinking brands who want their packaging to be recycled and are empowering consumers through smart packaging labels. Recycling labels placed on various consumer products are displayed with icons and limited texts. We need a resource which can provide quick information about the labels to the person who wants to recycle the item after consumption.  We need to know about the recycling labels

## What it does
Alexa skill " Recycling Center Finds recycling center for Drop-Off in nearby location based on user's Item and Zip Code
and items to be recycled. 
In first release of the skill "Recycling Center" , only one service was implemented i.e. to find nearby recycling center
based on item to recycle and zip code and it was only voice based skill without any support for display devices.
In the new version, following are the additional features:

(1) Interface with display is provided using 'Alexa Presentation Language' and the address of nearby recycling center is displayed also.
(2) Two more intents are added,  first intent is to provide information about recycling labels. 
To know about recycling labels user can ask " What is recycling label" . In response information about Label and its various parts are told and also displayed using "Pager" component. This information comes from 'how2recycle.info'

(3) Second new intent is about providing information for recycling process for various items. To know how to prepare items for recycling user can ask e.g. " How to recycle metal". In response to that the tips and preparation process for recycling is provided by Alexa. Also list of items for which information is available is shown to the user. By selecting item on the display user can see the information on the display about how to recycle the item. This information comes from 'earth911.com'

## How I built it
I have utilized python libraries "urllib" and "BeautifulSoup" to send the request to https://search.earth911.com/ and scrape the response to find the result list of the recycling centers near the Zip Code provided by the user.
Then using Alexa Presentation Language interface with display devices has been implemented. Information about recycling labels and its various parts are displayed using 'Pager' component. Sequence component is used to provide list of items for which recycling process tips are available. Individual items information is shown using a separate APL document
## Challenges I ran into
Scrapping the http response got from the search engine also this is my first skill based on APL
## Accomplishments that I'm proud of
I can help people in finding suitable recycling center to support the cause to  save-environment and also providing knowledge about recycling process
## What I learned
python package BeautifulSoup and Web Scrapping
## What's next for Recycling Center Finder
To automatically find nearest location, based on user's address,
Call Recycling Center,
Also to embed video of recycling process and blogs
