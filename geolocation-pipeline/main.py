from abc import ABC, abstractmethod
import pandas as pd
from geolocate import Geolocate
from scrape import Scrape
import os

class Client:
    def __init__(self, apikey):
        #Initialize client with the Elsevier API key
        self._apikey = apikey

    @property
    def apikey(self):
        return self._apikey

    @apikey.setter
    def apikey(self,key):
        #Validator for API key
        self._apikey = key


    def geolocate(self,data):
        self._operation = Geolocate(data)
        self._operation.execute()

    def scrape(self,data):
        self._operation = Scrape(self._apikey,data)
        self._operation.execute()


if __name__ == '__main__':
    api = input("Please enter your Elsevier API key. If you're only going to do Geolocation you may enter a blank key: ")
    user = Client(api)
    data = pd.read_csv((os.path.join(os.getcwd(),'data','metadata.csv')))
    aff_data = pd.read_csv((os.path.join(os.getcwd(),'data','scraped.csv')))

    while True:
        print ("Enter 1 to change Elservier Key")
        print ("Enter 2 to perform Scraping on metadata")
        print ("Enter 3 to perform Geolocation on scraped.csv")
        print ("Enter 4 to exit")
        print ()
        op = int(input())
        if op==1:
            api = input("Please enter Elsevier key: ")
            user.apikey = api
        elif op==2:
            user.scrape(data)
        elif op==3:
            user.geolocate(aff_data)
        else:
            break
