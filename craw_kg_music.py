import requests
from selenium import webdriver
from lxml import etree
from fake_useragent import UserAgent
import os
from selenium.webdriver.chrome.options import Options
import json
import re

class KuGou(object):
    def __init__(self) -> None:
        self.headers = {"User-Agent": UserAgent().random, "cookie": "kg_mid=7b878e1cbc728be6f5bb8274d5d6fd7e; kg_dfid=2C89BA1Ow9Eg184aX93NnoOC; kg_dfid_collect=d41d8cd98f00b204e9800998ecf8427e"}


    def music_parse(self, url):
        wb = webdriver.Chrome(executable_path="./chromedriver.exe",
                              options=chrome_options)
        wb.get(url=url)
        data = wb.page_source
        wb.quit()
        tree = etree.HTML(data)
        music = tree.xpath('//*[@class="music"]/@src')[0]
        musicname = "./music/" + tree.xpath(
            '//*[@class="audioName"]/@title')[0] + ".mp3"
        return music, musicname

    def music_download(self, music, musicname):
        response = requests.get(url=music, headers=self.headers).content
        with open(musicname, "wb") as fp:
            fp.write(response)

    def parse_index(self, is_index):
        pattern1 = re.compile(r'(\d+)-(\d+)')
        pattern2 = re.compile(r'(\d+)')
        matches1 = pattern1.findall(is_index)
        matches2 = pattern2.findall(is_index)
        indexs = []
        for match1 in matches1:
            start = match1[0]
            end = match1[1]
            indexs.extend(range(int(start), int(end) + 1))
        for match2 in matches2:
            start = match2[0]
            indexs.append(int(start))
        indexs = sorted(set(indexs))
        return indexs

    def download_one_batch(self, data, res, is_index):
        indexs = self.parse_index(is_index)
        # number = int(input("\n请选择歌曲序号>> "))
        fhashs = re.findall('"FileHash":"(.*?)"', res)
        album_ids = re.findall('"AlbumID":"(.*?)"', res)
        for number in indexs:
            if number <= 0:
                print("请检查输入是否符合规范\n退出酷狗下载")
                break
            try:
                name = str(data[number - 1]['FileName']).replace(
                    '<em>', '').replace('</em>', '')
                fhash = fhashs[number - 1]
                album_id = album_ids[number - 1]
                url = 'https://wwwapi.kugou.com/yy/index.php?r=play/getdata&callback=jQuery191010559973368921649_1548736071852&hash={}&album_id={}&_=1548736071853'
                hash_content = requests.get(url.format(fhash,
                                                       album_id), headers=self.headers).content
                pattern = re.compile(r'\"play_url\":\"(https:.*\.mp3)\",\"authors\"')
                real_download_url = re.search(pattern, hash_content.decode()).group(1).replace("\\/", "/")
                
            except TimeoutError:
                print("网络不佳，请重新下载")
                break
            try:
                if not os.path.exists("./music/"):
                    os.makedirs("./music/")
                save_path = "./music/" + name + ".mp3"
                true_path = os.path.abspath(save_path)
                print(name + "下载中.....")
                if os.path.exists(save_path):
                    continue
                # ct = requests.get(real_download_url).content
                # with open("./music/" + name + ".mp3", "wb") as fp:
                #     fp.write(ct)
                self.music_download(real_download_url, true_path)
                print(name + "下载完成")
            except:
                print("无法爬取内容")
        # 下载成功后退出程序
        print("下载完毕")

    def download(self):
        print("\n", "{:^30}".format("正在使用酷狗VIP下载器"))
        while True:
            song_name = input("\n请输入关键字或歌曲地址>>").strip()
            if song_name == '':
                continue
            elif "http" in song_name:
                self.music_parse(song_name)
            elif song_name == 'q':
                print("\n退出酷狗音乐下载")
                break
            print("\n正在努力寻找资源......")
            page = 1
            while True:
                url = "http://songsearch.kugou.com/song_search_v2?callback=jQuery112407470964083509348_1534929985284&keyword={}&" \
                  "page={}&pagesize=30&userid=-1&clientver=&platform=WebFilter&tag=em&filter=2&iscorrection=1&privilege_filte" \
                  "r=0&_=1534929985286".format(song_name, page)
                try:
                    res = requests.get(url).text
                    js = json.loads(res[res.index('(') + 1:-2])
                    data = js['data']['lists']  # 歌曲列表
                except TimeoutError:
                    print("\n网络不佳，请重新下载")
                    break
                except:
                    print("未找到资源QAQ")
                    break
                print("为你找到以下内容".center(30, '*'))
                print("{:6}{:30}".format("序号", "歌手  -  歌名"))
                try:
                    for i in range(10):
                        print(
                            str(i + 1) +
                            "    " + str(data[i]['FileName']).replace(
                                '<em>', '').replace('</em>', ''))
                    print("\n支持多数字输入，以及“-”表示范围，用空格隔开，输入n进入下一页")
                    while True:
                        is_index = input("\n选择下载序号>>").strip()
                        if is_index == "q":
                            print("已退出，感谢使用！")
                            return None
                        if is_index == "n":
                            page += 1
                            break
                        self.download_one_batch(data, res, is_index)
                except:
                    print("异常错误，请重新下载")


if __name__ == '__main__':
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    craw = KuGou()
    craw.download()
