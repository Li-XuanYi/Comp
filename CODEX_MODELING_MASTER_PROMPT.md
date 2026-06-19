# Codex 节点式建模总控提示词：纽约约租车调度决策

> 适用对象：Codex / Claude Code / Cursor Agent / 其他本地代码智能体  
> 项目角色：数学建模工程执行助手  
> 目标：将“纽约约租车调度决策”赛题拆解为可执行、可检查、可回退的工程节点。  
> 核心机制：**每完成一个节点 → 运行检查 → 测试通过 → Git commit → Git tag 保存节点**。

---

## 0. 使用方式

将本文件放在项目根目录，例如：

```text
nyc_fhv_dispatch/
├── CODEX_MODELING_MASTER_PROMPT.md
├── AGENTS.md
├── README.md
├── configs/
├── data/
├── src/
├── scripts/
├── outputs/
└── tests/
```

每次让 Codex 工作时，不要说“把整个项目写完”，而是按节点推进：

```text
请读取 CODEX_MODELING_MASTER_PROMPT.md 和 AGENTS.md。
当前只执行 Node XX：<节点名称>。
严格按照该节点的输入、输出、检查标准完成。
检查通过后使用 Git 保存节点。
不要提前实现后续节点。
```

---

## 1. 角色设定

你是一个严谨的数学建模工程执行助手，负责协助完成“纽约约租车调度决策”问题的代码实现、结果生成、工程检查和版本管理。

必须遵守：

```text
1. 节点式推进，不要一次性写大脚本。
2. 每个节点必须有明确输入、输出和检查标准。
3. 检查失败不得提交 Git。
4. 检查通过后必须 commit，并打 tag。
5. 不得修改 data/raw/ 原始数据。
6. 不得提交大型原始数据、模型文件、缓存文件。
7. 主要逻辑写入 src/，不要堆在 notebook。
8. 所有路径从 configs/paths.yaml 读取，避免硬编码绝对路径。
9. 重要随机过程必须固定 random seed。
10. 输出结果必须可复现、可解释、可写入数学建模论文。
```

---

## 2. 赛题背景

本项目研究纽约布鲁克林区出租车与约租车调度决策。数据包括：

```text
附件1：2019 年 1 月黄色出租车行程数据，布鲁克林区出发
附件2：2019 年 1 月绿色出租车行程数据，布鲁克林区出发
附件3：2019 年 1 月约租车 FHV 行程数据，布鲁克林区出发
附件4：黄色出租车数据字典
附件5：绿色出租车数据字典
附件6：FHV 数据字典
附件7：纽约 TLC Taxi Zone 地图数据
```

四个建模任务：

```text
问题1：预测 2019-02-01 布鲁克林各编号区域逐小时出发订单量。
问题2：参考黄绿出租车费用规律，为附件3 FHV 订单定价。
问题3：基于需求预测和定价结果，设计 2019-02-01 中午 12 点车辆区域分配方案。
问题4：规划 3 个布鲁克林区内基地站点，兼顾派车时间、订单数量和价格影响。
```

---

## 3. 总体建模路线

```text
黄绿出租车历史订单
        ↓
数据清洗与布鲁克林区域筛选
        ↓
区域 × 小时需求面板
        ↓
天气、节假日、时间特征融合
        ↓
需求预测模型
        ↓
2019-02-01 逐小时区域订单量预测
        ↓
出租车参考费用模型
        ↓
FHV 约租车定价
        ↓
车辆区域分配优化
        ↓
3 个基地选址优化
        ↓
最终表格、图表、论文结果
```

推荐主模型：

```text
问题1：LightGBM Poisson / GBDT 需求预测 + 历史均值 baseline
问题2：出租车参考价模型 + FHV 成本估计 + 利润约束折中定价
问题3：整数规划或边际收益贪心车辆分配
问题4：加权 p-median / 三基地组合枚举选址
```

---

## 4. 工程目录结构

请在项目根目录建立如下结构：

```text
nyc_fhv_dispatch/
├── CODEX_MODELING_MASTER_PROMPT.md
├── README.md
├── AGENTS.md
├── Makefile
├── requirements.txt
├── .gitignore
├── configs/
│   ├── paths.yaml
│   ├── model.yaml
│   └── experiment.yaml
├── data/
│   ├── raw/
│   ├── interim/
│   ├── processed/
│   └── external/
├── src/
│   ├── __init__.py
│   ├── io_utils.py
│   ├── schema.py
│   ├── preprocessing.py
│   ├── feature_engineering.py
│   ├── weather_calendar.py
│   ├── demand_baseline.py
│   ├── demand_model.py
│   ├── pricing_model.py
│   ├── dispatch_optimization.py
│   ├── base_location.py
│   ├── visualization.py
│   └── metrics.py
├── scripts/
│   ├── run_node.py
│   ├── check_node.py
│   ├── make_all_outputs.py
│   └── export_submission.py
├── outputs/
│   ├── tables/
│   ├── figures/
│   ├── models/
│   ├── logs/
│   └── submission/
└── tests/
    ├── test_schema.py
    ├── test_preprocessing.py
    ├── test_demand_panel.py
    ├── test_pricing.py
    ├── test_dispatch.py
    └── test_base_location.py
```

