# coding:utf-8
from bs4 import BeautifulSoup
import urllib
import re
import pandas as pd
import numpy as np
from config import *


# 20190307 --- 之前爬取历史净值的url失效, 新增爬取逻辑
def get_history_value(code, begin, fund_type):
    file_name = "{}_fund_value_{}_{}.csv".format(fund_type, code, DATE_NOW)
    if file_name in os.listdir(VALUE_DIR):
        return

    df_list = []
    for page_num in range(1, 10000):
        fund_url = 'http://fund.eastmoney.com/f10/F10DataApi.aspx?type=lsjz&code={}&page={}&per=1000'.format(code, page_num)
        soup = BeautifulSoup(urllib.request.urlopen(url=fund_url), "lxml")
        table = soup.find("table", {"class": "w782 comm lsjz"})
        td_th = re.compile('t[dh]')
        ret_list = []
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
    print(df_ret.shape)
    df_ret.to_csv(VALUE_DIR + file_name, index=False, encoding='utf-8')
    return


def str_to_float(x):
    if x.endswith('%'):
        tmp = x.strip('%')
        if tmp[0] in ['-']:
            return float(tmp[1:]) / 100.0 * (-1)
        if tmp[0] in ['+']:
            return float(tmp[1:]) / 100.0
        return float(tmp[1:]) / 100.0
    print('ERROR')
    print(x)
    return 'ERROR'


def cal_sharpe_ratio(fund_type, code, begin):
    df = pd.read_table(VALUE_DIR + "{}_fund_value_{}_{}.csv".format(fund_type, code, DATE_NOW), sep=',', encoding='utf-8')
    df['净值日期'] = pd.to_datetime(df['净值日期'])
    df = df[df['净值日期'] >= pd.to_datetime(begin)]
    df['日增长率'].fillna('0.00%', inplace=True)

    # Calculate Sharpe Ratio based on daily earnings
    df['rate_by_day'] = df['日增长率'].apply(str_to_float)
    annual_revenue = 365 * np.log(1 + df['rate_by_day'])
    sr_day = (annual_revenue.mean() - np.log(RISK_FREE_GAIN)) / annual_revenue.std()
    # print "Sharpe Ratio by day: \t{:.4f}".format(sr_day)

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
    # print "Sharpe Ratio by week: \t{:.4f}".format(sr_week)

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
    # print "Sharpe Ratio by month: \t{:.4f}".format(sr_month)
    return sr_day, sr_week, sr_month


def sr_rank_master(chose_type, top_rate, begin_date):
    rr_rank_df = pd.read_csv('data/{}基金_收益率排名_{}.csv'.format(FUND_TYPE.get(chose_type), DATE_NOW),
                             dtype={'code': str})
    chose_code_list = rr_rank_df.head(int(rr_rank_df.shape[0] * top_rate))['code'].tolist()
    sharpe_r_list = []
    for fund_code in chose_code_list:
        get_history_value(fund_code, begin_date, chose_type)
        sr_day, sr_week, sr_month = cal_sharpe_ratio(chose_type, fund_code, begin_date)
        sharpe_r_dict = dict()
        sharpe_r_dict['code'] = fund_code
        sharpe_r_dict['sr_daily'] = round(sr_day, 4)
        sharpe_r_dict['sr_weekly'] = round(sr_week, 4)
        sharpe_r_dict['sr_monthly'] = round(sr_month, 4)
        sharpe_r_list.append(sharpe_r_dict)
    sharpe_r_df = pd.DataFrame(sharpe_r_list)
    sort_df_list = []
    for sort_type in ['sr_daily', 'sr_weekly', 'sr_monthly']:
        sort_df = sharpe_r_df[['code', sort_type]]
        sort_df = sort_df.sort_values(by=sort_type, ascending=False)
        sort_df = sort_df.rename(columns={'code': 'fund_rank_by_{}'.format(sort_type)})
        sort_df = sort_df.reset_index(drop=True)
        sort_df_list.append(sort_df)
    ret = pd.concat(sort_df_list, axis=1)
    ret.to_csv('data/{}基金_夏普率排名_{}_{}.csv'.format(FUND_TYPE.get(chose_type), begin_date, DATE_NOW), index=False)
    return


if __name__ == '__main__':
    # sr_rank_master('zs', 0.2, '2016-04-01')
    get_history_value('000248', '2018-01-01', 'zs')
