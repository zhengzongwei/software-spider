import requests
import threading
import logs
import os
from contextlib import closing
from urllib.parse import urlparse

LOG = logs.LoggerBase("software_spider")


class SoftWareSpider(object):

    def __init__(self):
        self.threads = []
        self.base_url = None
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36 Edg/108.0.1462.76"
        }
        self.params_list = []
        self.url_list = []
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        self.download_path = os.path.join(self.base_dir, 'downloads')

    def get_download_url(self):
        pass

    @staticmethod
    def parse_url(url: str):
        parse_url = urlparse(url)
        filename = parse_url.path.split("/")[-1]
        version = None
        return {
            'filename': filename,
            'version': version
        }

    def download(self, url, filepath):
        # 检查文件件是否存在
        software_info = self.parse_url(url)
        file_name = software_info.get('filename')
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

    @staticmethod
    def check_log_dir(path):
        if not os.path.exists(path):
            os.makedirs(path)

    def run(self):
        # 采用多线程 下载
        # url = self.url_list[0]
        self.check_log_dir(self.download_path)
        LOG.info(f"开始下载任务 {len(self.url_list)}")
        for url in self.url_list:
            # 检查软件是否已下载
            software_info = self.parse_url(url)
            if os.path.exists(os.path.join(self.download_path, software_info['filename'])):
                LOG.info(f"软件 {software_info['filename']}已下载！")
                continue

            LOG.info(f"开始下载软件 f{url}")
            threading.Thread(target=self.download, args=(url, self.download_path))
            self.threads.append(threading.Thread(target=self.download, args=(url, self.download_path)))

        for t in self.threads:
            t.start()
        for t in self.threads:
            t.join()
