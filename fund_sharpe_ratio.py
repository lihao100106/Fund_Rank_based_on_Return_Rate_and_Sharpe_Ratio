# coding:utf-8
from retry import retry
import gevent
from gevent import pool, monkey
monkey.patch_all()
from bs4 import BeautifulSoup
import requests
import re
import pandas as pd
import numpy as np
from config import *

requests.adapters.DEFAULT_RETRIES = 2
session = requests.Session()
session.options('https://fund.eastmoney.com/')

concurrency_pool = pool.Pool(16)

# 20190307 --- 之前爬取历史净值的url失效, 新增爬取逻辑
def get_history_value(code, begin, fund_type):
    file_name = f"{fund_type}_fund_value_{code}_{DATE_NOW}.csv"
    if file_name in os.listdir(VALUE_DIR):
        return

    print(f'Start getting history value of [{fund_type}]{code}')

    df_list = []
    for page_num in range(1, 10000):
        fund_url = f'https://fund.eastmoney.com/f10/F10DataApi.aspx?type=lsjz&code={code}&page={page_num}&per=1000'
        td_th = re.compile('t[dh]')
        ret_list = []
        table = None
        while table is None:
            response = session.get(fund_url)
            soup = BeautifulSoup(response.text, "lxml")
            table = soup.find("table", {"class": "w782 comm lsjz"})
        for row in table.findAll("tr"):
            cells = row.findAll(td_th)
            row_data = dict()
            if len(cells) == 7:
                row_data['净值日期'] = cells[0].find(text=True)
                row_data['单位净值'] = cells[1].find(text=True)
                row_data['累计净值'] = cells[2].find(text=True)
                row_data['日增长率'] = cells[3].find(text=True)
            ret_list.append(row_data)

        ret = pd.DataFrame(ret_list)
        ret.drop(0, inplace=True)
        ret = ret[ret['净值日期'].apply(lambda x: 1 if len(str(x).split("-")) == 3 else 0) > 0]
        if ret.shape[0] <= 0:
            break

        if ret['净值日期'].min() <= begin:
            df_list.append(ret[ret['净值日期'] >= begin])
            break
        else:
            df_list.append(ret)
    df_ret = pd.concat(df_list, axis=0)
    print(f"Got history value of fund [{fund_type}]{code}: {df_ret.shape}")
    df_ret.to_csv(VALUE_DIR + file_name, index=False, encoding='utf-8')
    return


def str_to_float(x):
    """
    :param x: '-1.55%'
    :return: Decimal(-0.0155)
    """
    if x.endswith('%'):
        return float(x[:-1]) / 100
    print('ERROR')
    print(x)
    return 'ERROR'