---

## 5. Git 节点管理规则

### 5.1 基本规则

```text
1. 每个节点只实现当前节点内容。
2. 每个节点完成后必须运行：
   python scripts/check_node.py --node nodeXX
   pytest -q

3. 检查失败：
   - 不得 git commit
   - 阅读错误信息
   - 修复后重新检查

4. 检查通过：
   - git status
   - git diff --stat
   - git add 必要文件
   - git commit
   - git tag

5. 不提交 data/raw/。
6. 不提交 outputs/models/ 大模型文件。
7. 不提交 __pycache__/、缓存文件、临时文件。
```

### 5.2 标准保存命令

```bash
python scripts/check_node.py --node nodeXX
pytest -q

git status
git diff --stat

git add src/ scripts/ tests/ configs/ outputs/tables/ outputs/figures/ README.md AGENTS.md Makefile requirements.txt
git commit -m "nodeXX: <节点简短说明>"
git tag nodeXX-pass
```

### 5.3 回退命令

```bash
git log --oneline --decorate --graph --all
git checkout nodeXX-pass
```

如需从某节点新开分支：

```bash
git checkout -b fix-from-nodeXX nodeXX-pass
```

---

## 6. .gitignore 模板

```gitignore
data/raw/
data/interim/
data/processed/*.parquet
outputs/models/
outputs/logs/
__pycache__/
*.pyc
.ipynb_checkpoints/
.env
.DS_Store
*.tmp
*.bak
```

---

## 7. AGENTS.md 模板

```md
# AGENTS.md

## Project

This repository solves the NYC for-hire vehicle dispatch decision modeling problem.

## Language

Use Python 3.10+.

## Development Rule

Work node by node. Do not implement future nodes unless explicitly requested.

## Data Rule

Do not modify files under `data/raw/`.
Do not commit large raw data files.
All generated tables should go to `outputs/tables/`.
All figures should go to `outputs/figures/`.
All trained models should go to `outputs/models/`.

## Validation Rule

After finishing a node, run:

```bash
python scripts/check_node.py --node NODE_ID
pytest -q
```

Only if both checks pass:

```bash
git status
git add src/ scripts/ tests/ configs/ outputs/tables/ outputs/figures/ README.md AGENTS.md Makefile requirements.txt
git commit -m "nodeXX: short description"
git tag nodeXX-pass
```

If checks fail, fix the code and rerun checks. Do not commit failed work.

## Code Style

- Prefer Python modules over notebooks.
- Keep notebooks optional and exploratory.
- Use type hints where practical.
- Add docstrings for core functions.
- Keep random seeds fixed.
- Save every important intermediate result with clear filenames.
- Avoid hard-coded absolute paths.
- Read paths from `configs/paths.yaml`.

## Modeling Requirements

- Demand prediction must output hourly pickup counts for Brooklyn zones on 2019-02-01.
- Pricing must output a price for every row in the FHV file.
- Dispatch allocation must support configurable added vehicle numbers N.
- Base location must select exactly 3 Brooklyn zone IDs.
```

---

## 8. Makefile 模板

```makefile
.PHONY: check test node00 node01 node02 node03 node04 node05 node06 node07 node08 node09 node10 node11 node12

test:
	pytest -q

check:
	python scripts/check_node.py --node all
	pytest -q

node00:
	python scripts/run_node.py --node node00
	python scripts/check_node.py --node node00

node01:
	python scripts/run_node.py --node node01
	python scripts/check_node.py --node node01

node02:
	python scripts/run_node.py --node node02
	python scripts/check_node.py --node node02

node03:
	python scripts/run_node.py --node node03
	python scripts/check_node.py --node node03

node04:
	python scripts/run_node.py --node node04
	python scripts/check_node.py --node node04

node05:
	python scripts/run_node.py --node node05
	python scripts/check_node.py --node node05

node06:
	python scripts/run_node.py --node node06
	python scripts/check_node.py --node node06

node07:
	python scripts/run_node.py --node node07
	python scripts/check_node.py --node node07

node08:
	python scripts/run_node.py --node node08
	python scripts/check_node.py --node node08

node09:
	python scripts/run_node.py --node node09
	python scripts/check_node.py --node node09

node10:
	python scripts/run_node.py --node node10
	python scripts/check_node.py --node node10

node11:
	python scripts/run_node.py --node node11
	python scripts/check_node.py --node node11

node12:
	python scripts/make_all_outputs.py
	python scripts/check_node.py --node node12
```

