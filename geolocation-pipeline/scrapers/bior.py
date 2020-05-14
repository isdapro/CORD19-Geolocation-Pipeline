import requests
from tqdm import tqdm
import pandas as pd
import xml.etree.ElementTree as ElementTree
from ratelimit import limits, sleep_and_retry

tqdm.pandas()

#Initializing webdriver
options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
wd = webdriver.Chrome('chromedriver',options=options)
wd.implicitly_wait(15)
wd.set_page_load_timeout(15)

def scrape_bior(data):
    find_el = wd.find_elements_by_xpath
    try:
        wd.get("https://doi.org/"+data)
        wd.get(wd.current_url+".article-info")
        l=[]
        for i in find_el("//ol[@class='affiliation-list']/li/address/span"):
            l.append(i.text)
        return l
    except:
        l=[]
        return l

def execute_scrape_bior(df):
    df['affiliate'] = df.doi.progress_apply(scrape_bior)
    return df