def cal_sharpe_ratio(fund_type, code, begin):
    df = pd.read_table(VALUE_DIR + f"{fund_type}_fund_value_{code}_{DATE_NOW}.csv", sep=',', encoding='utf-8')
    df['净值日期'] = pd.to_datetime(df['净值日期'])
    df = df[df['净值日期'] >= pd.to_datetime(begin)]
    df['日增长率'].fillna('0.00%', inplace=True)

    # Calculate Sharpe Ratio based on daily earnings
    df['rate_by_day'] = df['日增长率'].apply(str_to_float)
    annual_revenue = 365 * np.log(1 + df['rate_by_day'])
    sr_day = (annual_revenue.mean() - np.log(RISK_FREE_GAIN)) / annual_revenue.std()
    # print("Sharpe Ratio by day: \t{:.4f}".format(sr_day))

    # Calculate Sharpe Ratio based on weekly earnings
    df['week_cnt'] = df['净值日期'].apply(lambda x: str(x.isocalendar()[0]) + '_' + str(x.isocalendar()[1]))
    rate_by_week = []
    for week, df_w in df.groupby('week_cnt'):
        df_s = df_w.sort_values(by='净值日期', ascending=True)
        df_s = df_s.reset_index(drop=True)
        if df_s.shape[0] >= 3:  # 小于3天的星期不参与计算
            start = df_s['单位净值'][0]
            end = df_s['单位净值'][df_s.shape[0] - 1]
            rate = np.log(end / start)
            rate_by_week.append(rate)
    annual_revenue_by_w = 52 * np.array(rate_by_week)
    sr_week = (annual_revenue_by_w.mean() - np.log(RISK_FREE_GAIN)) / annual_revenue_by_w.std()
    # print("Sharpe Ratio by week: \t{:.4f}".format(sr_week))

    # Calculate Sharpe Ratio based on monthly earnings
    df['month'] = df['净值日期'].apply(lambda x: str(x)[:7])
    rate_by_month = []
    for month, df_m in df.groupby('month'):
        df_s = df_m.sort_values(by='净值日期', ascending=True)
        df_s = df_s.reset_index(drop=True)
        if df_s.shape[0] >= 10:  # 小于10天的月份不参与计算
            start = df_s['单位净值'][0]
            end = df_s['单位净值'][df_s.shape[0] - 1]
            rate = np.log(end / start)
            rate_by_month.append(rate)
    annual_revenue_by_m = 12 * np.array(rate_by_month)
    sr_month = (annual_revenue_by_m.mean() - np.log(RISK_FREE_GAIN)) / annual_revenue_by_m.std()
    # print("Sharpe Ratio by month: \t{:.4f}".format(sr_month))
    return sr_day, sr_week, sr_month


def sr_rank_master(chose_type, top_rate, begin_date):
    rr_rank_df = pd.read_csv(f'data/{FUND_TYPE.get(chose_type)}基金_收益率排名_{DATE_NOW}.csv',
                             dtype={'code': str})
    top_rr_df = rr_rank_df.head(int(rr_rank_df.shape[0] * top_rate))
    chose_code_list = top_rr_df['code'].to_list()
    chose_name_list = top_rr_df['name'].to_list()
    sharpe_r_list = []
    
    @retry(Exception, logger=None)
    def get_history_value_concurrency_wrapper(fund_code, fund_name):
        get_history_value(fund_code, begin_date, chose_type)
        sr_day, sr_week, sr_month = cal_sharpe_ratio(chose_type, fund_code, begin_date)
        sharpe_r_dict = dict()
        sharpe_r_dict['code'] = fund_code
        sharpe_r_dict['name'] = fund_name
        sharpe_r_dict['sr_daily'] = round(sr_day, 4)
        sharpe_r_dict['sr_weekly'] = round(sr_week, 4)
        sharpe_r_dict['sr_monthly'] = round(sr_month, 4)
        sharpe_r_list.append(sharpe_r_dict)

    tasks = [concurrency_pool.spawn(get_history_value_concurrency_wrapper, fund_code, fund_name)
             for fund_code, fund_name in zip(chose_code_list, chose_name_list)]
    gevent.joinall(tasks)
    
    sharpe_r_df = pd.DataFrame(sharpe_r_list)
    sort_df_list = []
    for sort_type in ['sr_daily', 'sr_weekly', 'sr_monthly']:
        sort_df = sharpe_r_df[['code', 'name', sort_type]]
        sort_df = sort_df.sort_values(by=sort_type, ascending=False)
        sort_df = sort_df.rename(columns={'code': f'fund_rank_by_{sort_type}'})
        sort_df = sort_df.reset_index(drop=True)
        sort_df_list.append(sort_df)
    ret = pd.concat(sort_df_list, axis=1)
    ret.to_csv(f'data/{FUND_TYPE.get(chose_type)}基金_夏普率排名_{begin_date}_{DATE_NOW}.csv', encoding='utf-8-sig', index=False)
    return


if __name__ == '__main__':
    # sr_rank_master('zs', 0.2, '2016-04-01')
    get_history_value('000248', '2018-01-01', 'zs')
