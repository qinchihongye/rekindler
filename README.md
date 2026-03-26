# Rekindler 🔥

[English](README.md) | [中文](README.Chinese.md)

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8%2B-brightgreen.svg)](https://python.org)
[![vLLM](https://img.shields.io/badge/vLLM-supported-orange.svg)](https://github.com/vllm-project/vllm)
[![SGLang](https://img.shields.io/badge/SGLang-supported-orange.svg)](https://github.com/sgl-project/sglang)
[![MindIE](https://img.shields.io/badge/MindIE-supported-orange.svg)](https://www.hiascend.com/)

A lightweight daemon that monitors and auto-restarts model inference services (vLLM, SGLang, MindIE) on both NVIDIA GPU and Huawei Ascend NPU.

---

## 📖 Table of Contents

- [Background](#background)
- [Features](#features)
- [How It Works](#how-it-works)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
  - [Install Dependencies](#1-install-dependencies)
  - [Modify Configuration](#2-modify-configuration)
  - [Start Daemon](#3-start-daemon)
  - [Health Check](#4-health-check)
  - [Stop Service](#5-stop-service)
  - [View Logs](#6-view-logs)
- [Supported Services](#supported-services)
- [Adding New Services](#adding-new-services)
- [FAQ](#faq)
- [Changelog](#changelog)
- [Contributing](#contributing)
- [Acknowledgments](#acknowledgments)
- [License](#license)

## Background

In our LLM deployment workflow, we use CI/CD pipelines for one-click containerized deployment. However, in production, inference services (e.g., vLLM) can crash due to OOM, CUDA errors, or other exceptions. In such cases, container orchestration platforms can only provide **container-level** restarts — which means the entire container gets rebuilt, leading to long recovery times and potentially affecting other services in the same container.

To achieve **lighter and faster** failure recovery, I developed Rekindler: a **process-level** daemon that detects inference service crashes within seconds and restarts them in-place, without rebuilding the container.

It has been verified in production with the following frameworks:

| Framework | Hardware | Status |
| --- | --- | --- |
| vLLM | NVIDIA GPU | ✅ Verified |
| vLLM-Ascend | Huawei Ascend NPU | ✅ Verified |
| SGLang | NVIDIA GPU | ✅ Verified |
| MindIE | Huawei Ascend NPU | ✅ Verified |

The architecture is **configuration-driven**, making it easy to extend support for new inference frameworks (e.g., Alibaba PPU) by simply adding a config file and a startup script — no Python code changes required.

## Features

- 🔄 **Auto-Restart**: Periodically checks inference service health and automatically restarts on failure
- 🖥️ **Multi-Hardware**: Supports both NVIDIA GPU and Huawei Ascend NPU
- 🧩 **Multi-Framework**: vLLM, SGLang, MindIE out of the box
- ⚙️ **Config-Driven**: One daemon engine + JSON config, zero-code extension for new services
- 📡 **Health Check API**: FastAPI-powered HTTP endpoint for easy monitoring integration
- 🧠 **Smart Detection**: Distinguishes between "service crashed" and "service starting up" to avoid redundant restarts

## How It Works

```
┌─────────────────────────────────────────────────┐
│                 Rekindler Daemon                  │
│                                                   │
│   ┌───────────┐    ┌──────────────┐              │
│   │  Health    │    │  GPU/NPU     │              │
│   │  Check    │    │  Detection   │              │
│   └─────┬─────┘    └──────┬───────┘              │
│         │                 │                       │
│         ▼                 ▼                       │
│   ┌─────────────────────────────┐                │
│   │    Restart Decision Logic    │                │
│   │                             │                │
│   │ Health FAIL + VRAM free     │                │
│   │   → Restart service         │                │
│   │                             │                │
│   │ Health FAIL + VRAM occupied │                │
│   │   → Likely starting, wait   │                │
│   │                             │                │
│   │ Health OK                   │                │
│   │   → Service normal, no-op   │                │
│   └─────────────────────────────┘                │
│                                                   │
│   ┌───────────────┐                              │
│   │ FastAPI Server │ ← Exposes /health endpoint   │
│   │ (port: 8083)  │                              │
│   └───────────────┘                              │
└─────────────────────────────────────────────────┘
                        │
                        ▼
          ┌──────────────────────────┐
          │  Inference Service (vLLM) │
          │  (port: 8081)            │
          └──────────────────────────┘
```

**Check interval**: Runs every `check_interval` seconds (default: 30s)

## Project Structure

```
rekindler/
├── start_vllm_gpu.sh            # One-click start vLLM (GPU)
├── start_vllm_npu.sh            # One-click start vLLM (NPU)
├── start_sglang_gpu.sh          # One-click start SGLang (GPU)
├── start_mindie_npu.sh          # One-click start MindIE (NPU)
├── stop_vllm_gpu.sh             # One-click stop
├── stop_vllm_npu.sh
├── stop_sglang_gpu.sh
├── stop_mindie_npu.sh
├── backend/
│   ├── listener.py              # Unified daemon entry point
│   ├── core/                    # Core modules
│   │   ├── config.py            #   Config model (ListenerConfig)
│   │   ├── health_checker.py    #   Health check (HTTP /health)
│   │   └── hardware/            #   Hardware detection
│   │       ├── gpu_checker.py   #     NVIDIA GPU (nvidia-smi)
│   │       └── npu_checker.py   #     Ascend NPU (npu-smi)
│   ├── configs/                 # Config files
│   │   ├── vllm_gpu.json
│   │   ├── vllm_npu.json
│   │   ├── sglang_gpu.json
│   │   └── mindie_npu.json
│   ├── scripts/                 # Service start/clean scripts
│   │   ├── vllm_gpu/
│   │   │   ├── start_service.sh #   Start inference service
│   │   │   └── clean_service.sh #   Stop inference service
│   │   ├── vllm_npu/
│   │   ├── sglang_gpu/
│   │   └── mindie_npu/
│   ├── log/                     # Logs (with example logs)
│   │   ├── *.log.example        #   Example logs for reference
│   │   └── *.log                #   Generated at runtime (gitignored)
│   └── requirements.txt
├── frontend/                    # Frontend (reserved)
├── .gitignore
├── LICENSE
└── README.md
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r backend/requirements.txt
```

> [!WARNING]
> `requirements.txt` **only contains dependencies for the daemon itself** (FastAPI, Pydantic, Requests, etc.), NOT the inference frameworks.
> You need to **install the inference framework separately**:
> - **vLLM**: See [vLLM Installation](https://docs.vllm.ai/en/latest/getting_started/installation.html)
> - **SGLang**: See [SGLang Installation](https://docs.sglang.io/get_started/install.html)
> - **MindIE**: See [Huawei Ascend MindIE Docs](https://www.hiascend.com/)

> [!CAUTION]
> **NPU Requirements**: Using Ascend NPU (`vllm_npu` / `mindie_npu`) requires:
> - Huawei Ascend 910B series hardware
> - CANN driver and `torch-npu` installed
> - See [Huawei official docs](https://www.hiascend.com/)

### 2. Modify Configuration

#### 2.1 Modify Startup Script (Required)

> [!IMPORTANT]
> **You must modify the `start_service.sh`** under `backend/scripts/` for your target service, configuring the actual model path and launch parameters.
>
> ⚠️ **Please verify the startup command manually in your terminal first, then write it into `start_service.sh`.**
>
> Example `backend/scripts/vllm_gpu/start_service.sh`:
> ```bash
> CUDA_VISIBLE_DEVICES=0 \
> vllm serve /your/model/path \
>  --tensor-parallel-size 1 \
>  --max-model-len 32768 \
>  --host 0.0.0.0 \
>  --port 8081 \
>  --served-model-name your-model-name
> ```

#### 2.2 Modify Config File (Optional)

Edit the JSON config files under `backend/configs/`:

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

Config parameter reference:

| Parameter           | Type    | Default      | Description                                          |
| ------------------- | ------- | ------------ | ---------------------------------------------------- |
| `service_name`      | str     | `"vllm"`     | Service name (used in logs and health check response) |
| `hardware_type`     | str     | `"gpu"`      | Hardware type: `gpu` (NVIDIA) or `npu` (Ascend)      |
| `port`              | int     | `8083`       | **Daemon** FastAPI server port                       |
| `listen_port`       | int     | `8081`       | **Inference service** port (for health checks)       |
| `sh_file`           | str     | —            | Path to the inference service startup script         |
| `log_dir`           | str     | `backend/log`| Log output directory                                 |
| `check_interval`    | float   | `30.0`       | Health check interval (seconds)                      |
| `memory_threshold`  | int     | `300`        | VRAM threshold (MiB), above = "occupied"             |
| `num_threshold`     | float   | `0.5`        | GPU/NPU utilization threshold                        |
| `startup_wait_time` | float   | `60.0`       | Wait time after restart (seconds)                    |

`check_interval`, `memory_threshold`, and `startup_wait_time` should be adjusted based on your setup. Larger models with more GPUs take longer to start, so `startup_wait_time` should be set higher. For example, running Qwen3-235B-A22B on 8x H20 GPUs, I set it to 240 seconds.

Tested on NVIDIA H20, A100, A800 and Huawei Ascend 910B1, 910B2.

> [!TIP]
> `port` is the daemon's own API port, `listen_port` is the monitored inference service port — don't mix them up.

### 3. Start Daemon

Run from the project root:

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

Or run directly (foreground mode, useful for debugging):

```bash
python backend/listener.py --config backend/configs/vllm_gpu.json
```

### 4. Health Check

`$port` corresponds to the `port` field in the config file:

```bash
curl http://127.0.0.1:$port/health

# e.g., port 8083 (default)
curl http://127.0.0.1:8083/health
```

Response example:

```json
{
    "code": 200,
    "data": {
        "vllm_health": true,
        "gpu_occupied": true
    }
}
```

Status reference:

| `*_health` | `gpu_occupied` | Meaning                                    |
| ---------- | -------------- | ------------------------------------------ |
| `true`     | `true`         | ✅ Service running normally                 |
| `false`    | `true`         | ⏳ Service starting up (VRAM occupied)      |
| `false`    | `false`        | ❌ Service down, daemon will auto-restart    |

### 5. Stop Service

```bash
# Stop everything (daemon + inference service)
bash stop_vllm_gpu.sh

# Stop inference service only (daemon will auto-restart it)
bash backend/scripts/vllm_gpu/clean_service.sh
```

> [!NOTE]
> Stopping only the inference service while keeping the daemon running allows for **hot model updates**: modify the model path in `start_service.sh`, then kill the inference service — the daemon will restart it with the new config.

### 6. View Logs

```bash
# Daemon log
tail -f backend/log/nohup_vllm_gpu.log

# Inference service log
tail -f backend/log/vllm_service_*.log
```

Example logs with `.example` suffix are available in `backend/log/` for reference.

#### Log Analysis Example

Here is a walkthrough of the daemon's lifecycle from startup to stable operation (from `nohup_vllm.log.example`):

**Phase 1: Startup & Config Output**

```log
2025-06-26 16:42:49 - INFO - Starting VLLM listener with configuration:
  - Service name:       vllm
  - Port:               8081        ← Inference service port
  - Listening port:     8083        ← Daemon API port
  - Check interval:     30.0 seconds
  - memory_threshold:   300
```

The daemon prints all config on startup for verification.

**Phase 2: First Check Fails → Auto Restart**

```log
16:42:49 - ERROR   - Health check failed: Connection refused    ← Service not running
16:42:49 - WARNING - Service vllm is not healthy, attempting to restart  ← Triggers restart
16:42:49 - INFO    - Restarting service: vllm
16:42:49 - INFO    - Service vllm is restarting..., please wait at least 60.0 seconds!!!!!!
16:43:49 - INFO    - Service vllm restart command executed      ← Waited 60s, continues
```

On first startup, the inference service isn't running yet. The daemon detects the health check failure with no GPU occupancy, and **triggers a restart**.

**Phase 3: Service Starting Up → Wait**

```log
16:44:19 - ERROR   - Health check failed: Connection refused    ← Still not ready
16:44:19 - INFO    - Service vllm is not healthy, but GPU is occupied, not restart
                                                                ← GPU occupied = model loading
16:44:19 - INFO    - Please wait for the GPU to be released, or for the next health check
```

30 seconds later: health check still fails, but **GPU VRAM is occupied**. The daemon recognizes the model is loading and **does not restart again**, waiting for the next check cycle.

**Phase 4: Service Ready → Stable Operation**

```log
16:44:50 - INFO    - Service vllm is healthy                    ← ✅ Service ready
16:45:20 - INFO    - Service vllm is healthy
16:45:50 - INFO    - Service vllm is healthy
...
```

Model loaded successfully. Health checks pass, daemon enters **stable monitoring mode**, checking every 30 seconds.

**Phase 5: Service Crash → Auto Recovery**

```log
16:45:50 - ERROR   - Health check failed                        ← Service crashed
16:45:50 - WARNING - Service vllm is not healthy, attempting to restart
16:45:50 - INFO    - Restarting service: vllm                   ← Auto restart
...
16:47:50 - INFO    - Service vllm is healthy                    ← ✅ Recovered
```

If the inference service crashes during operation, the daemon detects it in the next check cycle and **automatically restarts it**.

> [!TIP]
> Key log identifiers:
> - `ERROR - Health check failed` → Inference service unreachable
> - `WARNING - attempting to restart` → Restart triggered
> - `INFO - but GPU is occupied, not restart` → Starting up, skipping restart
> - `INFO - Service ... is healthy` → All good

## Supported Services

| Service | Hardware    | Config File       | Start Script          |
| ------- | ----------- | ----------------- | --------------------- |
| vLLM    | NVIDIA GPU  | `vllm_gpu.json`   | `start_vllm_gpu.sh`   |
| vLLM    | Ascend NPU  | `vllm_npu.json`   | `start_vllm_npu.sh`   |
| SGLang  | NVIDIA GPU  | `sglang_gpu.json` | `start_sglang_gpu.sh` |
| MindIE  | Ascend NPU  | `mindie_npu.json` | `start_mindie_npu.sh` |

## Adding New Services

Adding a new inference framework requires **zero Python code changes** — just 3 steps:

1. **Create a config file**: `backend/configs/your_service.json`
2. **Create a startup script**: `backend/scripts/your_service/start_service.sh`
3. **Create a root-level start script**: `start_your_service.sh`

## FAQ

### Q: Inference service not starting after daemon launch?

Check if the model path in `start_service.sh` is correct, and verify that `listen_port` matches the actual port your inference service listens on.

### Q: Log shows "GPU is occupied, not restart" but the service isn't actually running?

Another process may be occupying GPU VRAM. Check with `nvidia-smi` (GPU) or `npu-smi info` (NPU), clean up the occupying process, and the daemon will auto-start the service on the next check.

### Q: How to adjust check frequency?

Modify the `check_interval` field in the config file (in seconds). Recommended minimum: 10 seconds.

## Changelog

### v1.0.0 (2025-06-26)

- 🎉 Initial release
- Support for vLLM (GPU/NPU), SGLang (GPU), MindIE (NPU)
- Config-driven unified daemon architecture
- FastAPI health check API
- Smart restart (distinguishes service failure from startup state)

### v2.0.0 (2026-03-26)

- 🔧 Refactor: Consolidated 4 separate modules into unified engine `listener.py`
- 📁 Added frontend/backend separated directory structure
- ⚡ Added root-level one-click start/stop scripts
- 📝 Enhanced README documentation and example logs

## Contributing

Contributions are welcome! Please follow these steps:

1. **Fork** this repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m 'feat: add your feature'`
4. Push the branch: `git push origin feature/your-feature`
5. Submit a **Pull Request**

### Commit Convention

| Prefix      | Description         |
| ----------- | ------------------- |
| `feat:`     | New feature         |
| `fix:`      | Bug fix             |
| `docs:`     | Documentation       |
| `refactor:` | Code refactoring    |
| `chore:`    | Build/config changes|

### Filing Issues

- 🐛 Bug reports: Please include logs and config info
- 💡 Feature requests: Please describe the use case

## Acknowledgments

Built with the following excellent open-source projects:

- [vLLM](https://github.com/vllm-project/vllm) — High-performance LLM inference engine
- [SGLang](https://github.com/sgl-project/sglang) — Fast LLM serving framework
- [MindIE](https://www.hiascend.com/) — Huawei Ascend inference engine
- [FastAPI](https://github.com/tiangolo/fastapi) — Modern Python web framework
- [PyTorch](https://pytorch.org/) — Deep learning framework

## License

Apache-2.0 — See [LICENSE](LICENSE) file
