from multiprocessing.dummy import Pool as ThreadPool
import os
import asyncio
import requests
import time as time_
import base64
import threading
import logging

APIKEY = ''
ASR_host = 'api.asmsolutions.ru'
MODEL = 'rus_f15_noswear'
VAD = 'microphone'
With_ASR = True


def connect_error(req):
    if req.status_code == 200:
        return False
    else:
        logging.error('error:' + str(req.status_code) + str(req.content))
        return True

def ASM_Recognition(raw_buffer):
    async_ = True
    wav_base64 = base64.b64encode(raw_buffer).decode()
    url_file = 'http://{}/file'.format(ASR_host)
    url_status = 'http://{}/task/status'.format(ASR_host)
    url_task = 'http://{}/task/result'.format(ASR_host)
    data_file = {
        'apikey': APIKEY,  # Персональный ключ
        'model': MODEL,  # Имя модели распознавания
        'wav': wav_base64,  # Бинарный контент аудиофайла
        # 'vad_model': None,  # Имя модели VAD, (без указания - данные нарезаются по 1 минуте)
        'async': async_,  # Асинхронный вариант, (по умолчанию False)
        'nbest': 1,  # Сколько nbest вариантов фраз выводить (по умолчанию 3)
    }

    result = ''
    r = requests.post(url_file, json=data_file)
    if not connect_error(r):
        if async_:
            task_id = r.json()
            data_satus = {
                'apikey': APIKEY,
                'task_id': task_id
            }
            while True:
                r = requests.post(url_status, json = data_satus)
                if connect_error(r):
                    return result
                ret = r.json()
                if ret['done'] == True:
                    break
                time_.sleep(0.25)
            r = requests.post(url_task, json = data_satus)
            if connect_error(r):
                return result
        ret = r.json()
        for res in ret:
            speech = res['speec_info']
            if 'text' in speech:
                result = result + speech['text']
    return result


def get_res(file_name):
        wf = open(file_name, "rb")
        data = wf.read(0)
        while True:
            data_read = wf.read(160)
            data = b''.join([data, data_read])
            if len(data_read) == 0:
                break
        wf.close()
        return ASM_Recognition(data)



def get_data(file_name):
    res_text = get_res(file_name[0])
    print(res_text)
    return [file_name[0], file_name[1], res_text]



def get_ref_transcription(file_name):
    f=open(file_name, 'r')
    result = f.readlines()
    res = ''
    for rr in result:
        res = rr.replace('\n','') + ' '
    if len(res) > 0:
        res = res[:-1]
    f.close()
    return res

def get_all_files(path):
    res = list()
    for root, d_names, f_names in os.walk(path):
        if len(d_names) == 0:
            for ff in f_names:
                name = ff.split('.')[0]
                if ff.split('.')[1] == 'wav':
                    res.append([root+'/'+ name+'.wav',get_ref_transcription(root+'/'+name + '.txt')])
                    if len(res)>1000:
                        return res
    return res

result_file_name = '/mnt/WORK/dialog/speech/open_stt/man_unpacked/kotov_1000_you_tube.res'

path_sound_data = '/mnt/WORK/dialog/speech/open_stt/man_unpacked/public_youtube700_val/'

all_files = get_all_files(path_sound_data)
print(len(all_files))

with ThreadPool(processes=1) as pool:
    f = open(result_file_name, 'w')
    count = pool.map(get_data, all_files)
    for c in count:
        f.write(c[1]+','+ c[2]+'\n')
    f.close()
