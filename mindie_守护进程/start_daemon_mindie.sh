ulimit -n 10240
rm /dev/shm/*

nohup python mindie_listen.py >>log/nohup_mindie.log 2>&1 &