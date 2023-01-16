import os
import re
import threading
from contextlib import closing
from urllib.parse import urlparse

import requests
import yaml
from requests_html import HTMLSession

import software_spider.logs.logs as logs

LOG = logs.Logger("software_spider")


class SoftwareSpider(object):
    def __init__(self) -> None:
        self.threads = []
        self.url_list = []
        self.soft_code_conf = dict()
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.download_path = os.path.join(os.path.dirname(self.base_dir), 'downloads')
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:108.0) Gecko/20100101 Firefox/108.0"
        }
        self.run()

    @staticmethod
    def check_dir(path) -> None:
        """
        检查文件夹是否创建
        """
        if not os.path.exists(path):
            os.makedirs(path)

    @staticmethod
    def parse_version(file_name: str = None) -> str:
        version = None
        version_reg = r'\d+\.(?:\d+\.)*\d+'
        result = re.search(file_name, version_reg)
        if result:
            version = result.group()
        return version

    def parse_url(self, url: str) -> dict:
        parse_url = urlparse(url)
        file_name = parse_url.path.split("/")[-1]

        version = self.parse_version(file_name)
        return {
            'file_name': file_name,
            'version': version
        }

    def get_config(self, file_path=None) -> None:
        """
        获取配置
        """
        if file_path is None:
            file_path = os.path.join(self.base_dir, 'conf', 'software.yaml')
        with open(file_path, 'r') as f:
            self.soft_code_conf = yaml.safe_load(f).get('software')

    def get_download_url(self) -> None:
        param_list = None
        for software_name in self.soft_code_conf:
            base_url = self.soft_code_conf[software_name]['base_url']
            if 'os' in self.soft_code_conf[software_name]:
                param_list = self.soft_code_conf[software_name]['os']

                for param in param_list:
                    r = requests.get(base_url, params=param, headers=self.headers, allow_redirects=False)
                    if r.status_code == 302:
                        self.url_list.append(r.headers['location'])
            else:
                # git download
                r = requests.get(base_url, headers=self.headers, allow_redirects=False)
                if r.status_code == 200 and software_name == 'git':
                    session = HTMLSession()
                    r = session.get(base_url)
                    for xpath in self.soft_code_conf[software_name]['xpath']:
                        self.url_list.append(r.html.xpath(xpath, first=True).attrs['href'])

    def download(self, url, filepath) -> None:
        software_info = self.parse_url(url)
        file_name = software_info.get('file_name')
        with closing(requests.get(url, stream=True)) as response:
            chunk_size = 40960  # 单次请求最大值
            content_size = int(response.headers['content-length'])  # 内容体总大小
            data_count = 0
            with open(f"{filepath}/{file_name}", "wb") as file:
                for data in response.iter_content(chunk_size=chunk_size):
                    file.write(data)
                    data_count = data_count + len(data)
                    now_jd = (data_count / content_size) * 100
                    print("\r 文件下载进度：%d%%(%d/%d) - %s"
                          % (now_jd, data_count, content_size, f"{filepath}/{file_name}"), end=" ")
                    if now_jd == 100:
                        LOG.info("\r 文件下载完成：%d%%(%d/%d) - %s"
                                 % (now_jd, data_count, content_size, f"{filepath}/{file_name}"))

    def pre_run(self) -> None:
        # 检查下载文件夹是否创建
        self.check_dir(self.download_path)
        # 检查配置文件内容

        self.get_config()
        if self.soft_code_conf is None:
            LOG.info(f"配置文件内容为空，下载终止！")
            return

        # 构造下载链接
        self.get_download_url()

    def run(self) -> None:
        self.pre_run()
        LOG.info(f"开始下载任务 {len(self.url_list)}")
        for url in self.url_list:
            # 检查软件是否已下载
            software_info = self.parse_url(url)
            if not software_info['version']:
                software_info['version'] = 'latest'

            # self.download_path = os.path.join(self.download_path,software_info['version'])
            if os.path.exists(os.path.join(self.download_path, software_info['file_name'])):
                LOG.info(f"软件 {software_info['file_name']}已下载！")
                continue

            LOG.info(f"开始下载软件 f{url}")
            threading.Thread(target=self.download, args=(url, self.download_path))
            self.threads.append(threading.Thread(target=self.download, args=(url, self.download_path)))

        for t in self.threads:
            t.start()
        for t in self.threads:
            t.join()


if __name__ == '__main__':
    SoftwareSpider()
