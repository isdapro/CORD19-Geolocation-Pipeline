import tensorflow as tf
import os
import torch
from transformers import BertForSequenceClassification, AdamW, BertConfig
from torch.utils.data import DataLoader, RandomSampler, SequentialSampler
from torch.utils.data import TensorDataset, random_split
from transformers import BertTokenizer
from helpers import splicomma, remove_special
import numpy as np

#Source code for BERT Classification inspired from https://mccormickml.com/2019/07/22/BERT-fine-tuning/

MODEL_DIR = os.path.join(os.getcwd(),'model_bert')

def initialize():
    if torch.cuda.is_available():
        # Tell PyTorch to use the GPU.
        device = torch.device("cuda")
        print('There are {} GPU(s) available.'.format(torch.cuda.device_count()))
        print('We will use the GPU:', torch.cuda.get_device_name(0))

    else:
        print('No GPU available, using the CPU instead.')
        device = torch.device("cpu")

    model = BertForSequenceClassification.from_pretrained(MODEL_DIR)
    tokenizer = BertTokenizer.from_pretrained(MODEL_DIR)
    model.to(device)

    return model,tokenizer,device


def predict(model,tokenizer,device,data):
    data['affiliate'] = data['affiliate'].apply(splicomma)
    pred_set = set()
    for i in data['affiliate']:
      for j in i:
        pred_set.add(remove_special(j))
    pred_set = list(pred_set)

    output_ids = []
    output_attention_masks = []

    for item in pred_set:
        encoded_dict = tokenizer.encode_plus(
                        item,
                        add_special_tokens = True,
                        max_length = 50,
                        pad_to_max_length = True,
                        return_attention_mask = True,
                        return_tensors = 'pt',
                   )
        output_ids.append(encoded_dict['input_ids'])

        output_attention_masks.append(encoded_dict['attention_mask'])

    output_ids = torch.cat(output_ids, dim=0)
    output_attention_masks = torch.cat(output_attention_masks, dim=0)
    batch_size = 32
    prediction_data = TensorDataset(output_ids, output_attention_masks)
    prediction_sampler = SequentialSampler(prediction_data)
    prediction_dataloader = DataLoader(prediction_data, sampler=prediction_sampler, batch_size=batch_size)

    model.eval()

    predictions , true_labels = [], []

    for batch in prediction_dataloader:
        batch = tuple(t.to(device) for t in batch)
        b_input_ids, b_input_mask = batch

        with torch.no_grad():
            outputs = model(b_input_ids, token_type_ids=None,
                          attention_mask=b_input_mask)
        logits = outputs[0]
        logits = logits.detach().cpu().numpy()
        predictions.append(logits)

    probs = tf.nn.sigmoid(np.concatenate(predictions,axis=0)[:,1])
    pred_dict=dict()
    for i in range(len(pred_set)):
      pred_dict[pred_set[i]]=probs[i]

    return pred_dict
