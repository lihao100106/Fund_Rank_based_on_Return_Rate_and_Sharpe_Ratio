# coding:utf-8
from fund_sharpe_ratio import *
from fund_return_rate import *


if __name__ == '__main__':
    # chose_type:    'gp': '股票型', 'hh': '混合型', 'zq': '债券型', 'zs': '指数型'
    # rr_time_list:  ['z', '1y', '3y', '6y', '1n', '2n', '3n']
    # sr_top_rate:   取值为0到1的float, 选择收益率排名的Top %(sr_top_rate * 100)基金去计算夏普率, 再进行排序
    # sr_begin_date: 计算夏普率的开始日期, 要保证大于等于 SHARPE_RATIO_BEGIN_DATE
    chose_type = 'gp'
    rr_time_list = ['1y', '3y', '6y', '1n', '2n']
    sr_top_rate = 0.1
    sr_begin_date = '2019-01-01'
    rr_rank_master(chose_type, rr_time_list)
    sr_rank_master(chose_type, sr_top_rate, sr_begin_date)
