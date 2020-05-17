from abc import ABC, abstractmethod
from operations import Operations
import pandas as pd
from helpers import geo_diff_check
from helpers import create_tfidf_dict, cluster_tfidf, master_address_extraction
from berthelpers import initialize, predict
from elastichelpers import create_index, elastic_main
import os

class Geolocate(Operations):
    def __init__(self,data):
        self._data = data

    def execute(self):
        '''We will call various functions to execute the geolocation pipeline'''
        print ("Starting geolocation...")
        extracted,to_extract = geo_diff_check(self._data)

        if len(to_extract)==0:
            t1 = self._data.explode('affiliate').reset_index()[['cord_uid','affiliate']]
            t1.dropna(subset=['affiliate'],inplace=True)
            t1['affiliate'] = t1['affiliate'].apply(lambda i: i.replace("\n","").strip())
            to_return = t1.merge(extracted,how='left',left_on='affiliate',right_on='affiliate')[['cord_uid','affiliate','grid_id','geonames_city_id','institute_name','lat','lng','city','state','state_code','country']]

            to_return.to_csv(os.path.join(os.getcwd(),'data','geolocated_full_metadata.csv'))
            print("Geolocation DONE!")
            return


        print("Clustering similar affiliations...")
        docTFIDF, df = create_tfidf_dict(to_extract)
        master_dict = cluster_tfidf(docTFIDF,df)

        print ("TF-IDF generated! Let's move to BERT stuff now..")

        model,tokenizer,device = initialize()
        pred_dict = predict(model,tokenizer,device,df)
        df = master_address_extraction(df,pred_dict)

        print ("BERT stuff done! Moving on to the final stage of ElasticSearch")
        create_index()
        results = elastic_main(master_dict,df)
        final = pd.concat([extracted,results],axis=0)

        t1 = self._data.explode('affiliate').reset_index()[['cord_uid','affiliate']]
        t1.dropna(subset=['affiliate'],inplace=True)
        t1['affiliate'] = t1['affiliate'].apply(lambda i: i.replace("\n","").strip())
        to_return = t1.merge(final,how='left',left_on='affiliate',right_on='affiliate')[['cord_uid','affiliate','grid_id','geonames_city_id','institute_name','lat','lng','city','state','state_code','country']]

        to_return.to_csv(os.path.join(os.getcwd(),'data','geolocated_full_metadata.csv'))
        print("Geolocation DONE!")
