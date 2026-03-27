# Rekindler 🔥

[English](README.md) | [中文](README.Chinese.md)

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8%2B-brightgreen.svg)](https://python.org)
[![vLLM](https://img.shields.io/badge/vLLM-supported-orange.svg)](https://github.com/vllm-project/vllm)
[![SGLang](https://img.shields.io/badge/SGLang-supported-orange.svg)](https://github.com/sgl-project/sglang)
[![MindIE](https://img.shields.io/badge/MindIE-supported-orange.svg)](https://www.hiascend.com/)

A lightweight daemon that monitors and auto-restarts model inference services (vLLM, SGLang, MindIE) on both NVIDIA GPU and Huawei Ascend NPU.

---

## 📖 目录

- [背景](#背景)
- [功能特点](#功能特点)
- [工作原理](#工作原理)
- [项目结构](#项目结构)
- [快速开始](#快速开始)
  - [安装依赖](#1-安装依赖)
  - [修改配置](#2-修改配置)
  - [启动守护进程](#3-启动守护进程)
  - [健康检查](#4-健康检查)
  - [停止服务](#5-停止服务)
  - [查看日志](#6-查看日志)
- [支持的服务](#支持的服务)
- [扩展新服务](#扩展新服务)
- [常见问题](#常见问题)
- [更新日志](#更新日志)
- [贡献指南](#贡献指南)
- [致谢](#致谢)
- [License](#license)

## 背景

在实际的大模型部署中，我们团队通过流水线实现了一键容器化部署。但在生产环境运行过程中，推理服务（如 vLLM）可能因 OOM、CUDA 异常等原因崩溃。此时，容器编排平台只能提供**容器级别**的重启——这意味着整个容器会被重建，不仅恢复时间长，还可能影响同一容器中的其他服务。

为了实现更**轻量、更快速**的故障恢复，我开发了 Rekindler：一个**进程级别**的守护进程，能够在推理服务崩溃时秒级检测并原地重启，无需重建容器。

目前已在以下框架的生产环境中验证使用：

| 框架 | 硬件 | 状态 |
| --- | --- | --- |
| vLLM | NVIDIA GPU | ✅ 已验证 |
| vLLM-Ascend | 华为 Ascend NPU | ✅ 已验证 |
| SGLang | NVIDIA GPU | ✅ 已验证 |
| MindIE | 华为 Ascend NPU | ✅ 已验证 |

架构上采用**配置驱动**设计，后续可轻松扩展支持更多推理框架（如阿里 PPU 等），只需添加配置和启动脚本，无需修改任何 Python 代码。

## 功能特点

- 🔄 **自动重启**：定期检测推理服务健康状态，异常时自动拉起
- 🖥️ **多硬件支持**：同时支持 NVIDIA GPU 和华为 Ascend NPU
- 🧩 **多框架支持**：vLLM、SGLang、MindIE 开箱即用
- ⚙️ **配置驱动**：一个守护进程引擎 + JSON 配置，零代码扩展新服务
- 📡 **健康检查 API**：FastAPI 提供 HTTP 接口，方便监控集成
- 🧠 **智能判断**：区分「服务故障」和「服务启动中」，避免重复拉起

## 工作原理

```
┌─────────────────────────────────────────────────┐
│                  Rekindler 守护进程               │
│                                                   │
│   ┌───────────┐    ┌──────────────┐              │
│   │ 健康检查   │    │ GPU/NPU 检测  │              │
│   │ /health   │    │ 显存占用判断   │              │
│   └─────┬─────┘    └──────┬───────┘              │
│         │                 │                       │
│         ▼                 ▼                       │
│   ┌─────────────────────────────┐                │
│   │       判断是否需要重启        │                │
│   │                             │                │
│   │ 健康检查失败 且 显存未占用     │                │
│   │   → 执行重启                 │                │
│   │                             │                │
│   │ 健康检查失败 但 显存已占用     │                │
│   │   → 可能在启动中，等待下次检查  │               │
│   │                             │                │
│   │ 健康检查成功                  │                │
│   │   → 服务正常，无需操作        │                │
│   └─────────────────────────────┘                │
│                                                   │
│   ┌───────────────┐                              │
│   │ FastAPI 服务   │ ← 对外暴露 /health 接口       │
│   │ (port: 8083)  │                              │
│   └───────────────┘                              │
└─────────────────────────────────────────────────┘
                        │
                        ▼
          ┌──────────────────────────┐
          │    推理服务 (vLLM 等)      │
          │    (port: 8081)           │
          └──────────────────────────┘
```

**检查周期**：每隔 `check_interval` 秒执行一次（默认 30 秒）

## 项目结构

```
rekindler/
├── start_vllm_gpu.sh            # 一键启动 vLLM (GPU)
├── start_vllm_npu.sh            # 一键启动 vLLM (NPU)
├── start_sglang_gpu.sh          # 一键启动 SGLang (GPU)
├── start_mindie_npu.sh          # 一键启动 MindIE (NPU)
├── stop_vllm_gpu.sh             # 一键停止
├── stop_vllm_npu.sh
├── stop_sglang_gpu.sh
├── stop_mindie_npu.sh
├── backend/
│   ├── listener.py              # 统一守护进程入口
│   ├── core/                    # 核心模块
│   │   ├── config.py            #   配置模型（ListenerConfig）
│   │   ├── health_checker.py    #   健康检查（HTTP /health）
│   │   └── hardware/            #   硬件检测
│   │       ├── gpu_checker.py   #     NVIDIA GPU（nvidia-smi）
│   │       └── npu_checker.py   #     Ascend NPU（npu-smi）
│   ├── configs/                 # 配置文件
│   │   ├── vllm_gpu.json
│   │   ├── vllm_npu.json
│   │   ├── sglang_gpu.json
│   │   └── mindie_npu.json
│   ├── scripts/                 # 推理服务启动/清理脚本
│   │   ├── vllm_gpu/
│   │   │   ├── start_service.sh #   启动推理服务
│   │   │   └── clean_service.sh #   停止推理服务
│   │   ├── vllm_npu/
│   │   ├── sglang_gpu/
│   │   └── mindie_npu/
│   ├── log/                     # 日志目录（含示例日志）
│   │   ├── *.log.example        #   示例日志供参考
│   │   └── *.log                #   运行时生成（已 gitignore）
│   └── requirements.txt
├── frontend/                    # 前端（预留）
├── .gitignore
├── LICENSE
└── README.md
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r backend/requirements.txt
```

> [!WARNING]
> `requirements.txt` **仅包含守护进程自身的依赖**（FastAPI、Pydantic、Requests 等），不包含推理框架。
> 你需要根据使用的推理框架**自行安装对应的包**：
> - **vLLM**：参考 [vLLM 安装文档](https://docs.vllm.ai/en/latest/getting_started/installation.html)
> - **SGLang**：参考 [SGLang 安装文档](https://docs.sglang.io/get_started/install.html)
> - **MindIE**：参考 [华为昇腾 MindIE 文档](https://www.hiascend.com/)

> [!CAUTION]
> **NPU 环境要求**：使用 Ascend NPU（`vllm_npu` / `mindie_npu`）需要：
> - 华为 Ascend 910B 系列硬件
> - 已安装 CANN 驱动和 `torch-npu`
> - 详见[华为官方文档](https://www.hiascend.com/)

### 2. 修改配置

#### 2.1 修改启动脚本（必须）

> [!IMPORTANT]
> **必须修改 `backend/scripts/` 下对应服务的 `start_service.sh`**，配置实际的模型路径和启动参数。
>
> ⚠️ **请先在终端中手动执行启动命令，确认服务能正常启动后，再写入 `start_service.sh`。**
>
> 例如 `backend/scripts/vllm_gpu/start_service.sh`：
> ```bash
> CUDA_VISIBLE_DEVICES=0 \
> vllm serve /your/model/path \
>  --tensor-parallel-size 1 \
>  --max-model-len 32768 \
>  --host 0.0.0.0 \
>  --port 8081 \
>  --served-model-name your-model-name
> ```

#### 2.2 修改配置文件（按需）

编辑 `backend/configs/` 下的 JSON 配置文件：

```json
{
    "service_name": "vllm",
    "hardware_type": "gpu",
    "port": 8083,
    "listen_port": 8081,
    "memory_threshold": 300,
    "num_threshold": 0.5,
    "check_interval": 30.0,
    "sh_file": "backend/scripts/vllm_gpu/start_service.sh",
    "startup_wait_time": 60.0,
    "log_dir": "backend/log"
}
```

配置文件参数说明：

| 参数                | 类型    | 默认值       | 说明                                       |
| ------------------- | ------- | ------------ | ------------------------------------------ |
| `service_name`      | str     | `"vllm"`     | 服务名称（用于日志标识和健康检查返回值）      |
| `hardware_type`     | str     | `"gpu"`      | 硬件类型：`gpu`（NVIDIA）或 `npu`（Ascend） |
| `port`              | int     | `8083`       | **守护进程** FastAPI 服务端口                |
| `listen_port`       | int     | `8081`       | **推理服务** 监听端口（用于健康检查）          |
| `sh_file`           | str     | —            | 推理服务启动脚本路径                          |
| `log_dir`           | str     | `backend/log`| 日志输出目录                                 |
| `check_interval`    | float   | `30.0`       | 健康检查间隔（秒）                            |
| `memory_threshold`  | int     | `300`        | 显存占用阈值（MiB），超过视为「被占用」        |
| `num_threshold`     | float   | `0.5`        | GPU/NPU 占用比例阈值（超过则认为硬件繁忙）     |
| `startup_wait_time` | float   | `60.0`       | 重启后等待服务启动的时间（秒）                 |

`check_interval`、`memory_threshold`、`startup_wait_time` 这几个参数请根据实际情况调整。模型越大、卡越多，启动时间越长，`startup_wait_time` 就要设得大一些。比如在 8 卡 H20 上跑 Qwen3-235B-A22B，我设的是 240 秒。

目前已在 NVIDIA H20、A100、A800 和华为 Ascend 910B1、910B2 上验证过。

> [!TIP]
> `port` 是守护进程自身的 API 端口，`listen_port` 是被监控的推理服务端口，两者不要混淆。

### 3. 启动守护进程

从项目根目录运行：

```bash
# vLLM on GPU
bash start_vllm_gpu.sh

# vLLM on Ascend NPU
bash start_vllm_npu.sh

# SGLang on GPU
bash start_sglang_gpu.sh

# MindIE on Ascend NPU
bash start_mindie_npu.sh
```

或直接运行（前台模式，方便调试）：

```bash
python backend/listener.py --config backend/configs/vllm_gpu.json
```

### 4. 健康检查

`$port` 对应配置文件中的 `port` 字段：

```bash
curl http://127.0.0.1:$port/health

# 例如 port 为 8083（默认值）
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

| `*_health` | `gpu_occupied` | 含义                               |
| ---------- | -------------- | ---------------------------------- |
| `true`     | `true`         | ✅ 服务运行正常                     |
| `false`    | `true`         | ⏳ 服务启动中（显存已占用，等待就绪） |
| `false`    | `false`        | ❌ 服务异常，守护进程将自动重启       |

### 5. 停止服务

```bash
# 一键停止（守护进程 + 推理服务）
bash stop_vllm_gpu.sh

# 仅停止推理服务（守护进程会自动重启它）
bash backend/scripts/vllm_gpu/clean_service.sh
```

> [!NOTE]
> 如果只停止推理服务而不停止守护进程，守护进程会在下一次检查周期自动重启推理服务。这可以用于**热更新模型**：修改 `start_service.sh` 中的模型路径后，只 kill 推理服务即可。

### 6. 查看日志

```bash
# 守护进程日志
tail -f backend/log/nohup_vllm_gpu.log

# 推理服务日志
tail -f backend/log/vllm_service_*.log
```

`backend/log/` 下有 `.example` 后缀的示例日志供参考。

#### 日志解析示例

以下是守护进程从启动到稳定运行的完整日志过程解读（摘自 `nohup_vllm.log.example`）：

**阶段一：启动 & 打印配置**

```log
2025-06-26 16:42:49 - INFO - Starting VLLM listener with configuration:
  - Service name:       vllm
  - Port:               8081        ← 推理服务端口
  - Listening port:     8083        ← 守护进程 API 端口
  - Check interval:     30.0 seconds
  - memory_threshold:   300
```

守护进程启动后先打印所有配置，方便确认参数是否正确。

**阶段二：首次检查失败 → 自动重启**

```log
16:42:49 - ERROR   - Health check failed: Connection refused    ← 推理服务未启动
16:42:49 - WARNING - Service vllm is not healthy, attempting to restart  ← 触发重启
16:42:49 - INFO    - Restarting service: vllm
16:42:49 - INFO    - Service vllm is restarting..., please wait at least 60.0 seconds!!!!!!
16:43:49 - INFO    - Service vllm restart command executed      ← 等待 60s 后继续
```

首次启动时推理服务尚未运行，守护进程检测到健康检查失败且 GPU 未被占用，**判定为异常并执行重启**。

**阶段三：服务启动中 → 等待**

```log
16:44:19 - ERROR   - Health check failed: Connection refused    ← 仍未就绪
16:44:19 - INFO    - Service vllm is not healthy, but GPU is occupied, not restart
                                                                ← GPU 已被占用，说明正在加载模型
16:44:19 - INFO    - Please wait for the GPU to be released, or for the next health check
```

30 秒后再次检查：健康检查仍然失败，但检测到 **GPU 显存已被占用**。守护进程判断模型正在加载中，**不会重复拉起**，等待下一轮检查。

**阶段四：服务就绪 → 稳定运行**

```log
16:44:50 - INFO    - Service vllm is healthy                    ← ✅ 服务就绪
16:45:20 - INFO    - Service vllm is healthy
16:45:50 - INFO    - Service vllm is healthy
...
```

推理服务加载完成，健康检查恢复正常，守护进程进入**稳定监控状态**，每 30 秒检查一次。

**阶段五：服务异常 → 再次自动恢复**

```log
16:45:50 - ERROR   - Health check failed                        ← 服务突然挂了
16:45:50 - WARNING - Service vllm is not healthy, attempting to restart
16:45:50 - INFO    - Restarting service: vllm                   ← 自动拉起
...
16:47:50 - INFO    - Service vllm is healthy                    ← ✅ 恢复正常
```

如果推理服务在运行中崩溃，守护进程会在下一个检查周期检测到并**自动拉起恢复**。

> [!TIP]
> 日志中的关键标识：
> - `ERROR - Health check failed` → 推理服务不可达
> - `WARNING - attempting to restart` → 触发了重启操作
> - `INFO - but GPU is occupied, not restart` → 正在启动中，跳过重启
> - `INFO - Service ... is healthy` → 一切正常

## 支持的服务

| 服务   | 硬件        | 配置文件          | 启动脚本              |
| ------ | ----------- | ----------------- | --------------------- |
| vLLM   | NVIDIA GPU  | `vllm_gpu.json`   | `start_vllm_gpu.sh`   |
| vLLM   | Ascend NPU  | `vllm_npu.json`   | `start_vllm_npu.sh`   |
| SGLang | NVIDIA GPU  | `sglang_gpu.json` | `start_sglang_gpu.sh` |
| MindIE | Ascend NPU  | `mindie_npu.json` | `start_mindie_npu.sh` |

## 扩展新服务

新增一种推理框架 **不需要修改任何 Python 代码**，只需 3 步：

1. **新建配置文件** `backend/configs/your_service.json`
2. **新建启动脚本** `backend/scripts/your_service/start_service.sh`
3. **新建根目录启动脚本** `start_your_service.sh`

## 常见问题

### Q: 守护进程启动后推理服务迟迟不拉起？

检查 `start_service.sh` 中的模型路径是否正确，以及 `listen_port` 是否和推理服务实际监听的端口一致。

### Q: 日志显示 "GPU is occupied, not restart" 但服务并没有在运行？

可能有其他进程占用了 GPU 显存。用 `nvidia-smi`（GPU）或 `npu-smi info`（NPU）检查，清理占用后守护进程会在下次检查时自动拉起服务。

### Q: 如何调整检查频率？

修改配置文件中的 `check_interval` 字段，单位为秒。建议不低于 10 秒。

## 更新日志

### v1.0.0 (2025-06-26)

- 🎉 初始版本发布
- 支持 vLLM (GPU/NPU)、SGLang (GPU)、MindIE (NPU)
- 配置驱动的统一守护进程架构
- FastAPI 健康检查 API
- 智能重启（区分服务故障和启动中状态）

### v2.0.0 (2026-03-26)

- 🔧 重构：4 个独立模块合并为统一引擎 `listener.py`
- 📁 新增前后端分离的目录结构
- ⚡ 新增根目录一键启动/停止脚本
- 📝 完善 README 文档和示例日志

## 贡献指南

欢迎贡献！请遵循以下步骤：

1. **Fork** 本仓库
2. 创建功能分支：`git checkout -b feature/your-feature`
3. 提交更改：`git commit -m 'feat: add your feature'`
4. 推送分支：`git push origin feature/your-feature`
5. 提交 **Pull Request**

### Commit 规范

| 前缀     | 说明         |
| -------- | ------------ |
| `feat:`  | 新功能       |
| `fix:`   | Bug 修复     |
| `docs:`  | 文档更新     |
| `refactor:` | 代码重构  |
| `chore:` | 构建/配置变更 |

### 提 Issue

- 🐛 Bug 报告：请附带日志和配置信息
- 💡 功能建议：请描述使用场景

## 致谢

本项目基于以下优秀的开源项目构建：

- [vLLM](https://github.com/vllm-project/vllm) — 高性能 LLM 推理引擎
- [SGLang](https://github.com/sgl-project/sglang) — 快速 LLM 服务框架
- [MindIE](https://www.hiascend.com/) — 华为昇腾推理引擎
- [FastAPI](https://github.com/tiangolo/fastapi) — 现代 Python Web 框架
- [PyTorch](https://pytorch.org/) — 深度学习框架

## License

Apache-2.0 — 详见 [LICENSE](LICENSE) 文件
