# 📚 课堂派 章节测试题库下载器

> Ketangpai Exam Downloader — 一键拉取课程所有章节测试题目 + 答案 + 你的作答记录，适用于考试复习等场景

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## ✨ 功能

- ✅ 登录课堂派（无需额外加密）
- ✅ 自动搜索课程
- ✅ 拉取全部章节测试的 **题目 + 选项 + 正确答案**
- ✅ 高亮你的 **作答记录**（正确 ✅ / 错误 ❌）
- ✅ 输出为清爽的 **Markdown 文件**，方便复习
- ✅ 支持命令行参数 / JSON 配置文件

## 🚀 快速开始

```bash
# 1. 克隆
git clone https://github.com/yourname/ktp-exam-downloader.git
cd ktp-exam-downloader

# 2. 安装依赖
pip install -r requirements.txt

# 3. 直接运行
python ktp_exam_downloader.py -a 138xxxxxx90 -p 你的密码 -c 路基路面

# 4. 或者用配置文件
cp config.example.json config.json
# 编辑 config.json 填入账号密码
python ktp_exam_downloader.py --config config.json
```

## 📖 使用说明

### 命令行参数

| 参数 | 简写 | 说明 | 默认值 |
|:---|---:|:---|:---:|
| `--account` | `-a` | 课堂派账号（手机号/邮箱） | — |
| `--password` | `-p` | 课堂派密码 | — |
| `--course` | `-c` | 课程名称关键词 | — |
| `--semester` | `-s` | 学年，如 `2025-2026` | `2025-2026` |
| `--term` | `-t` | 学期（1 或 2） | `2` |
| `--output` | `-o` | 输出目录 | 当前目录 |
| `--config` | | 配置文件路径 | — |
| `--quiet` | `-q` | 静默模式 | — |
| `--version` | | 显示版本号 | — |

### 示例

```bash
# 指定学期
python ktp_exam_downloader.py -a 138xxxx -p 123456 -c 交通设计 -s 2024-2025 -t 1

# 使用配置文件
python ktp_exam_downloader.py --config config.json

# 指定输出目录
python ktp_exam_downloader.py -a 138xxxx -p 123456 -c 路基路面 -o ./output
```

### 配置文件

```json
{
    "account": "138xxxxxx90",
    "password": "your_password",
    "course": "路基路面",
    "semester": "2025-2026",
    "term": 2
}
```

## 📄 输出示例

````markdown
## 1. 01概论
共 10 题

### 第1题 | 单选题 | 10.0分 | 得分: 10.0
路基路面是一项______工程，有的公路延续数百公里，甚至上千公里。
- [ ] 点状
- [x] **线状** ✅ ← 你的答案（正确）
- [ ] 面状
- [ ] 块状
````

## 🔧 技术原理

课堂派前端 SPA 通过 `TestpaperApi/doSubjectList` 接口获取题目数据，返回的 JSON 包含：

| 字段 | 说明 |
|:---|:---|
| `title` | 题目内容（HTML） |
| `replenishtype` | 题型（单选题/多选题等） |
| `options` | 选项列表 |
| `answer` | 正确答案的 option ID |
| `myanswer` | 你的作答 option ID |
| `myscore` | 你的得分 |
| `explanation` | 解析 |

**无需额外加密，明文密码即可登录。**

## 📦 依赖

- `requests` — HTTP 客户端

仅此一个外部依赖。

## 🤝 贡献

欢迎提 Issue 和 PR！

## ⚠️ 免责声明

本项目仅供学习交流使用，请勿用于商业用途或违反课堂派用户协议的行为。

## 📜 License

MIT
