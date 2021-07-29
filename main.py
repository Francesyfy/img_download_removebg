from selenium import webdriver
import time
import os
import requests
import shutil

import schedule
import sys

import glob
from PIL import Image
from u2net import remove_bg

from datetime import datetime

def delete_old_images(path):
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path)
    
def get_top_trend(browser):
    query_num = 0

    url = 'https://trends.google.com/trends/trendingsearches/realtime?geo=US&category=all'
    browser.get(url)
    # wait until the page to load
    time.sleep(3)
    # find top query
    ele = browser.find_elements_by_class_name('title')
    kw = ele[query_num].text.split(' • ')[0]
    return kw

def save_image(filename, src):
    try:
        r = requests.get(src, timeout=12)

        with open(filename, 'wb') as f:
            f.write(r.content)
        f.close()
    except KeyboardInterrupt:
            sys.exit()
    except:
        return 'Request timeout'
    
    try:
        im = Image.open(filename)
        width, height = im.size
        # saved
        if width+height >= 1800:
            return 'Saved'
        # image too small
        else:
            os.remove(filename)
            return 'Invalid image'
    # invalid image
    except KeyboardInterrupt:
            sys.exit()
    except:
        os.remove(filename)
        return 'Image cannot open'
    
def download_images(browser, url, kw, num, path_d, path_t):
    browser.get(url)
    browser.maximize_window()
    
    count = 0
    
    # Scroll down to bottom
    for i in range(5):
        browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)

    # find images
    img_elements = browser.find_elements_by_xpath('//a[@class="wXeWr islib nfEiy"]')
    print('-----------------------------------------')
    print('-----------------------------------------')
    print(f'{len(img_elements)} images found for keyword: {kw}')
    print('-----------------------------------------')
    print('-----------------------------------------\n')

    for index, img_element in enumerate(img_elements[1:]):
        try:  
            # click on image
            img_element.click()
            time.sleep(0.2)

            clicked_imgs = browser.find_elements_by_xpath('//a[@class="eHAdSb"]')
            size = clicked_imgs[1].find_element_by_xpath('.//span[@class="VSIspc"]').get_attribute('innerHTML')
            w, h = size.split(' × ')
            print(f'Image {index+1} size: {size}')

            # check image sizes
            if int(w) + int(h) >= 1800 and int(w) + int(h) < 7000:
                wait = 0
                no_http = True
                while no_http and wait <= 8:
                    time.sleep(1)
                    for clicked_img in clicked_imgs:
                        src = clicked_img.find_element_by_xpath('.//img[@class="n3VNCb"]').get_attribute('src')
                        if src.startswith('http') and not src.startswith('https://encrypted-tbn0.gstatic.com'):
                            print(src)
                            no_http = False
                            break
                    wait += 1
            else:
                print('Pass')
                print('------------------')
                continue
            
            # save image to download folder
            filename = path_d + kw + '_' + str(count) + ".jpg"
            if_saved = save_image(filename, src)
            if if_saved == 'Saved':
                # remove background and save to transparent folder
                try:
                    remove_bg(filename, path_t)
                    print(f'{count+1} images saved')
                    count += 1
                    if (count >= num):
                        break
                except KeyboardInterrupt:
                    sys.exit()
                except:
                    print('Fail to remove background')
                    os.remove(filename)
            else:
                print(if_saved)
            print('------------------')

        except KeyboardInterrupt:
            sys.exit()
                
        except:
            print('Fail to get image')
            print('------------------')


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
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-infobars")
    browser = webdriver.Chrome(options=options)

    keyword = get_top_trend(browser)
    url = 'https://www.google.com/search?q='+keyword+'&tbm=isch'

    browser.close()

    # download images
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-infobars")
    browser = webdriver.Chrome(options=options)

    num = 100 # number of images to be downloaded
    download_images(browser, url, keyword, num, path_d, path_t)
    browser.close()

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
    print(f'\n************* FINISHED AT {dt_string} *************\n')


main()

# run the program every hour
schedule.clear()
schedule.every().hours.at("00:00").do(main)

while True:
    schedule.run_pending()
    time.sleep(1)