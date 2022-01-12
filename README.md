# Fund_Rank_based_on_Return_Rate_and_Sharpe_Ratio
基于历史收益率和夏普率(Sharpe Ratio)的基金排序

1. **使用方法**：
   - 配置好参数，运行 fund_select_main.py，便可以得到收益率和夏普率的排序文件，默认存储在data/目录下
   - 在收益率排名靠前的基金中，挑选一些夏普率比较高的基金，然后可以根据基金的其他指标再做最终选择；
   
2. **fund_return_rate.py**
   按照最近1周、1月、3月、6月、1年、2年、3年的收益率排名，从天天基金网爬取基金代码，并进行统计和排序

3. **fund_sharpe_ratio.py**
   从天天基金网爬取基金的历史每日净值数据，计算基金的夏普率并排序