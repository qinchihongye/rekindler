## 一、参数解释

* 所有参数

  | 参数                | 类型            | 描述                                        |
  | ------------------- | --------------- | ------------------------------------------- |
  | `service_name`      | `str`           | 服务名称                                    |
  | `port`              | `int`           | 守护进程服务端口                            |
  | `listen_port`       | `int`           | mindie监听端口                              |
  | `work_dir`          | `str`           | 工作目录 (默认为当前文件夹)                 |
  | `sh_file`           | `str`           | mindie 启动脚本                             |
  | `log_dir`           | `Optional[str]` | 日志目录<br />（默认在工作目录下log文件夹） |
  | `check_interval`    | `float`         | 检查间隔（秒）                              |
  | `memory_threshold`  | `int`           | 内存阈值（NPU好像有默认3376的占用）         |
  | `num_threshold`     | `float`         | GPU占用数阈值                               |
  | `startup_wait_time` | `float`         | mindie启动等待时间                          |

## 二、启动代码

* 启动守护进程

  > bash start_daemon_mindie.sh

  健康检测：

  ```curl
  curl http://127.0.0.1:8083/health
  ```

  成功启动则返回

  ```json
  {
      "code": 200,
      "data": {
          "mindie_health": true,
          "gpu_occupied": true
      }
  }
  ```

  如果

  1. mindie_health 为 true, gpu_occupied 为true, 说明mindie启动成功
  2. mindie_health 为 false, gpu_occupied 为true, 说明mindie正在启动中
  3. mindie_health 为 false, gpu_occupied 为false, 说明mindie启动失败
  
* kill mindie

  > bash clean_mindie_server.sh

* kill 守护进程

  > bash clean_daemon_mindie.sh

* 如果只kill mindie服务，不kill守护进程，则会重启mindie服务

  ---

## 三、日志

* 查看守护进程日志

  ```shell
  tail -f log/nohup_mindie.log
  ```

  ![image-20251104142704818](https://qinchihongye-1313059842.cos.ap-guangzhou.myqcloud.com/20251104142706536.png)

* 查看mindie启动日志

  ```shell
  tail -f log/mindie_service_2025_1104_1642.log
  ```

  ![image-20251104142357028](https://qinchihongye-1313059842.cos.ap-guangzhou.myqcloud.com/20251104142415158.png)