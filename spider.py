import os
import re
import json
import base64

import requests
from lxml import etree
from fontTools.ttLib import TTFont


class TongChengSpider(object):

    """
    58同城 | 北京市朝阳区租房信息爬虫

    ~~~~~~

    - 网址：https://bj.58.com/chaoyang/chuzu/

    - 网站反爬较严重，不仅有字体反爬，对 IP 限制也较严格，所以把网页源码保存到了本地，
      在无代理的情况使用本地文件，有代理的情况实时抓取。
    """

    def __init__(self):
        self.url = "https://bj.58.com/chaoyang/chuzu/"
        self.headers = {
            "referer": "https://bj.58.com/",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36"
        }
        # 存放解密后的字符串与数字对应关系
        self.keys = dict()
        self.proxies = dict()

    def crawler(self):
        """获取网页内容"""

        if self.proxies:
            # 有代理就请求网页
            _response = requests.get(self.url, headers=self.headers).text
        else:
            # 无代理使用本地文件
            with open("./_58.html", "r") as f:
                _response = f.read()
        return _response

    def _init_data(self):
        """处理网页加密字符串，将 tff 格式转化为 xml 格式，并找出对应关系"""

        self.get_font_data()
        self.parse_font_data()

    def get_font_data(self):
        """获取网站加密字体数据"""

        response = self.crawler()
        _base64_code = re.findall(
            "data:application/font-ttf;charset=utf-8;base64,(.*?)'\) format",
            response)[0]
        _data = base64.decodebytes(_base64_code.encode())
        with open('font_data.ttf', 'wb') as f:
            f.write(_data)
        font = TTFont('font_data.ttf')
        font.saveXML('font_data.xml')

    def parse_font_data(self):
        """解析 XML 格式的字体文件
           找出 unicode 和加密字符的对应关系"""

        unicode_list = ['0x9476', '0x958f', '0x993c', '0x9a4b', '0x9e3a',
                        '0x9ea3', '0x9f64', '0x9f92', '0x9fa4', '0x9fa5']
        glyph_list = {'glyph00001': '0', 'glyph00002': '1', 'glyph00003': '2',
                      'glyph00004': '3', 'glyph00005': '4', 'glyph00006': '5',
                      'glyph00007': '6', 'glyph00008': '7', 'glyph00009': '8',
                      'glyph00010': '9'}

        data = etree.parse("./font_data.xml")
        self.keys = {item: glyph_list[data.xpath("//cmap//map[@code='{}']/@name".format(item))[0]]
                     for item in unicode_list}

    def replace_secret_code(self, raw_string, rep_string, rep_dict):
        """替换加密字体"""

        return raw_string.replace(rep_string, rep_dict[rep_string])

    def get_real_resp(self):
        """替换掉原始网页中的加密字体"""

        _response = self.crawler()

        # 将获取到的字符串替换为网页中的字符串样式
        _keys = json.loads(json.dumps(self.keys).replace("0x", "&#x").replace('":', ';":'))

        response = None
        for item in _keys.keys():
            if not response:
                response = self.replace_secret_code(_response, item, _keys)
            else:
                response = self.replace_secret_code(response, item, _keys)

        with open("demo.html", "w") as f:
            f.write(response)

    def del_(self):
        """删除无用文件"""

        os.remove("font_data.xml")
        os.remove("font_data.ttf")

    def run(self):
        self._init_data()
        self.get_real_resp()
        # self.del_()


if __name__ == '__main__':
    tc = TongChengSpider()
    tc.run()
