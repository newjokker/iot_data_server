#!/bin/bash


sqlite3 /root/Code/iot_server/data/iot_data.db "SELECT * FROM sensor_data ORDER BY id DESC LIMIT 10;"