import requests
import pymongo
import time
import keys

# TODO: replace with your own app_id and app_key
app_id = keys.app_id
app_key = keys.app_key

# Connect to mongodb database
client = pymongo.MongoClient('localhost', 27017)
db = client['dictionary']
collection = db['words']

# Fields for Oxford Dictionary API
find_id = 1763
language = 'en'
region = 'regions=gb'

# Loop that adds data to mongodb while navigating through inconsistencies in Oxford API calls examples:
# Some dictionary entries do not have definitions because they are either "derivatives of" or have "Cross References"

for x in range(3000):
    ox_word = collection.find_one({'id': str(find_id)})
    # Print ox_word for trouble shooting incase of failure so you know which entry caused failure
    print(ox_word)
    url = 'https://od-api.oxforddictionaries.com:443/api/v1/entries/' + language + '/' + ox_word['word'].lower() \
          + '/' + region
    r = requests.get(url, headers={'app_id': app_id, 'app_key': app_key})

    if '404' not in str(r):

        ox_data = r.json()

        collection.find_one_and_update(filter={'id': str(find_id)},
                                   update={"$set": {'lexicalCategory': ox_data['results'][0]
                                   ['lexicalEntries'][0]['lexicalCategory']}})

        if 'definition' in ox_data['results'][0]['lexicalEntries'][0]['entries'][0]:
            collection.find_one_and_update(filter={'id': str(find_id)},
                                   update={"$set": {'definition': ox_data['results'][0]
                                   ['lexicalEntries'][0]['entries'][0]['senses'][0]['definitions'][0]}})

        elif 'crossReferenceMarkers' in ox_data['results']:
            collection.find_one_and_update(filter={'id': str(find_id)},
                                           update={"$set": {'definition': ox_data['results'][0]
                                           ['lexicalEntries'][0]['entries'][0]['senses'][0]['crossReferenceMarkers'][0]}})

        elif'derivativeOf' in ox_data['results']:
            collection.find_one_and_update(filter={'id': str(find_id)},
                                           update={"$set": {'definition': 'derivative of ' + str(ox_data['results'][0]
                                            ['lexicalEntries'][0]['derivativeOf'][0]['text'])}})

        if 'phoneticSpelling' in ox_data['results']:
                try:
                    collection.find_one_and_update(filter={'id': str(find_id)},
                                       update={"$set": {'phonetic': ox_data['results'][0]
                                       ['lexicalEntries'][0]['pronunciations'][0]['phoneticSpelling']}})
                except KeyError:
                    collection.find_one_and_update(filter={'id': str(find_id)},
                                                   update={"$set": {'phonetic': ox_data['results'][0]['lexicalEntries']
                                                   [0]['entries'][0]['pronunciations'][0]['phoneticSpelling']}})

        elif'etymologies' in ox_data['results']:
            try:
                collection.find_one_and_update(filter={'id': str(find_id)},
                                    update={"$set": {'etymologies': ox_data['results'][0]
                                    ['lexicalEntries'][0]['entries'][0]['etymologies'][0]}})
            except KeyError:
                collection.find_one_and_update(filter={'id': str(find_id)},
                                               update={"$set": {'etymologies': ox_data['results'][0]['lexicalEntries']
                                               [0]['entries'][1]['etymologies']}})

        find_id += 1

        # time sleep based on 60 request/s for free accounts 3000 total a month 6/16/2018
        time.sleep(1)
    else:
        find_id += 1
