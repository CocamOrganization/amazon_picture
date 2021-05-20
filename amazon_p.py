import requests
from user_agents import user_agents
from lxml import etree
import random
import os
import time


class amazon_p(object):

    def check(self, reason, asin, text):
        '''将抓取失败的html文件保存到本地，分析原因'''
        path = 'D:/test/' + reason+ '/' + asin + '.html'
        with open(path, 'w', encoding='utf-8') as f:
            f.write(text)

    def get_response(self, asin, retries=0):
        '''获取html代码'''
        if retries > 10:
            print('超过最大重试次数:{url}'.format(url=url))
            return
        retries += 1
        headers = {'user-agent': random.choice(user_agents),
                    'accept-ch': 'ect, rtt, downlink',
                    'accept - ch - lifetime': '86400',
                    'cache - control': 'no - cache',
                    'content - encoding': 'gzip',
                    'content - language': 'en-US',
                    'content - type': 'text/html',
                    'referer': 'https://www.amazon.com/',
                    'charset': 'UTF-8',
                    'server': 'Server'}
        url = f'https:{asin}'
        try:
            response = requests.get(url, headers=headers, timeout=5)
            if 'Robot Check' in response.text:
                print('出现验证码,更换ip:{url}'.format(url=url))
                time.sleep(random.randint(4, 10))
                return self.get_response(url, retries)
            elif 'Enter the characters you see below' in response.text:
                print('出现验证码,更换ip:{url}'.format(url=url))
                time.sleep(random.randint(4, 10))
                return self.get_response(url, retries)
            elif response.status_code == 404:
                print('Page Not Found: {url}'.format(url=url))
            elif response.status_code == 200:
                print('成功获取页面：{url}'.format(url=url))
                return {'rp': response, 'asin': asin}
            elif response.status_code == 503:
                print('出现503错误：{url}'.format(url=url))
                # self.check('unknown', '503', text)
                time.sleep(random.randint(6, 10))
                return self.get_response(url, retries)
            else:
                print('出现未知类型的错误：{url}'.format(url=url))
                return {'rp': 'failed', 'asin': asin}
                # self.check('unknown', url, text)
        except:
            print('连接超时，准备重试')
            time.sleep(random.randint(8, 12))
            return self.get_response(url, retries)

    def check_html(self, response):
        asin = response['asin']


if __name__ == '__main__':
    pass