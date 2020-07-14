# coding:utf-8
from fund_sharpe_ratio import *
from fund_return_rate import *
from config import *


if __name__ == '__main__':
    """
    chose_type:    'gp': '股票型', 'hh': '混合型', 'zq': '债券型', 'zs': '指数型'
    rr_time_list:  ['z', '1y', '3y', '6y', '1n', '2n', '3n']  # 含义: 最近1周, 1月, 3月, 6月, 1年, 2年, 3年
    sr_top_rate:   取值为0到1的float, 选择收益率排名的Top %(sr_top_rate * 100)基金去计算夏普率, 再进行排序
    sr_begin_date: 计算夏普率的开始日期, 要保证大于等于 SHARPE_RATIO_BEGIN_DATE
    """

    # 收益率排名
    for chose_type, chose_name in FUND_TYPE.items():
        print("正在获取 {} 基金的历史收益率排名...".format(chose_name))
        rr_rank_master(chose_type=chose_type, time_list=['1y', '3y', '6y', '1n', '2n'])

    # # 夏普率排名
    # chose_type = 'gp'
    # sr_top_rate = 0.1
    # sr_begin_date = '2019-01-01'
    # sr_rank_master(chose_type=chose_type, top_rate=sr_top_rate, begin_date=sr_begin_date)
