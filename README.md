# Rekindler

A lightweight daemon that monitors and auto-restarts model inference services (vLLM, SGLang, MindIE) on both NVIDIA GPU and Huawei Ascend NPU.

## 项目结构

```
rekindler/
├── backend/
│   ├── listener.py              # 统一守护进程入口
│   ├── core/                    # 核心模块
│   │   ├── config.py            #   配置模型
│   │   ├── health_checker.py    #   健康检查
│   │   └── hardware/            #   硬件检测
│   │       ├── gpu_checker.py   #     NVIDIA GPU
│   │       └── npu_checker.py   #     Ascend NPU
│   ├── configs/                 # 配置文件
│   │   ├── vllm_gpu.json
│   │   ├── vllm_npu.json
│   │   ├── sglang_gpu.json
│   │   └── mindie_npu.json
│   ├── scripts/                 # 启动/停止脚本
│   │   ├── vllm_gpu/
│   │   ├── vllm_npu/
│   │   ├── sglang_gpu/
│   │   └── mindie_npu/
│   └── requirements.txt
├── frontend/                    # 前端（预留）
└── README.md
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r backend/requirements.txt
```

### 2. 修改配置

编辑 `backend/configs/` 下的配置文件，根据实际环境修改模型路径、端口等参数。

配置文件参数说明：

| 参数                | 类型    | 说明                          |
| ------------------- | ------- | ----------------------------- |
| `service_name`      | str     | 服务名称                      |
| `hardware_type`     | str     | 硬件类型：`gpu` 或 `npu`      |
| `port`              | int     | 守护进程服务端口              |
| `listen_port`       | int     | 推理服务监听端口              |
| `sh_file`           | str     | 推理服务启动脚本路径          |
| `check_interval`    | float   | 健康检查间隔（秒）            |
| `memory_threshold`  | int     | 显存/内存阈值（MiB）          |
| `num_threshold`     | float   | GPU/NPU 占用比例阈值          |
| `startup_wait_time` | float   | 服务启动等待时间（秒）        |

### 3. 启动守护进程

从项目根目录运行对应的启动脚本：

```bash
# vLLM on GPU
bash backend/scripts/vllm_gpu/start_daemon.sh

# vLLM on Ascend NPU
bash backend/scripts/vllm_npu/start_daemon.sh

# SGLang on GPU
bash backend/scripts/sglang_gpu/start_daemon.sh

# MindIE on Ascend NPU
bash backend/scripts/mindie_npu/start_daemon.sh
```

或直接运行：

```bash
python backend/listener.py --config backend/configs/vllm_gpu.json
```

### 4. 健康检查

```bash
curl http://127.0.0.1:8083/health
```

返回示例：

```json
{
    "code": 200,
    "data": {
        "vllm_health": true,
        "gpu_occupied": true
    }
}
```

状态说明：
- `*_health: true, gpu_occupied: true` → 服务运行正常
- `*_health: false, gpu_occupied: true` → 服务启动中
- `*_health: false, gpu_occupied: false` → 服务异常，守护进程将自动重启

### 5. 停止服务

```bash
# 停止推理服务（守护进程会自动重启）
bash backend/scripts/vllm_gpu/clean_service.sh

# 停止守护进程
bash backend/scripts/vllm_gpu/clean_daemon.sh
```

### 6. 查看日志

```bash
# 守护进程日志
tail -f log/nohup_vllm_gpu.log

# 推理服务日志
tail -f log/vllm_service_*.log
```

## 支持的服务

| 服务 | 硬件 | 配置文件 |
| --- | --- | --- |
| vLLM | NVIDIA GPU | `vllm_gpu.json` |
| vLLM | Ascend NPU | `vllm_npu.json` |
| SGLang | NVIDIA GPU | `sglang_gpu.json` |
| MindIE | Ascend NPU | `mindie_npu.json` |

## License

Apache-2.0