---

## 9. 节点开发总览

| 节点 | 名称 | 核心输出 | Git tag |
|---|---|---|---|
| Node 00 | 项目初始化 | 项目骨架 | `node00-pass` |
| Node 01 | 数据审计 | 原始数据审计表 | `node01-pass` |
| Node 02 | 清洗与字段统一 | 清洗后的 Brooklyn 订单 | `node02-pass` |
| Node 03 | 需求面板 | 区域-小时订单面板 | `node03-pass` |
| Node 04 | 天气日历特征 | 建模特征表 | `node04-pass` |
| Node 05 | EDA 图表 | 论文图表 | `node05-pass` |
| Node 06 | 需求预测 baseline | baseline 指标 | `node06-pass` |
| Node 07 | 主需求预测模型 | 2019-02-01 预测表 | `node07-pass` |
| Node 08 | OD 距离时间估计 | OD 参考表 | `node08-pass` |
| Node 09 | FHV 定价 | FHV 定价结果 | `node09-pass` |
| Node 10 | 车辆分配 | 12 点车辆分布方案 | `node10-pass` |
| Node 11 | 三基地选址 | 3 个基地编号和覆盖图 | `node11-pass` |
| Node 12 | 最终提交导出 | 四问附件结果 | `node12-pass` |

---

# 10. 节点详细提示词

以下内容可以逐节点复制给 Codex。

---

## Node 00：项目初始化

```text
你现在执行 Node 00：项目初始化。

请完成：
1. 创建标准项目目录。
2. 创建 README.md。
3. 创建 AGENTS.md。
4. 创建 requirements.txt。
5. 创建 .gitignore。
6. 创建 configs/paths.yaml、configs/model.yaml、configs/experiment.yaml。
7. 创建 scripts/check_node.py 的基础框架。
8. 创建 scripts/run_node.py 的基础框架。
9. 创建 tests/test_schema.py 的基础 smoke test。
10. 确保 src/ 可以被 import。

禁止：
1. 不要读取或修改 data/raw/。
2. 不要实现后续节点。
3. 不要训练模型。

检查：
python scripts/check_node.py --node node00
pytest -q

检查通过后：
git add .
git commit -m "node00: initialize modeling project structure"
git tag node00-pass

最后汇报：
- 创建了哪些文件
- 检查是否通过
- commit hash
- tag 名称
```

---

## Node 01：原始数据读取与数据审计

关键输出：

```text
outputs/tables/node01_data_audit.csv
```

```text
你现在执行 Node 01：原始数据读取与数据审计。

任务：
1. 实现 src/io_utils.py。
2. 实现读取 yellow、green、fhv、taxi_zone_lookup、taxi_zones.shp 的函数。
3. 生成数据审计表，记录：
   - dataset
   - n_rows
   - n_cols
   - columns
   - missing_rate_summary
   - datetime_min
   - datetime_max
4. 输出到 outputs/tables/node01_data_audit.csv。
5. 添加或更新测试。

禁止：
1. 不要修改 data/raw/。
2. 不要执行清洗逻辑。
3. 不要实现后续节点。

检查：
python scripts/check_node.py --node node01
pytest -q

检查通过后：
git status
git diff --stat
git add src/ scripts/ tests/ configs/ outputs/tables/
git commit -m "node01: audit raw taxi and fhv datasets"
git tag node01-pass

最后汇报：
- 修改了哪些文件
- 生成了哪些结果
- 检查是否通过
- commit hash
```

---

## Node 02：字段统一与异常清洗

字段统一规则：

```text
yellow:
tpep_pickup_datetime -> pickup_datetime
tpep_dropoff_datetime -> dropoff_datetime

green:
lpep_pickup_datetime -> pickup_datetime
lpep_dropoff_datetime -> dropoff_datetime

fhv:
Pickup_datetime -> pickup_datetime
DropOff_datetime -> dropoff_datetime
```

清洗规则：

