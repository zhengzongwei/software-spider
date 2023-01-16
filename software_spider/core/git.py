from software_spider.core import software_spider as software_spider
from requests_html import HTMLSession

import software_spider.logs.logs as logs

LOG = logs.LoggerBase("git")


class Git(software_spider.SoftWareSpider):

    def __init__(self) -> None:
        super().__init__()
        self.base_url = "https://git-scm.com/download/win"
        self.get_download_url()
        self.run()

    def get_download_url(self) -> None:
        session = HTMLSession()
        r = session.get(self.base_url)
        win_git_x86 = r.html.xpath('//*[@id="main"]/p[2]/strong/a', first=True)

        win_git_x64 = r.html.xpath('//*[@id="main"]/p[3]/strong/a', first=True)

        self.url_list.extend([win_git_x64.attrs['href'], win_git_x86.attrs['href']])


if __name__ == '__main__':
    Git()
