from elsapy.elsclient import ElsClient
from elsapy.elsprofile import ElsAuthor, ElsAffil
from elsapy.elsdoc import FullDoc, AbsDoc
from elsapy.elssearch import ElsSearch
from elsapy.elsentity import ElsEntity
from ratelimit import limits, sleep_and_retry

import requests
from tqdm import tqdm
import pandas as pd
import xml.etree.ElementTree as ElementTree

tqdm.pandas()

class CustomReader(ElsEntity):
    # static variables
    __payload_type = u'abstracts-retrieval-response'
    __uri_base = u'https://api.elsevier.com/content/abstract/'
    def __init__(self, doi_id = ''):
        super().__init__(self.__uri_base + 'doi/' + str(doi_id))

    def read(self, els_client = None):
        """Reads the JSON representation of the document from ELSAPI.
        Returns True if successful; else, False."""
        if super().read(self.__payload_type, els_client):
            return True
        else:
            return False
    @property
    def affiliation(self):
        return self.data['affiliation']


@sleep_and_retry
@limits(calls=2, period=1)
def affiliations_getter(data,client):
    ''' the data is my doi identifier '''

    l=[]
    if not isinstance(data,str):
        return l
    my_auth = CustomReader(data)
    if my_auth.read(client):
        ''' return the list'''
        try:
            aff = my_auth.affiliation
            if not aff:
                return l
            if not isinstance(aff, list):
                templist = []
                templist.append(aff)
                aff = templist
            for i in aff:
                name = ""
                city = ""
                country = ""
                try:
                    name = str(i['affilname'])
                except KeyError:
                    pass
                try:
                    city = str(i['affiliation-city'])
                except KeyError:
                    pass
                try:
                    country = str(i['affiliation-country'])
                except KeyError:
                    pass
                l.append(name+','+city+','+country)
            return l
        except KeyError:
            return l
        return l
    else:
        return l

def execute_scrape_else(df,api_key):
    client = ElsClient(api_key)
    df['affiliate'] = df.doi.progress_apply(affiliations_getter, args=(client,))
    return df
