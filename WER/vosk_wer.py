#!/usr/bin/env python3
from multiprocessing.dummy import Pool as ThreadPool
import asyncio
import websockets
import sys
import time
import json
import os


path_sound_data = '/mnt/WORK/dialog/speech/open_stt/man_unpacked/public_youtube700_val/'
#path_sound_data = '/mnt/WORK/dialog/speech/open_stt/man_unpacked/little_Test/'
result_file_name = '/mnt/WORK/dialog/speech/open_stt/man_unpacked/shmirev_1000_you_tube.res'
uri = 'ws://localhost:8888'

async def get_res(file_name):
    async with websockets.connect(uri) as websocket:
        wf = open(file_name, "rb")
        while True:
            data = wf.read(8000)
            if len(data) == 0:
                break
            await websocket.send(data)
            await websocket.recv()
        await websocket.send('{"eof" : 1}')
        res = await websocket.recv()
        wf.close()
        return json.loads(res)['text']


def get_data(file_name):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    res_text = loop.run_until_complete(get_res(file_name[0]))
    return [file_name[0], file_name[1], res_text]

# print(get_data(sample_file_name))

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

all_files = get_all_files(path_sound_data)
print(len(all_files))


with ThreadPool(processes=1) as pool:
    f = open(result_file_name, 'w')
    count = pool.map(get_data, all_files)
    for c in count:
        f.write(c[1]+','+ c[2]+'\n')
    f.close()

