# 应用程序运行说明

此文档提供了关于如何设置和运行该应用程序的详细说明。该应用程序包括一个聊天界面前端、心理咨询服务后台以及用户管理系统。

## 快速开始

1. 配置ZhipuAI API Key:
   打开 demos/chat_demos/Langchain-Chatchat/libs/chatchat-server/chatchat/server/api_server/chat_routes.py 文件。
   在第74行位置填入你的ZhipuAI API Key。
   启动后请确保选择模型为 chatchat。

2. 安装前端依赖:
   安装 npm 或 cnpm,node.js等软件，并安装依赖。

3. 配置数据库连接:
   更改这两个文件中的数据库链接为你运行环境的绝对路径。
   ![文件1](https://github.com/garveyMui/MetaBCI/blob/master/images/img1.png)
![文件2](https://github.com/garveyMui/MetaBCI/blob/master/images/img2.png)
4. 启动应用程序:
   打开浏览器并访问 http://127.0.0.1:5000 进行注册与登录。

5. 启动AI模型:
   我们的后台建立在 chatchat 基础上。
   登录后按照图示依次启动AI模型。
   
![第一步](https://github.com/garveyMui/MetaBCI/blob/master/images/img3.png)
![第二步](https://github.com/garveyMui/MetaBCI/blob/master/images/img4.png)
![第三步](https://github.com/garveyMui/MetaBCI/blob/master/images/img5.png)
![第四步](https://github.com/garveyMui/MetaBCI/blob/master/images/img6.png)

6. 情感识别:
   用户登录后会开启情感接收端口。
   运行 Online_emotion.py 文件进行情感识别。


7. 模拟脑电信号测试（无脑电帽时）:
   在 `demos/chat_demos` 目录下运行：
   `python mock_eeg_emotion.py --mode random --collector-host 127.0.0.1 --collector-port 4023`
   可选模式：`calm / stress / happy / random`。
   如果只想验证分类不发UDP，可加 `--dry-run`。
