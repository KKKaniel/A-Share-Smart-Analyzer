# 📈 大A智能分析系统

A股中小盘智能筛选与多维度分析，使用 GitHub Actions 自动运行并生成网页报告。

## 在线访问

部署后可通过 GitHub Pages 访问：

[https://kkkkaniel.github.io/A-Share-Smart-Analyzer](https://kkkkaniel.github.io/A-Share-Smart-Analyzer)

## 功能

- 自动抓取 A 股实时行情（akshare）
- 中小盘筛选：市值 20~200 亿、PE ≤ 60、PB ≤ 5
- 多维度评分与 TOP20 排名
- 自动生成网页报告
- 工作日定时更新

## 本地运行

```bash
pip install -r requirements.txt
python analyzer/main.py
```

生成后的网页在 `docs/index.html`。

## 免责声明

本项目仅供学习研究，不构成投资建议。
