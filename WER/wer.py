from tqdm import *
from WER.wer_calculation import *
file_name = '/mnt/WORK/dialog/speech/buriy_audiobooks_2_val.txt'


def LoadResults(file_name):
    f = open(file_name, 'r')
    l = f.readlines()
    f.close()
    ref = list()
    new = list()
    for ll in l:
        ll = ll.replace('\n', '')
        r = ll.split('\t')
        ref.append(r[1])
        new.append(r[2])
        # ref.append(r[1].replace('ё', 'е').replace('-', ''))
        # new.append(r[2].replace('ё', 'е').replace('-', ''))
    return [new , ref]

def Preprocessor(data):
    result = list()
    for dd in data:
        result.append(dd.replace('ё', 'е').replace('-',''))
    return result

def WER_calc(new , ref):
    total = 0.
    total_len = 0.
    for i in tqdm(range(0,len(ref))):
        ground_truth = ref[i]
        hypothesis = new[i]
        if(len(hypothesis)>0):
            words = len(ground_truth.split())
            WER = wer(hypothesis, ground_truth)
            total = total + WER*words
            total_len = total_len + words
    return [total/total_len, total_len]

