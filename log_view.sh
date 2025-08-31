#!/bin/bash

cd /root/Code/iot_server

journalctl -u iot_data_server.service -f 
