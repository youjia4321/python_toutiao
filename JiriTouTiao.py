# -*- coding:utf-8 -*-
__author__ = 'youjia'
__date__ = '2018/6/5 10:01'
import requests
import urllib.request
from urllib.parse import urlencode
from requests.exceptions import RequestException
import json
import re
from multiprocessing import Pool
from bs4 import BeautifulSoup
import pymongo
MONGO_URL = 'localhost'
MONGO_DB = 'toutiao'
MONGO_TABLE = 'toutiao'
client = pymongo.MongoClient(MONGO_URL, connect=False)
db = client[MONGO_DB]

headers = {
    "Accept": "text/plain, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) " \
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.27" \
                  "85.104 Safari/537.36",
    "Content-Type": "text/html;charset=utf-8"
}
count = 0


def get_page_html(offset, keyword):
    data = {
        'offset': offset,
        'format': 'json',
        'keyword': keyword,
        'autoload': 'true',
        'count': '20',
        'cur_tab': '3',
        'from': 'search_tab'
    }
    url = 'https://www.toutiao.com/search_content/?' + urlencode(data)
    try:
        res = requests.get(url)
        if res.status_code == 200:
            return res.text
        return None
    except RequestException:
        print('请求出错')
        return None


def get_page_deal(html):
    data = json.loads(html)
    if data and 'data' in data.keys():
        for item in data.get('data'):
            yield item.get('article_url')


def get_detail(url):
    global headers
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            return res.text
        return None
    except RequestException:
        print('请求页面出错', url)
        return None


def get_detail_deal(html, url):
    soup = BeautifulSoup(html, 'lxml')
    # title = soup.select('title')
    #     # print(title)
    title = soup.select('title')[0].get_text()
    # print(title)
    reg = 'gallery: JSON.parse.*?"(.*?})".*?siblingList'
    res = re.compile(reg, re.S)
    result = re.search(res, html)
    if result:
        data1 = result.group(1)
        data2 = data1.replace(r'\"', r'"')
        # print(type(data))
        # print(Data)
        data = json.loads(data2)
        # print(data)
        if data and 'sub_images' in data.keys():
            sub_images = data.get('sub_images')
            images = [item.get('url') for item in sub_images]
            # for image in images: download_image(image)
            save_image(images)
            return {
                'title': title,
                'url': url,
                'images': images
            }


def save_to_mongo(result):
    if db[MONGO_TABLE].insert(result):
        print('存储到MongoDB成功', result)
        print('\n\n')
        return True


def save_image(images):
    global count
    for img in images:
        image = img.replace('\\', '')
        print('正在下载图片', image + '.jpg')
        urllib.request.urlretrieve(image + '.jpg',
                                   'E:\\PyCharmp\\PycharmProjects\\爬虫\\爬虫及算法\\image\\图片\%s.jpg' % count)
        count += 1
    print('全部图片下载完成')


def main(offset):
    html = get_page_html(offset, '街拍')
    # print(get_page_deal(html))
    for url in get_page_deal(html):
        html = get_detail(url)
        if html:
            results = get_detail_deal(html, url)
            if results:
                save_to_mongo(results)


if __name__ == "__main__":
    # main()
    # 进程池，开启多进程
    groups = [i*20 for i in range(0, 10)]  # 抓取1~10组
    pool = Pool()
    pool.map(main, groups)

'''
图片存到本地的另一种方法
from hashlib import md5 导入md5
def download_image(url):
    print('正在下载', url)
    try:
        res = requests.get(url)
        if res.status_code == 200:
            save_image(res.content)  一般请求html页面用text 图片就用content 返回二进制
        return None
    except RequestException:
        print('请求图片出错')
        return None

def save_image(content):
    file_path = '{0}/{1}.{2}'.format(os.getcwd(), md5(content).hexdigest(), 'jpg')
                                    当前路径       去掉重复图片
    if not os.path.exists(file_path):
        with open(file_path, 'wb') as f:
            f.write(content)
            f.close()
'''






