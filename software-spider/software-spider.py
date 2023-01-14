import requests
import threading
import logs
from contextlib import closing
from urllib.parse import urlparse
from requests_html import HTMLSession

LOG = logs.LoggerBase("software-spider")


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
        code_info = self.parse_url(url)
        file_name = code_info.get('filename')
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
                             % (now_jd, data_count, content_size, f"{filepath}/{file_name}"))
                    if now_jd == 100:
                        LOG.info("\r 文件下载完成：%d%%(%d/%d) - %s"
                                 % (now_jd, data_count, content_size, f"{filepath}/{file_name}"))

    def run(self):
        # 采用多线程 下载
        # url = self.url_list[0]
        for url in self.url_list:
            threading.Thread(target=self.download, args=(url, '.'))
            self.threads.append(threading.Thread(target=self.download, args=(url, '.')))

        for t in self.threads:
            t.start()
        for t in self.threads:
            t.join()


class Code(SoftWareSpider):

    def __init__(self):
        super().__init__()

        self.threads = []
        self.data = {
            "build": "stable",
            "os": [
                "win32-x64-user",
                "win32-arm64-user",
                "darwin-arm64",
                "darwin-universal",
                "linux-deb-x64",
                "linux-deb-arm64",
                # "linux-rpm-x64",
                # "linux-rpm-arm64",
                # "linux-rpm-armhf"
            ]
        }
        self.base_url = "https://code.visualstudio.com/sha/download"

        self.gen_params()
        self.get_download_url()
        self.run()

    def gen_params(self):
        for os in self.data['os']:
            params = {
                "os": os,
                "build": self.data['build']
            }
            self.params_list.append(params)

    def get_download_url(self):
        for param in self.params_list:
            r = requests.get(self.base_url, params=param, headers=self.headers, allow_redirects=False)

            if r.status_code == 302:
                self.url_list.append(r.headers['location'])

    # def download(self, url, filepath):
    #     # 检查文件件是否存在
    #     code_info = self.parse_url(url)
    #     file_name = code_info.get('filename')
    #     with closing(requests.get(url, stream=True)) as response:
    #         chunk_size = 40960  # 单次请求最大值
    #         content_size = int(response.headers['content-length'])  # 内容体总大小
    #         data_count = 0
    #         with open(f"{filepath}/{file_name}", "wb") as file:
    #             for data in response.iter_content(chunk_size=chunk_size):
    #                 file.write(data)
    #                 data_count = data_count + len(data)
    #                 now_jd = (data_count / content_size) * 100
    #                 LOG.info("\r 文件下载进度：%d%%(%d/%d) - %s"
    #                          % (now_jd, data_count, content_size, f"{filepath}/{file_name}"), end=" ")

    # def run(self):
    #     # 采用多线程 下载
    #     # url = self.url_list[0]
    #     for url in self.url_list:
    #         threading.Thread(target=self.download, args=(url, '.'))
    #         self.threads.append(threading.Thread(target=self.download, args=(url, '.')))
    #
    #     for t in self.threads:
    #         t.start()
    #     for t in self.threads:
    #         t.join()

    # def parse_version(self, filename: str):
    #     if filename.endswith('deb'):
    #         pass
    #     elif filename.endswith('rpm'):
    #         pass
    #     elif filename.endswith('exe'):
    #         pass
    #     elif filename.endswith("zip"):
    #         pass
    #     else:
    #         print(f"the filename {filename} is not in ['deb', 'rpm', 'exe']")
    #     pass

    # @staticmethod
    # def parse_url(url: str):
    #     parse_url = urlparse(url)
    #     filename = parse_url.path.split("/")[-1]
    #     version = None
    #     return {
    #         'filename': filename,
    #         'version': version
    #     }
    #


class Git(SoftWareSpider):

    def __init__(self):
        super().__init__()
        self.base_url = "https://git-scm.com/download/win"
        self.get_download_url()
        self.run()

    def get_download_url(self):
        session = HTMLSession()
        r = session.get(self.base_url)
        win_git_x86 = r.html.xpath('//*[@id="main"]/p[2]/strong/a', first=True)

        win_git_x64 = r.html.xpath('//*[@id="main"]/p[3]/strong/a', first=True)

        self.url_list.extend([win_git_x64.attrs['href'], win_git_x86.attrs['href']])


if __name__ == '__main__':
    # Code()
    Git()
