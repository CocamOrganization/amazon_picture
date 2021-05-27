import requests
from user_agents import user_agents
from lxml import etree
import random
from threading import Thread, Lock
import queue
import re
# import io
import csv
import time


class amazon_p(object):

    def check(self, reason, asin, text):
        '''将抓取失败的html文件保存到本地，分析原因'''
        path = 'D:/test/' + reason+ '/' + asin + '.html'
        with open(path, 'w', encoding='utf-8') as f:
            f.write(text)

    def get_response(self, url, retries=0):
        '''获取html代码'''
        retries += 1
        if retries > 10:
            print('超过最大重试次数:{url}'.format(url=url))
            return {'rp': None, 'url': url, 'result': 'FAIL'}
        headers = {'user-agent': random.choice(user_agents),
                    }
        try:
            response = requests.get(url, headers=headers, timeout=5)
            if 'Robot Check' in response.text:
                print('出现验证码,更换ip:{url}'.format(url=url))
                time.sleep(random.randint(1, 3))
                return self.get_response(url, retries)
            elif 'Enter the characters you see below' in response.text:
                print('出现验证码,更换ip:{url}'.format(url=url))
                time.sleep(random.randint(1, 3))
                return self.get_response(url, retries)
            elif response.status_code == 404:
                print('Page Not Found: {url}'.format(url=url))
                return {'rp': response, 'url': url, 'result': 'NG1'}
            elif response.status_code == 200:
                print('成功获取页面：{url}'.format(url=url))
                return {'rp': response, 'url': url, 'result': 'OK'}
            elif response.status_code == 503:
                print('出现503错误：{url}'.format(url=url))
                # self.check('unknown', '503', text)
                time.sleep(random.randint(1, 3))
                return self.get_response(url, retries)
            else:
                print('出现未知类型的错误：{url}'.format(url=url))
                return {'rp': 'failed', 'url': url, 'result': 'FAIL'}
                # self.check('unknown', url, text)
        except:
            print('连接超时，准备重试')
            time.sleep(random.randint(1, 3))
            return self.get_response(url, retries)

    def check_html(self, response):
        asin = response['url'].split('/')[-1].strip('\n')
        if response['result'] == 'OK':
            html = etree.HTML(response['rp'].text)
            asin1 = html.xpath('//th[contains(text(),  "ASIN")]/following-sibling::*[1]/text()')
            if len(asin1) == 0:
                yield {'asin': asin, 'result': 'NG2'}
            else:
                asin1 = asin1[0].strip('\n')
                if asin1 == asin:
                    jpgs1 = html.xpath('//span[@class="a-button-text"]//img[contains(@src, "jpg")]/@src')
                    # jpgs2 = html.xpath('//img[@class="product-image"]/@src')
                    # jpgs3 = jpgs1 + jpgs2
                    jpgs = []
                    for j in jpgs1:
                        pattern = j + '.*?"main":\{"(.*?jpg)"'
                        ju = re.search(pattern, response['rp'].text).group(1)
                        jpgs.append(ju.strip('\n'))
                    if len(jpgs) == 0:
                        yield {'asin': asin, 'result': 'No_Image'}
                    for i, jpg_url in enumerate(jpgs):
                        jpg_name = [f'{asin}.jpg' if i == 0 else f'{asin}_{i}.jpg'][0]
                        jpg_rp = self.get_response(jpg_url)
                        if jpg_rp['result'] == 'OK':
                            yield {'asin': asin, 'result': 'OK', 'rp': jpg_rp['rp'], 'name': jpg_name}
                        else:
                            yield {'asin': asin, 'result': 'jpg_FAIL'}
                else:
                    yield {'asin': asin, 'result': 'NG2'}
        elif response['result'] == 'NG1':
            yield {'asin': asin, 'result': 'NG1'}

    def save_img(self, results):
        self.record_inf(results)
        # print(results)
        if results['result'] == 'OK':
            name = results['name']
            if '_' in name:
                with open(f'imgs/side_picture/{name}', 'wb') as f:
                    f.write(results['rp'].content)
            else:
                with open(f'imgs/main_picture/{name}', 'wb') as f:
                    f.write(results['rp'].content)

    def record_inf(self, results):
        with open('records.csv', 'a', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([results['asin'], results['result'], results.get('name', None)])

q = queue.Queue()
lock = Lock()

def main(q):
    while q.empty() is not True:
        lock.acquire()  # 加锁
        url = q.get()
        lock.release()  # 解锁
        try:
            ap = amazon_p()
            respnse = ap.get_response(url.strip('\n'))
            pictures = ap.check_html(respnse)
            for p in pictures:
                lock.acquire()  # 加锁
                ap.save_img(p)
                lock.release()  # 解锁
        except:
            print(f'此{url}提取jpg失败')


if __name__ == '__main__':
    with open('imgs/asins', 'r') as f:
        asins = f.readlines()
    for asin in set(asins):
        url = f'https://www.amazon.co.jp/dp/{asin}'
        q.put(url)
    p_lst = []
    # 开始多线程抓取
    for i in range(10):
        p = Thread(target=main, args=(q,))
        p.start()
        p_lst.append(p)
    for p in p_lst:
        p.join()
    print('程序运行结束')