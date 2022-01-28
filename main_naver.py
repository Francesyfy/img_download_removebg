import time
import os
import requests
import shutil

import sys
import urllib.request
import json

import schedule

import glob
from PIL import Image
from u2net import remove_bg

from datetime import datetime


def delete_old_images(path):
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path)
    
def get_top_trend():
    url = 'https://api.signal.bz/news/realtime'
    response = urllib.request.urlopen(url) 
    rescode = response.getcode() 
    if ( rescode == 200 ): 
        response_body = response.read()
        data = json.loads(response_body.decode('utf -8'))
        kw = data['top10'][0]['keyword']
        return kw
    else:
        print("Error Code:" + rescode)
    
def download_images(kw, num, path_d, path_t):

    count = 0 # number of saved images

    # ------- API Client ID and Secret --------
    
    client_id = "Qp4oHArxBmZlReKFDEnu" 
    client_secret = "1yX7ls4V62" 

    # https://developers.naver.com/docs/serviceapi/search/image/image.md#%EC%9D%B4%EB%AF%B8%EC%A7%80
    # -----------------------------------------
    
    for start_pos in [1+100*i for i in range(10)]:

        # ---------- Request Variables ----------
        params = {
            "query": urllib.parse.quote(kw), # keyword encoded in UTF-8
            "display": "100", # number of search results output: 10 - 100
            "start": str(start_pos), # search start positions: 1 - 1000
            "filter": "all" # large, medium, small
        }

        url = "https://openapi.naver.com/v1/search/image?" + "&".join([x[0]+"="+x[1] for x in params.items()]) 
        
        # ---------- API Request ----------
        try:
            req = urllib.request.Request(url)
            req.add_header("X-Naver-Client-Id", client_id)
            req.add_header("X-Naver-Client-Secret", client_secret)

            response = urllib.request.urlopen(req)  
            response_body = response.read()
            data = json.loads(response_body.decode('utf -8'))

        except KeyboardInterrupt:
            print(f'Number of images saved: {count+1} / {num}')
            print('KeyboardInterrupt')
            sys.exit()
        except Exception as e:
            print(f'Number of images saved: {count+1} / {num}')
            print(e)


        # ---------- Sample Output ----------
        # img_info = {
        # "title": "포토갤러리 | 공작도시 | 프로그램 | JTBC [4회] 성진家 사람들 속 자연스럽게 스며든 이설의 모습",
        # "link": "https://photo.jtbc.joins.com/prog/drama/artificialcity/Img/20211217_153013_4562.jpg",
        # "thumbnail": "https://search.pstatic.net/sunny/?src=https://photo.jtbc.joins.com/prog/drama/artificialcity/Img/20211217_153013_4562.jpg&type=b150",
        # "sizeheight": "1296",
        # "sizewidth": "864"}


        # ---------- Loop through outputs and save image ----------
        for img_info in data['items']:
            
            # filter image by size
            if int(img_info['sizewidth']) + int(img_info['sizeheight']) >= 1800:

                try:
                    # save image to download folder
                    r = requests.get(img_info['link'], timeout=12)
                    filename = path_d + kw + '_' + str(count) + ".jpg"

                    with open(filename, 'wb') as f:
                        f.write(r.content)
                    f.close()

                    # remove background and save to transparent folder
                    remove_bg(filename, path_t)
                    print(f'Number of images saved: {count+1} / {num}', end = "\r")
                    count += 1
                    if (count >= num):
                        return
                
                except KeyboardInterrupt:
                    print(f'Number of images saved: {count+1} / {num}')
                    print('KeyboardInterrupt')
                    sys.exit()
                except Exception as e:
                    # if failed to remove background
                    # remove image from download folder as well
                    print(f'Number of images saved: {count+1} / {num}')
                    print(e)
                    os.remove(filename)



def main():

    now = datetime.now()
    dt_string = now.strftime("%Y/%m/%d %H:%M:%S")
    print(f'\n************* STARTED AT {dt_string} *************\n')

    path_d = 'download/' # path to save images downloaded from google
    path_t = 'transparent/' # path to save images with background removed
    path_final = 'final/' # update at last

    # delete old images
    delete_old_images(path_d)
    delete_old_images(path_t)

    # get top query
    keyword = get_top_trend()
    print('Search keyword: ' + keyword)

    # download images
    num = 10
    download_images(keyword, num, path_d, path_t)

    # backup folders
    i = 0
    p = 'final_' + str(i) + '/'
    while os.path.exists(p):
        i += 1
        p = 'final_' + str(i) + '/'
    shutil.copytree(path_t, p)

    '''
    # duplicate transparent folder as final output
    if os.path.exists(path_final):
        shutil.rmtree(path_final)
    shutil.copytree(path_t, path_final)
    '''

    now = datetime.now()
    dt_string = now.strftime("%Y/%m/%d %H:%M:%S")
    print(f'\n\n************* FINISHED AT {dt_string} *************\n')


main()

# run the program every hour
schedule.clear()
schedule.every().hours.at("00:00").do(main)

while True:
    schedule.run_pending()
    time.sleep(1)