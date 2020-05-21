import requests
from tqdm import tqdm
import pandas as pd
import xml.etree.ElementTree as ElementTree
from ratelimit import limits, sleep_and_retry

tqdm.pandas()

def node_text(node):
    if node.text:
        result = node.text
    else:
        result = ''
    for child in node:
        if child.tail is not None:
            result += child.tail
    return result

@sleep_and_retry
@limits(calls=2, period=1)
def affiliations_pmc(data):
    try:
        PMC_ID = data.lstrip('PMC')
        response = requests.get('https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id='+PMC_ID, timeout = 10)
        root = ElementTree.fromstring(response.content)
        l=[]
        for i in root.iter('aff'):
          l.append(node_text(i))
        return l
    except:
        l=[]
        return l

@sleep_and_retry
@limits(calls=2, period=1)
def affiliations_pubmed(data):
    try:
        PUBMED_ID = int(data)
        response = requests.get('https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id='+str(PUBMED_ID)+'&retmode=XML', timeout = 10)
        root = ElementTree.fromstring(response.content)
        l=[]
        for i in root.iter('Affiliation'):
          l.append(node_text(i))
        return l
    except:
        l=[]
        return l

def main_funct(data):
    if pd.isnull(data['pmcid']):
        data['affiliate'] = affiliations_pubmed(data['pubmed_id'])
    else:
        data['affiliate'] = affiliations_pmc(data['pmcid'])
    return data


def execute_pmc_main(df):
    df.progress_apply(main_funct, axis=1)
    return df