```text
1. pickup_datetime 必须在 2019-01-01 至 2019-01-31。
2. dropoff_datetime 必须晚于 pickup_datetime。
3. duration_min > 0。
4. duration_min <= 180。
5. PULocationID 属于 Brooklyn。
6. 对 yellow 和 green：
   - trip_distance > 0
   - total_amount > 0
   - fare_amount 合理
7. 对 FHV：
   - 保留可用于定价的 PU、DO、pickup、dropoff、base、SR_Flag。
```

关键输出：

```text
data/interim/yellow_clean.parquet
data/interim/green_clean.parquet
data/interim/fhv_clean.parquet
outputs/tables/node02_cleaning_report.csv
```

```text
你现在执行 Node 02：字段统一与异常清洗。

任务：
1. 实现 src/preprocessing.py。
2. 统一 yellow、green、fhv 字段名。
3. 根据 taxi_zone_lookup 筛选 Borough == Brooklyn 的 PULocationID。
4. 按清洗规则过滤异常记录。
5. 计算 duration_min。
6. 输出 clean parquet 文件和清洗报告。
7. 添加 tests/test_preprocessing.py。

禁止：
1. 不要修改 data/raw/。
2. 不要训练模型。
3. 不要实现需求预测。

检查：
python scripts/check_node.py --node node02
pytest -q

检查通过后：
git status
git diff --stat
git add src/ scripts/ tests/ configs/ outputs/tables/
git commit -m "node02: clean Brooklyn pickup records"
git tag node02-pass

最后汇报：
- 清洗前后行数
- 删除异常记录数量
- 输出文件
- 检查结果
- commit hash
```

---

## Node 03：逐小时需求面板

关键字段：

```text
zone_id
datetime_hour
date
hour
weekday
is_weekend
pickup_count
yellow_count
green_count
```

关键输出：

```text
data/processed/hourly_demand_panel.parquet
outputs/tables/node03_demand_panel_summary.csv
```

```text
你现在执行 Node 03：逐小时需求面板构建。

任务：
1. 读取 data/interim/yellow_clean.parquet 和 green_clean.parquet。
2. 按 PULocationID 和小时聚合订单数。
3. 构造完整面板：
   - 所有 Brooklyn zone
   - 2019-01-01 00:00:00 至 2019-01-31 23:00:00
   - 每小时一行
   - 无订单小时填 0
4. 输出 hourly_demand_panel.parquet。
5. 输出面板摘要表。
6. 添加 tests/test_demand_panel.py。

禁止：
1. 不要加入天气特征。
2. 不要训练模型。
3. 不要实现后续节点。

检查：
python scripts/check_node.py --node node03
pytest -q

检查通过后：
git status
git diff --stat
git add src/ scripts/ tests/ configs/ outputs/tables/
git commit -m "node03: build hourly Brooklyn demand panel"
git tag node03-pass

最后汇报：
- 面板行数
- zone 数量
- 时间范围
- 输出文件
- 检查结果
- commit hash
```

---

## Node 04：天气与日历特征

特征建议：

```text
temperature
precipitation
snow_indicator
wind_speed
visibility
is_weekend
is_holiday
is_morning_peak
is_evening_peak
is_night
hour_sin
hour_cos
weekday
month
day
```

关键输出：

```text
data/processed/hourly_features.parquet
outputs/tables/node04_feature_summary.csv
```

```text
你现在执行 Node 04：天气与日历特征融合。

任务：
1. 实现 src/weather_calendar.py。
2. 读取 hourly_demand_panel.parquet。
3. 读取或生成外部天气数据表。
4. 合并天气特征到逐小时面板。
5. 构造日历特征：
   - weekday
   - is_weekend
   - is_holiday
   - is_morning_peak
   - is_evening_peak
   - is_night
   - hour_sin
   - hour_cos
6. 输出 hourly_features.parquet。
7. 输出特征摘要表。
8. 添加测试，确保关键特征无严重缺失。

注意：
如果暂时没有外部天气数据，可以先建立可替换接口，并生成格式正确的 weather_hourly.csv 模板；
但必须在报告中记录该假设，后续应替换为真实天气数据。

禁止：
1. 不要训练预测模型。
2. 不要实现定价。
3. 不要实现调度优化。

检查：
python scripts/check_node.py --node node04
pytest -q

检查通过后：
git status
git diff --stat
git add src/ scripts/ tests/ configs/ outputs/tables/
git commit -m "node04: merge weather and calendar features"
git tag node04-pass

最后汇报：
- 合并后的特征数量
- 缺失率
- 输出文件
- 检查结果
- commit hash
```

---

## Node 05：探索性分析与论文图表

关键输出：

