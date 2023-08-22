import os
import re
import threading
from contextlib import closing
from urllib.parse import urlparse

import requests
import toml
from requests_html import HTMLSession

import software_spider.logs.logs as logs

LOG = logs.Logger("software_spider")


class SoftwareSpider(object):
    def __init__(self) -> None:
        self.debug = False
        self.threads = []
        self.url_info_list = []
        self.url_list = []
        self.soft_code_conf = dict()
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.download_base_path = os.path.join(os.path.dirname(self.base_dir), 'downloads')
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:108.0) Gecko/20100101 Firefox/108.0"
        }
        # TODO 需要支持 更新指定软件
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

    def get_config(self, file_path=None) -> dict:
        """
        获取配置
        """
        if file_path is None:
            file_path = os.path.join(self.base_dir, 'conf', 'software.toml')
        return toml.load(file_path)

    def get_download_url(self) -> None:
        for software_name in self.soft_code_conf:
            print(software_name)
            url_info = {
                'name': software_name,
                'urls': list()

            }
            base_url = self.soft_code_conf[software_name]['base_url']

            if 'os' in self.soft_code_conf[software_name]:
                param_dict = self.soft_code_conf[software_name]['os']
                for os_type in param_dict:
                    for param in param_dict[os_type]:
                        r = requests.get(base_url, params=param, headers=self.headers, allow_redirects=False)
                        if r.status_code == 302:
                            url_info['urls'].append(r.headers['location'])
            if 'xpath' in self.soft_code_conf[software_name]:
                r = requests.get(base_url, headers=self.headers, allow_redirects=False)
                if r.status_code == 200:
                    session = HTMLSession()
                    r = session.get(base_url)
                    for xpath in self.soft_code_conf[software_name]['xpath']:
                        url_info['urls'].append(r.html.xpath(xpath, first=True).attrs['href'])

            if 'download_url' in self.soft_code_conf[software_name]:
                for download_url in self.soft_code_conf[software_name]['download_url']:
                    download_url = f'{base_url}/{download_url}'
                    if software_name not in ['postman','docker']:
                        r = requests.get(download_url, headers=self.headers, allow_redirects=False, timeout=3)
                        if r.status_code == 302:
                            url_info['urls'].append(r.headers['location'])
                    url_info['urls'].append(download_url)
            self.url_info_list.append(url_info)

    def download(self, url, download_path) -> None:
        software_info = self.parse_url(url)
        file_name = software_info.get('file_name')
        with closing(requests.get(url, stream=True)) as response:
            chunk_size = 40960  # 单次请求最大值
            content_size = int(response.headers['content-length'])  # 内容体总大小
            data_count = 0
            with open(f"{download_path}/{file_name}", "wb") as file:
                for data in response.iter_content(chunk_size=chunk_size):
                    file.write(data)
                    data_count = data_count + len(data)
                    now_jd = (data_count / content_size) * 100

                    print("\r 文件下载进度：%d%%(%d/%d) - %s"
                          % (now_jd, data_count, content_size, f"{download_path}/{file_name}"),end=" ")
                    if now_jd == 100:
                        LOG.info("\r 文件下载完成：%d%%(%d/%d) - %s"
                                 % (now_jd, data_count, content_size, f"{download_path}/{file_name}"))

    def pre_run(self) -> None:
        # 检查 DBEUG模式是否开启
        conf_path = os.path.join(self.base_dir, 'conf', 'conf.toml')
        conf = self.get_config(conf_path).get('conf')
        self.debug = conf.get("DEBUG")

        # 检查下载文件夹是否创建
        self.check_dir(self.download_base_path)
        # 检查配置文件内容

        self.soft_code_conf = self.get_config()
        if self.soft_code_conf is None:
            LOG.info(f"配置文件内容为空，下载终止！")
            return

        # 构造下载链接
        self.get_download_url()

    def run(self) -> None:

        self.pre_run()
        LOG.info(f"开始下载任务 {len(self.url_info_list)}")
        for url_info in self.url_info_list:
            LOG.info(url_info)
            name = url_info['name']

            for url in url_info['urls']:
                software_info = self.parse_url(url)
                if not software_info['version']:
                    software_info['version'] = 'latest'

                download_path = os.path.join(self.download_base_path, name, software_info['version'])
                self.check_dir(download_path)
                if os.path.exists(
                        os.path.join(download_path, name, software_info['version'], software_info['file_name'])):
                    LOG.info(f"软件 {software_info['file_name']}已下载！")
                    continue

                LOG.info(f"开始下载软件 {name} {software_info['file_name']}")
                threading.Thread(target=self.download, args=(url, download_path))
                self.threads.append(threading.Thread(target=self.download, args=(url, download_path)))

        for t in self.threads:
            t.start()
        for t in self.threads:
            t.join()


if __name__ == '__main__':
    SoftwareSpider()
