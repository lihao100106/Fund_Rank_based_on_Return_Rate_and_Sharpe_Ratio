# coding:utf-8
import datetime
import os


FUND_TYPE = {
    'gp': u'股票型',
    'hh': u'混合型',
    'zq': u'债券型',
    'zs': u'指数型',
}

COMMON_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36",
    "cookie": "xsb_history=872701%7C%u7B2C%u4E00%u4EBA%u5C45%2C872128%7C%u7B2C%u4E00%u6587%u4F53; em_hq_fls=js; qgqp_b_id=cf6becf838e25866bf830674c19442e0; HAList=f-0-399006-%u521B%u4E1A%u677F%u6307%2Ca-sh-603290-N%u65AF%u8FBE%2Cp-sz-837498-%u7B2C%u4E00%u7269%u4E1A; ASP.NET_SessionId=abk35lzirbuovhohyfkk5r2i; st_si=31888493841701; st_asi=delete; st_pvi=86155137491474; st_sp=2019-11-07%2011%3A01%3A21; st_inirUrl=https%3A%2F%2Fwww.baidu.com%2Flink; st_sn=2; st_psi=20200714212803526-0-5371499353",
    "Host": "fund.eastmoney.com",
    "Referer": "http://fund.eastmoney.com/data/fundranking.html",
    "Accept": "*/*"
}

VALUE_DIR = 'data/history_Net_Asset_Value/'
DATE_NOW = str(datetime.datetime.now())[:10]
SHARPE_RATIO_BEGIN_DATE = '2014-01-01'
RISK_FREE_GAIN = 1.03

# 文件存储路径
if not os.path.exists('data/'):
    os.mkdir('data/')

if not os.path.exists(VALUE_DIR):
    os.mkdir(VALUE_DIR)