```text
outputs/figures/brooklyn_total_demand_map.png
outputs/figures/hourly_pattern.png
outputs/figures/weekday_weekend_pattern.png
outputs/figures/weather_demand_relation.png
outputs/figures/top20_zones.png
```

```text
你现在执行 Node 05：探索性分析与论文图表生成。

任务：
1. 实现 src/visualization.py。
2. 基于 hourly_features.parquet 生成论文可用图表。
3. 图表至少包括：
   - 布鲁克林各区总订单热力图
   - 24 小时平均订单曲线
   - 工作日与周末对比图
   - 天气变量与订单量关系图
   - Top 20 区域订单量柱状图
4. 输出对应 png 文件。
5. 输出一个 EDA 摘要表。

禁止：
1. 不要训练模型。
2. 不要实现后续问题。
3. 不要生成无意义空图。

检查：
python scripts/check_node.py --node node05
pytest -q

检查通过后：
git status
git diff --stat
git add src/ scripts/ tests/ configs/ outputs/tables/ outputs/figures/
git commit -m "node05: generate exploratory demand analysis figures"
git tag node05-pass

最后汇报：
- 生成了哪些图
- 图表对应论文用途
- 检查结果
- commit hash
```

---

## Node 06：需求预测 Baseline

Baseline 方案：

```text
Baseline A：zone × hour 历史均值
Baseline B：zone × weekday × hour 历史均值
Baseline C：最近一周同小时均值
```

数据划分：

```text
训练集：2019-01-01 至 2019-01-24
验证集：2019-01-25 至 2019-01-31
```

评价指标：

```text
MAE
RMSE
SMAPE
```

关键输出：

```text
outputs/tables/node06_baseline_metrics.csv
outputs/tables/node06_baseline_validation_predictions.csv
```

```text
你现在执行 Node 06：需求预测 Baseline。

任务：
1. 实现 src/demand_baseline.py。
2. 读取 hourly_features.parquet。
3. 按时间划分训练集和验证集。
4. 实现至少三个 baseline：
   - zone × hour 历史均值
   - zone × weekday × hour 历史均值
   - 最近一周同小时均值
5. 计算 MAE、RMSE、SMAPE。
6. 输出 baseline 指标表和验证集预测表。
7. 添加或更新 tests。

禁止：
1. 不要训练 LightGBM 主模型。
2. 不要预测 2019-02-01 最终结果。
3. 不要实现定价。

检查：
python scripts/check_node.py --node node06
pytest -q

检查通过后：
git status
git diff --stat
git add src/ scripts/ tests/ configs/ outputs/tables/
git commit -m "node06: build demand prediction baselines"
git tag node06-pass

最后汇报：
- 各 baseline 指标
- 最优 baseline
- 输出文件
- 检查结果
- commit hash
```

---

## Node 07：主需求预测模型

推荐模型：

```text
LightGBM Poisson Regression
或 XGBoost / HistGradientBoostingRegressor
```

若环境无法安装 LightGBM，可使用 scikit-learn 的 HistGradientBoostingRegressor 替代，并在报告中说明。

关键输出：

```text
outputs/tables/node07_model_metrics.csv
outputs/tables/pred_demand_2019_02_01_hourly.csv
outputs/figures/model_validation_compare.png
```

```text
你现在执行 Node 07：主需求预测模型。

任务：
1. 实现 src/demand_model.py。
2. 构造滞后特征和滚动特征。
3. 训练主需求预测模型。
4. 与 Node 06 baseline 对比。
5. 输出模型验证指标。
6. 预测 2019-02-01 00:00 至 23:00 每个 Brooklyn zone 的出发订单量。
7. 预测值必须非负。
8. 输出 pred_demand_2019_02_01_hourly.csv。
9. 生成验证集对比图。

禁止：
1. 不要实现 FHV 定价。
2. 不要实现车辆分配。
3. 不要实现基地选址。

检查：
python scripts/check_node.py --node node07
pytest -q

检查通过后：
git status
git diff --stat
git add src/ scripts/ tests/ configs/ outputs/tables/ outputs/figures/
git commit -m "node07: train main hourly demand prediction model"
git tag node07-pass

最后汇报：
- 模型类型
- 验证集指标
- 是否优于 baseline
- 2019-02-01 预测表维度
- 检查结果
- commit hash
```

---

## Node 08：OD 距离与时间估计

FHV 没有 `trip_distance`，因此需要从黄绿出租车历史 OD 中估计：

```text
estimated_distance(PU, DO) = median(trip_distance | PU, DO)
estimated_duration(PU, DO) = median(duration_min | PU, DO)
```

若同一 OD 样本不足，则用区域质心距离兜底：

```text
estimated_distance = alpha × centroid_distance
```

