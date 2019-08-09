"""
检查内容安全策略收集子域名收集子域名
"""
import requests

from common.module import Module
from common import utils
from config import logger


class CheckRobots(Module):
    """
    检查robots.txt收集子域名
    """

    def __init__(self, domain):
        Module.__init__(self)
        self.domain = self.register(domain)
        self.module = 'Check'
        self.source = 'Robots.txt'

    def check(self):
        """
        正则匹配域名的robots.txt文件中的子域
        """
        urls = [f'http://{self.domain}/robots.txt',
                f'https://{self.domain}/robots.txt',
                f'http://www.{self.domain}/robots.txt',
                f'https://www.{self.domain}/robots.txt']
        response = None
        for url in urls:
            self.header = self.get_header()
            self.proxy = self.get_proxy(self.source)
            response = self.get(url, allow_redirects=False)
            if response:
                break
        if not response:
            return
        self.subdomains = utils.match_subdomain(self.domain, response.text)

    def run(self):
        """
        类执行入口
        """
        logger.log('DEBUG', f'开始执行{self.source}检查{self.domain}'
                   f'域响应头中的内容安全策略字段')
        self.check()
        self.save_json()
        self.gen_result()
        self.save_db()
        logger.log('DEBUG', f'结束执行{self.source}检查{self.domain}'
                   f'域响应头中的内容安全策略字段')
        self.finish()


def do(domain):  # 统一入口名字 方便多线程调用
    """
    类统一调用入口

    :param str domain: 域名
    """
    check = CheckRobots(domain)
    check.run()


if __name__ == '__main__':
    do('qq.com')