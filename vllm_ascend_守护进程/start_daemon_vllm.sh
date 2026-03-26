ulimit -n 10240
rm /dev/shm/*

nohup python vllm_listen.py >>log/nohup_vllm.log 2>&1 &