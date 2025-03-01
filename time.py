import datetime
import time

# 获取当前时间
now = datetime.datetime.now()

# 格式化时间为年月日时分秒
current_high_precision = time.perf_counter()
formatted_time = now.strftime('%Y%m%d_%H%M%S')
import pdb; pdb.set_trace()
# 拼接文件名
csv_filename = f'exported_data_{formatted_time}.csv'

print(csv_filename)