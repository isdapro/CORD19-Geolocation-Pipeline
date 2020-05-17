from abc import ABC, abstractmethod
from operations import Operations
import os
import pandas as pd
from helpers import scrape_diff_check, scrape_map, scrape_reduce
from scrapers.elsev import execute_scrape_else
from scrapers.medr import execute_scrape_medr
from scrapers.bior import execute_scrape_bior
from scrapers.pmc import execute_scrape_pmc


class Scrape(Operations):
    def __init__(self, apikey, data):
        self._apikey = apikey
        self._data = data

    def execute(self):
        '''Handles the execution of the entire scraping process by calling respective functions'''

        #Use diff to split into evaluated and to-evaluate
        extracted,to_extract = scrape_diff_check(self._data)
        if len(to_extract)==0:
            return

        #Split DF into different source providers
        df_else,df_medr,df_bior,df_pmc,df_others = scrape_map(to_extract)

        #Perform scraping on all providers
        print("Scraping Elsevier...")
        df_else = execute_scrape_else(df_else, self._apikey)
        print("Elsevier Scraping Complete!")
        print("Scraping MedrXiv...")
        df_medr = execute_scrape_medr(df_medr)
        print("MedrXiv Scraping Complete!")
        print("Scraping BiorXiv...")
        df_bior = execute_scrape_bior(df_bior)
        print("BiorXiv Scraping Complete!")
        print("Scraping PMC...")
        df_pmc = execute_scrape_pmc(df_pmc)
        print("PMC Scraping Complete!")
        df_others = df_others.apply(lambda x: return [])

        #Concatenate and return full metadata
        results = scrape_reduce(df_else,df_medr,df_bior,df_pmc,df_others)
        final = pd.concat([extracted,results],axis=0)
        final.dropna(subset=['affiliate'],inplace=True)
        final.to_csv(os.path.join(os.getcwd(),'data','scraped.csv'))
