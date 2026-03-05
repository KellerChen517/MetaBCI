# 应用程序运行说明

此文档提供了关于如何设置和运行该应用程序的详细说明。该应用程序包括一个简洁聊天前端、AI聊天后端接口、心理咨询辅助逻辑以及用户管理系统。

## 快速开始

1. 配置智谱智能体:
   启动 `web.py` 前设置环境变量：
   - `ZHIPU_API_KEY`：你的智谱 API Key
   - `ZHIPU_API_BASE`：接口地址（默认 `https://open.bigmodel.cn/api/paas/v4`）
   - `ZHIPU_MODEL`：模型名（默认 `glm-5`）
   不配置 Key 时，系统会进入本地演示回复模式。

2. 安装依赖:
   安装 Python 依赖并确保 Flask/SQLAlchemy 可用。

3. 配置数据库连接:
   更改这两个文件中的数据库链接为你运行环境的绝对路径。
   ![文件1](https://github.com/garveyMui/MetaBCI/blob/master/images/img1.png)
![文件2](https://github.com/garveyMui/MetaBCI/blob/master/images/img2.png)
4. 启动应用程序:
   打开浏览器并访问 http://127.0.0.1:5000 进行注册与登录。

5. 启动聊天服务:
   运行 `python demos/chat_demos/web.py`，浏览器访问 `http://127.0.0.1:5000`。

6. 情感识别:
   用户登录后会开启情感接收端口。
   运行 Online_emotion.py 文件进行情感识别。


7. 模拟脑电信号测试（无脑电帽时）:
   在 `demos/chat_demos` 目录下运行：
   `python mock_eeg_emotion.py --mode random --collector-host 127.0.0.1 --collector-port 4023`
   可选模式：`calm / stress / happy / random`。
   如果只想验证分类不发UDP，可加 `--dry-run`。
