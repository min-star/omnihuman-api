# 即梦数字人视频生成（Streamlit Demo）

基于 **火山引擎即梦（Jimeng）CV API** 的数字人视频生成示例项目。
支持 **图片 + 音频驱动** 的数字人视频生成流程，集成了主体检测、Mask 选择、Prompt 控制、视频生成与下载等完整功能，适合 **内部测试 / 技术演示 / 二次开发**。

---

## 一、功能概览

### ✅ 核心功能

* 🔐 **AK / SK 在线填写**

  * 支持火山引擎 Access Key / Secret Key 在页面中直接输入
  * 无需写死在代码中，便于多账号切换

* 🖼 **图片上传（人物图像）**

  * 支持 JPG / PNG 格式
  * 自动保存到本地并生成公网可访问 URL

* 🎵 **音频上传（驱动音频）**

  * 支持 MP3 / WAV 格式
  * 作为数字人说话 / 表情驱动音频

* 🔍 **人物 / 主体检测**

  * 调用即梦目标检测接口
  * 自动识别图片中的多个主体
  * 返回每个主体对应的 Mask

* ✂️ **Mask 裁剪与可视化预览**

  * 根据 Mask 自动裁剪主体区域
  * 按最长边缩放，统一预览尺寸

* 🧩 **主体选择机制**

  * 可从多个检测到的主体中选择
  * 支持「不使用 Mask，直接使用原图」模式

* ✏️ **Prompt 驱动控制**

  * 支持输入文本 Prompt
  * 用于控制表情、稳定性、真实感、风格等

* 🎬 **数字人视频生成**

  * 提交视频生成任务
  * 自动轮询任务状态

* 📥 **视频结果展示与下载**

  * 生成完成后可直接在线播放
  * 支持下载 MP4 文件
  * 视频按「时间 + UUID」自动命名并保存

---

## 二、运行环境要求

* Python **≥ 3.9**（推荐 3.10）
* 操作系统：Linux / macOS / Windows
* 一个 **可公网访问的静态文件服务**（用于图片和音频 URL）

> ⚠️ 火山引擎接口要求：
> 图片和音频 URL **必须可以被公网直接访问**

---

## 三、依赖安装

### 1️⃣ 创建虚拟环境（强烈推荐）

```bash
python -m venv venv
source venv/bin/activate
```

Windows：

```bash
venv\\Scripts\\activate
```

---

### 2️⃣ 安装 Python 依赖

直接安装：

```bash
pip install streamlit requests pillow numpy
```

或使用 `requirements.txt`：

```txt
streamlit>=1.30
requests>=2.28
Pillow>=9.5
numpy>=1.23
```

```bash
pip install -r requirements.txt
```

---

## 四、目录结构说明

```text
.
├── app.py              # Streamlit 主程序
├── res/                # 生成的视频结果保存目录
├── requirements.txt    # Python 依赖
└── README.md
```

请确保 `res` 目录存在：

```bash
mkdir -p res
```

---

## 五、静态文件服务配置（非常重要）

项目中会将 **上传的图片 / 音频保存到本地目录**，并通过 HTTP 方式对外暴露。

### 示例配置（本地测试）

```python
UPLOAD_DIR = "/home/yourname/data/uploads"
PUBLIC_BASE_URL = "http://你的IP:8000"
```

启动一个简单的 HTTP 服务：

```bash
cd /home/yourname/data/uploads
python -m http.server 8000
```

> 生产环境建议使用：
>
> * nginx
> * caddy
> * cloudflared

---

## 六、启动项目

```bash
streamlit run app.py
```

浏览器访问：

```
http://localhost:8501
```

---

## 七、使用流程说明

1. 打开页面，输入 **Access Key / Secret Key**
2. 上传一张 **人物图片**
3. 上传一段 **音频文件**
4. （可选）输入 **Prompt 描述**
5. 点击「开始检测」
6. 从检测到的主体中选择目标（或选择原图）
7. 等待视频生成完成
8. 在线预览并下载生成的视频

---

## 八、常见注意事项

* 建议使用 **清晰正脸人物图像**
* 音频时长不宜过长（建议 < 60 秒）
* 若接口返回失败，请重点检查：

  * AK / SK 是否正确
  * 图片 / 音频 URL 是否能被公网访问
  * 文件格式是否符合要求

---

## 九、适用场景

* 数字人 / 虚拟人能力演示
* 内部技术验证
* API 调用示例参考
* 二次开发或功能扩展基础工程

---

## 十、免责声明

本项目仅作为 **火山引擎即梦 API 使用示例（Demo）**。
生成效果、接口能力、配额限制等以火山引擎官方文档为准。

---

## 十一、可扩展方向（建议）

* Docker 一键部署
* AK / SK 使用环境变量管理
* 多任务队列 / 并发控制
* 历史任务与结果管理
* Prompt 模板与预设管理

---

如需进一步定制或扩展，请根据实际业务需求进行二次开发。
