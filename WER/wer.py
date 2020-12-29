from tqdm import *
from jiwer import wer
from WER.russian_stt_text_normalization.normalizer import Normalizer

def LoadResults(file_name):
    f = open(file_name, 'r')
    l = f.readlines()
    f.close()
    ref = list()
    new = list()
    for ll in l:
        ll = ll.replace('\n', '')
        r = ll.split(',')
        ref.append(r[0])
        ss = len(r)
        if len(r)>2:
            string = ''
            for i in range(1, len(r)):
                string = string + r[i] + ' '
            new.append(string)
        else:
            new.append(r[1])
    return [new , ref]

def Preprocessor(data):
    result = list()

    error_counter = 0
    for dd in tqdm(data):
        norm = Normalizer(device='cpu', jit_model='russian_stt_text_normalization/jit_s2s.pt')
        str_ = dd.replace('ё', 'е').replace('-', '').lower().replace('.','')
        try:
            str_ = norm.norm_text(str_)
        except:
            print(str_)
            error_counter = error_counter + 1
        result.append(str_)
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
            if WER != 0 :
                print(hypothesis,'/', ground_truth)
            total = total + WER*words
            total_len = total_len + words
    return [total/total_len, total_len]