关键输出：

```text
outputs/tables/od_distance_duration_reference.csv
outputs/tables/fhv_with_estimated_distance.csv
```

```text
你现在执行 Node 08：OD 距离与时间估计。

任务：
1. 实现 OD 距离和时长参考表。
2. 从 yellow_clean 和 green_clean 计算相同 PU-DO 的距离中位数和时长中位数。
3. 对样本不足的 OD，使用 taxi_zones.shp 的区域质心距离兜底。
4. 为 fhv_clean 中每一行补齐：
   - estimated_distance
   - observed_duration_min
   - estimated_od_duration_min
5. 输出 OD 参考表和 FHV 补齐表。
6. 添加测试，确保 FHV 每一行都有距离估计。

禁止：
1. 不要训练价格模型。
2. 不要实现车辆分配。
3. 不要实现基地选址。

检查：
python scripts/check_node.py --node node08
pytest -q

检查通过后：
git status
git diff --stat
git add src/ scripts/ tests/ configs/ outputs/tables/
git commit -m "node08: estimate od distance and duration references"
git tag node08-pass

最后汇报：
- OD 参考表行数
- FHV 距离补齐成功率
- 使用历史 OD 和质心兜底的比例
- 检查结果
- commit hash
```

---

## Node 09：FHV 约租车定价模型

定价模型：

```text
第一层：出租车参考价模型
    taxi_reference_price = f(distance, duration, PU, DO, hour, weekday, weather)

第二层：FHV 成本模型
    cost = c0 + c_distance × distance + c_time × duration

第三层：价格优势与利润约束折中
    fhv_price = max(
        cost × (1 + minimum_profit_rate),
        taxi_reference_price × (1 - discount_rate)
    )
```

拼车订单可以进一步折扣：

```text
if SR_Flag == 1:
    fhv_price *= shared_ride_discount_factor
```

关键输出：

```text
outputs/tables/fhv_pricing_results.csv
outputs/tables/node09_pricing_model_summary.csv
```

```text
你现在执行 Node 09：FHV 约租车定价模型。

任务：
1. 实现 src/pricing_model.py。
2. 使用 yellow_clean 和 green_clean 训练出租车参考价模型。
3. 价格标签优先使用 total_amount，也可以同时记录 fare_amount 模型作为对照。
4. 特征至少包括：
   - estimated_distance / trip_distance
   - duration_min
   - PULocationID
   - DOLocationID
   - hour
   - weekday
   - is_weekend
   - weather features
5. 对 fhv_with_estimated_distance.csv 中每条 FHV 订单预测出租车参考价。
6. 构造 FHV 成本。
7. 使用价格优势与利润约束公式输出最终 fhv_price。
8. 输出 fhv_pricing_results.csv。
9. 确保结果行数与 FHV 输入一致。
10. 确保价格为正，无缺失。

禁止：
1. 不要实现车辆分配。
2. 不要实现基地选址。
3. 不要只用固定均价糊弄定价。

检查：
python scripts/check_node.py --node node09
pytest -q

检查通过后：
git status
git diff --stat
git add src/ scripts/ tests/ configs/ outputs/tables/
git commit -m "node09: price fhv trips using taxi reference model"
git tag node09-pass

最后汇报：
- 参考价模型类型
- 定价结果行数
- 平均价格
- 平均利润率估计
- 检查结果
- commit hash
```

---

## Node 10：车辆区域分配优化

题目没有明确新增车辆数，因此模型应支持参数化：

```text
N = 50
N = 100
N = 200
```

优化目标：

```text
maximize sum_z served_orders_z × profit_z
```

关键输出：

```text
outputs/tables/vehicle_allocation_12pm.csv
outputs/tables/node10_revenue_gain_summary.csv
outputs/figures/vehicle_allocation_map.png
```

```text
你现在执行 Node 10：车辆区域分配优化。

任务：
1. 实现 src/dispatch_optimization.py。
2. 读取 pred_demand_2019_02_01_hourly.csv。
3. 提取 2019-02-01 12:00-13:00 的区域预测需求。
4. 根据 fhv_pricing_results.csv 和历史订单估计区域平均利润。
5. 估计每个区域的平均服务周期 tau_z。
6. 对 N = 50、100、200 分别计算最优车辆分布。
7. 输出每个区域：
   - zone_id
   - zone_name
   - predicted_demand_12pm
   - avg_profit
   - avg_service_time
   - vehicles_N50
   - vehicles_N100
   - vehicles_N200
8. 估计营收增长和利润增长。
9. 生成车辆分布地图。

禁止：
1. 不要实现基地选址。
2. 不要把车辆简单按订单量比例分配，必须考虑利润和服务时长。
3. 不要输出负车辆数。

检查：
python scripts/check_node.py --node node10
pytest -q

检查通过后：
git status
git diff --stat
git add src/ scripts/ tests/ configs/ outputs/tables/ outputs/figures/
git commit -m "node10: optimize noon vehicle allocation"
git tag node10-pass

最后汇报：
- N=50/100/200 的总车辆数是否正确
- 预计新增营收
- 预计新增利润
- Top 投放区域
- 检查结果
- commit hash
```

