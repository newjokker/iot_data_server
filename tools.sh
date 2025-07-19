#!/bin/bash


# 打印文件夹的最新的几个数据
ls -lt /mnt/ssd/run | tail -n +2 | head -n 100 | awk '{print $NF}'

# 拷贝日志到本地
scp -P 54548   txkj@119.45.103.177:/home/txkj/Code/dcu_escalator/logs/trend_copy3.db /home/txkj/Code/dcu_escalator/logs    
scp -P 54548   txkj@119.45.103.177:/home/txkj/Code/dcu_escalator/logs/baseline.db /home/txkj/Code/dcu_escalator/logs    
scp -P 54548   txkj@119.45.103.177:/home/txkj/Code/dcu_escalator/speed_test /home/txkj/Code/dcu_escalator/logs    

# 复制本地代码到远程
scp -r -P 54548 /home/txkj/Code/dcu_escalator/scripts/  /home/txkj/Code/dcu_escalator/dao/  /home/txkj/Code/dcu_escalator/templates/  /home/txkj/Code/dcu_escalator/auto_amount/  txkj@119.45.103.177:/home/txkj/Code/dcu_escalator/;
scp  -P 54548 /home/txkj/Code/dcu_escalator/*  txkj@119.45.103.177:/home/txkj/Code/dcu_escalator/;

# 查看
sqlite3 ./logs/trend.db "SELECT * FROM trend_info ORDER BY id DESC LIMIT 10;"

sqlite3 ./logs/trend.db "SELECT * FROM trend_info WHERE collector = 1 AND channel IN (9, 10) AND feature = 'speed' ORDER BY id DESC LIMIT 10;"

sqlite3 ./logs/trend.db "SELECT * FROM trend_info WHERE task_name = '3e72763842b311f056f796f7a9169aae';"

sqlite3 ./logs/logs.db "SELECT * FROM log_entries ORDER BY id DESC LIMIT 10;"

sqlite3 ./logs/baseline.db "SELECT * FROM baseline_info ORDER BY id DESC LIMIT 10;"

# 查看所有的表
sqlite3 ./logs/trend.db "SELECT name FROM sqlite_master WHERE type='table';"

# 查询趋势的时间范围
sqlite3 ./logs/trend.db "SELECT date FROM trend_info where id==1   LIMIT 1;"

# 删除对应的表
sqlite3 ./logs/trend.db "DROP TABLE IF EXISTS trend_info_minute;"
sqlite3 ./logs/trend.db "DROP TABLE IF EXISTS trend_info_hour;"
sqlite3 ./logs/trend.db "DROP TABLE IF EXISTS trend_info_day;"
sqlite3 ./logs/trend.db "DROP TABLE IF EXISTS trend_info_month;"
sqlite3 ./logs/trend.db "DROP TABLE IF EXISTS alarm_info;"


# 查看指定的 task_id 对应的日志文件
curl http://127.0.0.1:52021/server/detect/log/task_id

# 查看指定的 task_id 对应的日志文件
curl http://127.0.0.1:52021/database_size_info

# 查看指定的 task_id 对应的日志文件
curl http://127.0.0.1:52021/server/detect/progress

nohup ./start_server.sh > server.log 2>&1 &


