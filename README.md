# cn-date

![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Tests](https://img.shields.io/badge/tests-24%20passing-success)
![Dependencies](https://img.shields.io/badge/dependencies-0-brightgreen)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)

零依赖的中文自然语言日期解析 —— 把「明天下午3点」「下周一」「3天后晚上8点半」变成可用的 `datetime`。

- **相对日**：今天 / 今晚 / 明天 / 后天 / 大后天
- **星期**：周X / 星期X / 礼拜X，支持 本周 / 下周 / 下下周（已过的自动顺延到下周）
- **偏移**：N天后 / N周后 / N个月后 / N小时后 / N分钟后 / 半小时后，支持 两 / 俩 / 仨 / 一两
- **日号**：本月X号 / 下月X号 / X号 / 月底；超出月末自动钳制（1月31日 + 1个月 → 2月28日）
- **时刻**：X点 / X点半 / X点X分 / `14:30`，配合 凌晨 / 早上 / 上午 / 中午 / 下午 / 晚上 段词
- **输入边界**：拒绝 24 点、超范围分钟、0 号与被截断的多位数字；无法解析时返回 `None`
- **透明度**：`ParseResult.has_date / has_time` 告诉你哪些成分是显式给出的，哪些是默认补齐

零第三方依赖，Python ≥ 3.8。

## 安装

```bash
pip install .
```

## 真实运行示例

以 `--now 2026-03-04T10:00`（周三）为基准：

```console
$ python -m cn_date "明天下午3点" "下周一上午9点" "3天后晚上8点半" "半小时后" "月底" "下周五" --now 2026-03-04T10:00
明天下午3点  →  2026-03-05 15:00  [DT]
下周一上午9点  →  2026-03-09 09:00  [DT]
3天后晚上8点半  →  2026-03-07 20:30  [DT]
半小时后  →  2026-03-04 10:30  [DT]
月底  →  2026-03-31 09:00  [D]
下周五  →  2026-03-13 09:00  [D]
```

方括号里的 `D` / `T` 标记哪些成分来自原文、哪些是默认补齐（默认时刻 09:00）。

## 作为库使用

```python
from datetime import datetime
from cn_date import parse, parse_dt

parse_dt("明天下午3点", now=datetime(2026, 3, 4, 10, 0))
# datetime(2026, 3, 5, 15, 0)

r = parse("3天后晚上8点半", now=datetime(2026, 3, 4, 10, 0))
r.dt          # datetime(2026, 3, 7, 20, 30)
r.has_time    # True —— 「晚上8点半」是显式给出的

parse_dt("随便说说")   # None
```

## 设计取舍

- **段词表驱动**：凌晨 / 中午 / 下午 / 晚上的语义集中一张表，规则可读可测
- **「下周X」按完整周计算**：从下一个周一起算，不受「今天是不是周日」影响；本周已过的星期自动顺延
- **小时级偏移精确推移**：`2小时后` 从 now 加 2 小时（而非落在默认 9 点），天数级偏移保持默认时刻
- **月份钳制**：`_add_months` 处理月末溢出（31 号 + 1 月 → 2 月 28/29 日）
- **严格数字边界**：先校验原始小时，再应用段词；时刻与日号不会从多位数字尾部截取匹配
- **UTF-8 CLI**：Windows 默认编码下也稳定输出中文帮助、解析结果与错误信息

## 运行测试

```bash
python -m unittest discover -s tests
# Ran 24 tests ... OK
```

CI 会构建 wheel/sdist 并运行 `twine check`，再从仓库外目录安装真实 wheel，执行入口冒烟与全部测试；覆盖 Ubuntu/Windows/macOS × Python 3.8/3.9/3.11/3.13，共 13 个作业。

## 项目结构

```
cn-date/
├── LICENSE
├── CHANGELOG.md
├── MANIFEST.in
├── cn_date/
├── tests/
│   ├── smoke_installed.py
│   ├── test_cli.py
│   └── test_parse.py
├── .github/workflows/ci.yml
├── pyproject.toml
└── README.md
```

## License

MIT
