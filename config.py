# coding:utf-8
import datetime


FUND_TYPE = {'gp': u'股票型',
             'hh': u'混合型',
             'zq': u'债券型',
             'zs': u'指数型',
             }

VALUE_DIR = 'data/history_Net_Asset_Value/'
DATE_NOW = str(datetime.datetime.now())[:10]
SHARPE_RATIO_BEGIN_DATE = '2014-01-01'
RISK_FREE_GAIN = 1.03
