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
def affiliations(data):
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

def execute_scrape_pmc(df):
    df['affiliate'] = df.pmcid.progress_apply(affiliations)
    return df