---

## Node 11：三个基地选址

加权 p-median：

```text
minimize sum_z w_z × min_b T(b, z)
```

其中：

```text
w_z = predicted_demand_z × avg_profit_z
T(b, z) = 基地区域 b 到需求区域 z 的派车时间
```

约束：

```text
只选择 3 个基地
基地必须位于 Brooklyn zone
每个需求区域由最近或最低成本基地服务
```

关键输出：

```text
outputs/tables/base_location_results.csv
outputs/tables/base_location_assignment.csv
outputs/figures/base_location_map.png
```

```text
你现在执行 Node 11：三个基地选址。

任务：
1. 实现 src/base_location.py。
2. 构造 Brooklyn zone 之间的派车时间矩阵。
   - 优先使用历史 OD 中位时长。
   - 样本不足时使用质心距离 / 平均速度估计。
3. 构造区域权重：
   w_z = predicted_demand_z × avg_profit_z
4. 枚举所有三基地组合。
5. 对每个组合计算加权派车时间成本。
6. 选择成本最小的 3 个基地。
7. 输出：
   - base_location_results.csv
   - base_location_assignment.csv
   - base_location_map.png
8. 与简单基准方案对比：
   - 订单量最高 3 区域
   - 随机 3 区域
   - 地理 k-means 3 中心

禁止：
1. 不要只选订单量最高的三个区域。
2. 不要忽略派车时间。
3. 不要输出超过或少于 3 个基地。

检查：
python scripts/check_node.py --node node11
pytest -q

检查通过后：
git status
git diff --stat
git add src/ scripts/ tests/ configs/ outputs/tables/ outputs/figures/
git commit -m "node11: select three optimal Brooklyn base zones"
git tag node11-pass

最后汇报：
- 三个基地编号
- 对应区域名称
- 加权派车时间成本
- 相比基准方案提升
- 检查结果
- commit hash
```

---

## Node 12：最终提交附件导出

关键输出：

```text
outputs/submission/q1_hourly_prediction.xlsx
outputs/submission/q2_fhv_pricing.xlsx
outputs/submission/q3_vehicle_allocation.xlsx
outputs/submission/q4_base_location.xlsx
outputs/submission/model_summary.md
outputs/submission/figures/
```

```text
你现在执行 Node 12：最终提交附件导出。

任务：
1. 实现 scripts/make_all_outputs.py。
2. 实现 scripts/export_submission.py。
3. 汇总四问结果：
   - 问题1：2019-02-01 各区域逐小时订单量预测
   - 问题2：附件3 每条 FHV 订单定价
   - 问题3：2019-02-01 12 点车辆分配方案
   - 问题4：3 个基地选址方案
4. 导出 Excel 附件。
5. 汇总论文图表到 outputs/submission/figures/。
6. 生成 model_summary.md，说明每一问使用的模型、输入、输出、评价指标和主要结果。
7. 确保所有输出无关键缺失值。

禁止：
1. 不要重新训练全部模型，除非必要。
2. 不要覆盖原始数据。
3. 不要生成空表或空图。

检查：
python scripts/check_node.py --node node12
pytest -q

检查通过后：
git status
git diff --stat
git add src/ scripts/ tests/ configs/ outputs/tables/ outputs/figures/ outputs/submission/
git commit -m "node12: export final modeling outputs"
git tag node12-pass
git tag final-submission-v1

最后汇报：
- 四问附件文件路径
- 关键结果摘要
- 检查结果
- commit hash
- final tag 名称
```

---

## 11. check_node.py 检查逻辑建议

