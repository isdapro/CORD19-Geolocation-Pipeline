import pandas as pd
import os
from ast import literal_eval
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity, linear_kernel
from postal.parser import parse_address
import re
import sys

BASE_DIR = os.getcwd()
DATA_DIR = os.path.join(os.getcwd(),'data')

def scrape_map(meta):
    meta_pmc = meta[meta.pmcid.notna()]
    meta_non_pmc = meta[meta.pmcid.isna()]
    meta_else = meta_non_pmc[meta_non_pmc.source_x.str.contains("Els")]
    meta_bior=meta_non_pmc[meta_non_pmc.source_x.str.contains("bio")]
    meta_medr = meta_non_pmc[meta_non_pmc.source_x.str.contains("medr")]
    others = meta_non_pmc[meta_non_pmc.source_x.str.contains("CZI|WHO")]
    original_len = len(meta)
    mapped_len = len(meta_pmc)+len(meta_else)+len(meta_bior)+len(meta_medr)
    if original_len!=mapped_len:
        print ("Scraping logic not defined for {} rows. Contact me on github if this is a large number".format(original_len-mapped_len))

    return meta_else,meta_medr,meta_bior,meta_pmc,others

def scrape_reduce(*args,**kwargs):
    l = []
    for arg in args:
        l.append(arg)
    final_df = pd.concat(l,axis=0)
    return final_df

def scrape_diff_check(data):
    if os.path.exists(os.path.join(DATA_DIR,'scraped.csv')):
        prev_df = pd.read_csv(os.path.join(DATA_DIR,'scraped.csv'))
        if len(prev_df)==0:
            return prev_df,data

        if type(prev_df['affiliate'][0])!=list:
            prev_df['affiliate'] = prev_df['affiliate'].apply(literal_eval)
        #Handling the case when you already have the results for a newer version
        if len(prev_df)>len(data):
            print("Seems you already have the results for a version later than this")
            return prev_df,pd.DataFrame([])

        merged = data.merge(prev_df, how = 'left', left_on = 'cord_uid', right_on = 'cord_uid')
        extracted = merged[merged.affiliate.notna()][['cord_uid','source_x_x','sha_x','doi_x','affiliate']]
        to_extract = merged[merged.affiliate.isna()][['cord_uid','source_x_x','sha_x','doi_x','affiliate']]
        extracted.columns = ['cord_uid','source_x','sha','doi','affiliate']
        to_extract.columns = ['cord_uid','source_x','sha','doi','affiliate']

        return extracted,to_extract

    else:
        to_extract = data
        extracted = pd.DataFrame()
        return extracted,to_extract

def geo_diff_check(data):
    if type(data['affiliate'][0])!=list:
        data['affiliate'] = data['affiliate'].apply(literal_eval)
    data = data.explode('affiliate').reset_index()[['affiliate']]
    data = data.dropna()
    l = set()
    for i in data['affiliate']:
        j = i.replace("\n","").strip()
        if j:
            l.add(j)
    df = pd.DataFrame(list(l), columns=['affiliate'])

    if os.path.exists(os.path.join(DATA_DIR,'geolocated_affiliations.csv')):

        prev_df = pd.read_csv(os.path.join(DATA_DIR,'geolocated_affiliations.csv'))
        if len(prev_df)==0:
            return prev_df,data

        if type(prev_df['affiliate'][0])!=list:
            prev_df['affiliate'] = prev_df['affiliate'].apply(literal_eval)

        if len(prev_df)>len(df):
            print("Seems you already have the results for a version later than this")
            return prev_df,pd.DataFrame([])

        merged = df.merge(prev_df, how = 'left', left_on = 'affiliate', right_on = 'affiliate')
        extracted = merged[merged.grid_id.notna()][['affiliate','grid_id']]
        to_extract = merged[merged.grid_id.isna()][['affiliate','grid_id']]

        return extracted,to_extract

    else:
        to_extract = df
        extracted = pd.DataFrame()
        return extracted,to_extract


def remove_special(data):
    data = re.sub(r'\W+', ' ', data).lower()
    data = " ".join(data.split())
    return data

def create_tfidf_dict(df):

    def cleaner(k):
        k = re.sub(r'\W+', ' ', k).lower()
        k = " ".join(k.split())
        return k

    df['cleaned'] = df['affiliate'].apply(cleaner)
    df.dropna(subset=['cleaned'],inplace = True)
    corpus = list(df['cleaned'])
    cv = TfidfVectorizer(use_idf=True)
    docTFIDF = cv.fit_transform(corpus)
    return docTFIDF, df


def cluster_tfidf(docTFIDF,df):
    master_dict = dict()
    size = docTFIDF.shape[0]
    for i in range (0,size,500):
        print(str(((i*100)//size))+' % completed '+'\r')
        sys.stdout.flush()
        cos_sim = linear_kernel(docTFIDF[i:min(size,i+500)],docTFIDF)
        for j in range(0,cos_sim.shape[0]):
            master_dict[i+j] = list(df[cos_sim[j]>0.65].index)
    return master_dict

def splicomma(data):
    l = data.split(",")
    l2=[]
    for i in l:
        l2.append(i.lstrip(" ").rstrip(" "))
    return l2

def remove_digits(data):
    data = re.sub("\d+", "", data)
    return data

def address_parse(data):
    d = dict(parse_address(data))
    inv_map = {v:k for k,v in d.items()}
    return inv_map

def city_from_dict(data):
    if 'city' in data.keys():
        return data['city']
    else:
        return ""

def country_from_dict(data):
    if 'country' in data.keys():
        return data['country']
    else:
        return ""

def country_cleaner(data):
    if data=='usa':
        return 'united states'
    elif data=='united states of america':
        return 'united states'
    elif data=='republic of china':
        return 'china'
    elif data=='uk':
        return 'united kingdom'
    elif data=='england':
        return 'united kingdom'
    elif data=='españa':
        return 'spain'
    elif data=='the netherlands':
        return 'netherlands'
    elif data=='republic of korea':
        return 'south korea'
    elif data=='taiwan roc':
        return 'taiwan'
    elif data=='hong kong':
        return 'china'
    elif data=='republic of china':
        return 'china'
    else:
        return data

def institute_extractions(data, pred_dict):
    p = 0
    st = ""
    for i in data:
        i = remove_special(i)
        if pred_dict[i]>p and pred_dict[i]>0.1:
            st = i
            p = pred_dict[i]
    return st

def master_address_extraction(data,pred_dict):
    data['dict'] = data['cleaned'].apply(address_parse)
    data['city'] = data['dict'].apply(city_from_dict)
    data['city'] = data['city'].apply(remove_digits)
    data['country'] = data['dict'].apply(country_from_dict)
    data['country'] = data['country'].apply(country_cleaner)
    data['extracted'] = data['affiliate'].apply(institute_extractions, args=(pred_dict,))
    data = data[['affiliate','extracted','country','city']]
    return data
