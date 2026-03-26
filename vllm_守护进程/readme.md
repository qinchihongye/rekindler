## 一、参数解释

* 所有参数

  | 参数                | 类型            | 描述                                        |
  | ------------------- | --------------- | ------------------------------------------- |
  | `service_name`      | `str`           | 服务名称                                    |
  | `port`              | `int`           | 守护进程服务端口                            |
  | `listen_port`       | `int`           | vllm监听端口                                |
  | `work_dir`          | `str`           | 工作目录 (默认为当前文件夹)                 |
  | `sh_file`           | `str`           | vllm 启动脚本                               |
  | `log_dir`           | `Optional[str]` | 日志目录<br />（默认在工作目录下log文件夹） |
  | `check_interval`    | `float`         | 检查间隔（秒）                              |
  | `memory_threshold`  | `int`           | 内存阈值                                    |
  | `num_threshold`     | `float`         | GPU占用数阈值                               |
  | `startup_wait_time` | `float`         | vllm启动等待时间                            |

## 二、启动代码

* 启动守护进程

  > bash start_daemon_vllm.sh

  健康检测：

  ```curl
  curl http://127.0.0.1:8083/health
  ```

  成功启动则返回

  ```json
  {
      "code": 200,
      "data": {
          "vllm_health": true,
          "gpu_occupied": true
      }
  }
  ```

  如果

  1. vllm_health 为 true, gpu_occupied 为true, 说明vllm启动成功
  2. vllm_health 为 false, gpu_occupied 为true, 说明vllm正在启动中
  3. vllm_health 为 false, gpu_occupied 为false, 说明vllm启动失败


* kill vllm

  > bash clean_vllm_server.sh

* kill 守护进程

  > bash clean_daemon_vllm.sh

* 如果只kill vllm服务，不kill守护进程，则会重启vllm服务

  ---

## 三、日志

* 查看守护进程日志

  ```shell
  tail -f log/nohup_vllm.log
  ```

* 查看mindie启动日志

  ```shell
  tail -f log/vllm_service_2025_0626_1642.log
  ```
 