```text
node00:
- 目录结构存在
- README.md、AGENTS.md、Makefile 存在
- src 可 import

node01:
- node01_data_audit.csv 存在
- 包含 yellow、green、fhv 三类数据记录

node02:
- clean 文件存在
- duration_min > 0
- PULocationID 属于 Brooklyn
- 出租车金额、距离合理

node03:
- hourly_demand_panel.parquet 存在
- 每个 Brooklyn zone 每小时都有记录
- pickup_count 非负

node04:
- hourly_features.parquet 存在
- 时间、天气、日历特征完整

node05:
- 指定图表存在
- 文件大小 > 0

node06:
- baseline metrics 存在
- MAE、RMSE、SMAPE 非空

node07:
- 2019-02-01 预测表存在
- 覆盖 24 小时
- 覆盖所有 Brooklyn zones
- 预测值非负

node08:
- FHV 每行都有 estimated_distance
- estimated_distance > 0

node09:
- FHV 定价结果行数与 FHV 输入一致
- fhv_price > 0
- 无关键缺失值

node10:
- N=50/100/200 分配车辆总数正确
- 车辆数非负整数

node11:
- 恰好输出 3 个基地
- 基地属于 Brooklyn zone

node12:
- 四问提交文件存在
- 关键表无空值
```

---

## 12. 每个节点的论文记录要求

每个节点建议额外输出：

```text
outputs/logs/nodeXX_notes.md
```

内容包括：

```text
1. 本节点目的
2. 输入数据
3. 处理方法
4. 输出结果
5. 异常处理
6. 可写入论文的解释
7. 下一节点依赖
```

---

## 13. 最终论文结构建议

```text
一、问题重述
二、数据说明与预处理
三、问题一：布鲁克林区域订单分布与需求预测
    3.1 数据聚合
    3.2 时间、天气、节假日特征
    3.3 Baseline 模型
    3.4 主预测模型
    3.5 预测结果分析
四、问题二：约租车定价模型
    4.1 出租车费用规律分析
    4.2 OD 距离估计
    4.3 出租车参考价模型
    4.4 FHV 利润约束定价
    4.5 附件3 定价结果
五、问题三：车辆区域分配优化
    5.1 利润与服务能力建模
    5.2 优化模型
    5.3 车辆分布结果
    5.4 营收增长估计
六、问题四：三基地选址
    6.1 派车时间矩阵
    6.2 加权 p-median 模型
    6.3 基地选址结果
    6.4 方案优势分析
七、模型评价与敏感性分析
八、结论
```

---

## 14. 最终执行总控 Prompt

```text
请读取 CODEX_MODELING_MASTER_PROMPT.md 和 AGENTS.md。

我们现在采用节点式开发完成纽约约租车调度决策建模项目。

请从 Node 00 开始执行。

严格要求：
1. 每次只完成一个节点。
2. 当前节点检查通过后才能进入下一节点。
3. 每个节点完成后运行：
   python scripts/check_node.py --node nodeXX
   pytest -q
4. 检查通过后执行：
   git status
   git diff --stat
   git add src/ scripts/ tests/ configs/ outputs/tables/ outputs/figures/ README.md AGENTS.md Makefile requirements.txt
   git commit -m "nodeXX: <节点简述>"
   git tag nodeXX-pass
5. 检查失败不得 commit。
6. 不要提交 data/raw/。
7. 不要提前实现后续节点。
8. 每个节点最后汇报：
   - 修改文件
   - 生成文件
   - 检查结果
   - commit hash
   - tag 名称

现在开始 Node 00。
```

---

## 15. 单节点通用 Prompt 模板

```text
请读取 CODEX_MODELING_MASTER_PROMPT.md 和 AGENTS.md。

当前只执行 Node XX：<节点名称>。

任务范围：
<复制该节点的任务说明>

禁止事项：
1. 不要修改 data/raw/。
2. 不要实现未来节点。
3. 不要删除已有通过检查的文件。
4. 不要提交大文件。

完成标准：
1. 生成指定输出文件。
2. python scripts/check_node.py --node nodeXX 通过。
3. pytest -q 通过。
4. git diff 内容只包含本节点相关修改。

通过检查后执行：
git add src/ scripts/ tests/ configs/ outputs/tables/ outputs/figures/ README.md AGENTS.md Makefile requirements.txt
git commit -m "nodeXX: <简短说明>"
git tag nodeXX-pass

检查失败时：
不要 commit。
先修复失败原因，再重新运行检查。

最后给我输出：
- 修改了哪些文件
- 生成了哪些结果
- 检查是否通过
- commit hash
- tag 名称
```

---

## 16. 执行纪律

```text
宁可节点小一点，也不要一口气写完。
宁可多检查几次，也不要提交失败状态。
宁可模型简单可解释，也不要堆复杂但不可复现的深度模型。
宁可输出参数化方案，也不要在题目未给条件时拍脑袋固定假设。
```

本项目核心标准：

```text
预测可信
定价合理
分配可解释
选址可复现
论文能讲清楚
代码能跑通
结果能提交
```
