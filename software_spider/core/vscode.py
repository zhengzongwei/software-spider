import software_spider.core.software_spider as software_spider
import requests

import software_spider.logs.logs as logs

LOG = logs.LoggerBase("vscode")


class Code(software_spider.SoftWareSpider):

    def __init__(self) -> None:
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

    def gen_params(self) -> None:
        for os in self.data['os']:
            params = {
                "os": os,
                "build": self.data['build']
            }
            self.params_list.append(params)

    def get_download_url(self) -> None:
        for param in self.params_list:
            r = requests.get(self.base_url, params=param, headers=self.headers, allow_redirects=False)

            if r.status_code == 302:
                self.url_list.append(r.headers['location'])


if __name__ == '__main__':
    Code()
