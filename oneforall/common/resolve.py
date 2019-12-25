import asyncio
import functools

import tqdm
from dns.resolver import Resolver

import config
from config import logger


def dns_resolver():
    """
    dns解析器
    """
    resolver = Resolver()
    resolver.nameservers = config.resolver_nameservers
    resolver.timeout = config.resolver_timeout
    resolver.lifetime = config.resolver_lifetime
    return resolver


async def dns_query_a(hostname):
    """
    查询A记录

    :param str hostname: 主机名
    :return: 查询结果
    """
    resolver = dns_resolver()
    try:
        answer = resolver.query(hostname, 'A')
    except Exception as e:
        logger.log('TRACE', e.args)
        answer = e
    return answer


async def aiodns_query_a(hostname):
    """
    异步查询A记录

    :param str hostname: 主机名
    :return: 查询结果
    """
    try:
        loop = asyncio.get_event_loop()
        answer = await loop.getaddrinfo(hostname, 'http')
    except Exception as e:
        logger.log('TRACE', e.args)
        answer = e
    return answer


def resolve_callback(future, index, datas):
    """
    解析结果回调处理

    :param future: future对象
    :param index: 下标
    :param datas: 结果集
    """
    try:
        answer = future.result()
    except Exception as e:
        datas[index]['ips'] = str(e.args)
        datas[index]['valid'] = 0
    else:
        if isinstance(answer, list):
            ips = {item[4][0] for item in answer}
            datas[index]['ips'] = str(ips)[1:-1]
        else:
            datas[index]['ips'] = 'Something error'
            datas[index]['valid'] = 0


async def bulk_query_a(datas):
    """
    批量查询A记录

    :param datas: 待查的数据集
    :return: 查询过得到的结果集
    """
    logger.log('INFOR', '正在异步查询子域的A记录')
    tasks = []
    # semaphore = asyncio.Semaphore(config.limit_resolve_conn)
    for i, data in enumerate(datas):
        if not data.get('ips'):
            subdomain = data.get('subdomain')
            task = asyncio.ensure_future(aiodns_query_a(subdomain))
            task.add_done_callback(functools.partial(resolve_callback,
                                                     index=i,
                                                     datas=datas))  # 回调
            tasks.append(task)
    if tasks:  # 任务列表里有任务不空时才进行解析
        futures = asyncio.as_completed(tasks)
        for future in tqdm.tqdm(futures,
                                total=len(tasks),
                                desc='Progress',
                                smoothing=1.0,
                                ncols=True):
            await future
        # await asyncio.wait(tasks)  # 等待所有task完成
    logger.log('INFOR', '完成异步查询子域的A记录')
    return datas


def run_bulk_query(datas):
    new_datas = asyncio.run(bulk_query_a(datas))
    return new_datas
