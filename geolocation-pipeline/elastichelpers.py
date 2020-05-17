import json
import requests
from elasticsearch import Elasticsearch, helpers
from queue import Queue
from threading import Thread
import threading
import os
import pandas as pd

with open('querytemplate.txt','r') as file:
    template = file.read().replace('\n','')
master_dict = dict()
es = Elasticsearch([{'host':'localhost', 'port': 9200, 'request_timeout': 30, 'index.refresh_interval':60}])
lock = threading.Lock()

def create_index():
    print("Creating your BERT index on Localhost..")
    es = Elasticsearch([{'host':'localhost', 'port': 9200, 'request_timeout': 30, 'index.refresh_interval':60}])
    with open(os.path.join(os.getcwd(),'data','grid.json'), encoding = 'utf-8') as f:
      data = json.load(f)
    data = data['institutes']
    helpers.bulk(es, data, index='grid-test',doc_type='_doc', request_timeout=200)
    print("Done..")



def elastic_query(index, bert_magic):
    qdict = dict()
    qdict["source"] = template
    qdict["params"] = dict()
    qdict["params"]["country"] = ""
    qdict["params"]["institute"] = ""
    qdict["params"]["city"] = ""

    #Full Query
    qdict["params"]["country"] += bert_magic['country'][index]
    qdict["params"]["city"] += bert_magic['city'][index]
    qdict["params"]["institute"] += bert_magic['extracted'][index]

    if qdict["params"]["institute"]=="":
        return {'hits':{'hits':[]}}

    res = es.search_template(index='grid-test',body = qdict)
    if len(res)>0:
        return res

    #Medium Query
    qdict["params"]["city"] = ""
    res = es.search_template(index='grid-test',body = qdict)
    if len(res)>0:
        return res

    #Weak query
    qdict["params"]["country"] = ""
    res = es.search_template(index='grid-test',body = qdict)
    return res

def mapper(index, bert_magic, cluster_dict):
    score_dict = dict()
    for i in cluster_dict[index]:
        res = elastic_query(i,bert_magic)
        '''if len(res['hits']['hits'])==0:
            return "not found"
        res = res['hits']['hits'][0]
        score = res['_score']
        grid_id = res['_source']['id']
        return grid_id'''
        for item in range(len(res['hits']['hits'])):
            score = res['hits']['hits'][item]['_score']
            grid_id = res['hits']['hits'][item]['_source']['id']
            if grid_id not in score_dict.keys():
                score_dict[grid_id] = score
            else:
                score_dict[grid_id]+=score
    if len(score_dict)==0:
        return "not found"
    else:
        return list({k:v for k,v in sorted(score_dict.items(), key=lambda item: item[1])}.keys())[-1]


class Worker(Thread):
    def __init__(self, queue, bert_magic, cluster_dict):
        Thread.__init__(self)
        self.queue = queue
        self.bert_magic = bert_magic
        self.cluster_dict = cluster_dict


    def run(self):
        while True:
            idx = self.queue.get()
            try:
                val = mapper(idx,self.bert_magic,self.cluster_dict)
                with lock:
                    master_dict[idx] = val
                    if (idx%10000==0):
                        print ("Done for {} values".format(idx))
            finally:
                self.queue.task_done()

def elastic_main(cluster_dict,bert_magic):

    queue = Queue()
    for w in range(8):
        worker = Worker(queue,bert_magic,cluster_dict)
        worker.daemon = True
        worker.start()
    for i in range(len(bert_magic)):
        queue.put(i)

    queue.join()

    print("Just doing some final operations now...")

    geo = pd.DataFrame(master_dict.items(), columns=['idx','grid_id'])
    geo['idx'] = geo['idx'].astype(str).astype(int)
    bert_magic['idx'] = bert_magic.index
    merged = bert_magic.merge(geo,how='left',left_on='idx',right_on='idx')[['affiliate','grid_id']]
    add = pd.read_csv(os.path.join(os.getcwd(),'data','addresses.csv'))
    final  = merged.merge(add,how='left',left_on='grid_id',right_on='grid_id')

    '''Potentially we can allow a Diff check by uncommenting the following line, however, I am investigating the
    fact that a diff check could undermine the clustering approach and result in a hit on accuracy. So, for the time
    being it has been commented out'''
    
    #final.to_csv(os.path.join(os.getcwd(),'data','geolocated_affiliations.csv'))

    return final
