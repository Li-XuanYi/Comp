# B题论文写作过程日志

## 节点 0：建模结果修复基线
- 分支：`paper-prep-fixes`
- 提交：`140eb99 fix: align dispatch allocation and base selection`
- 检查：`node10/node11/node12` 通过，相关 pytest 通过。
- 关键修复：Q3 需求饱和后车辆闲置；Q4 采用基地到需求区的派车方向。

## 节点 1：LaTeX 工程搭建
- 参考工作区提供的 `cumcmthesis.cls` 模板和示例论文结构。
- 为提升编译稳定性，主文档采用 `ctexart` 自定义版式，保留 `paper/template/cumcmthesis.cls` 作为格式参考。
- 建立 `paper/main.tex`、`paper/figures/` 和本文档。
- 初版摘要写入模型主线和关键数值，等待编译检查和后续扩写。
## 节点 2：论文完整初稿
- 完成内容：问题重述、总体思路、模型假设、符号说明、数据预处理、四问模型、灵敏度分析、模型评价和结论。
- 写作依据：题面、本地附件、`paper-prep-fixes` 分支输出表、子 agent 审阅建议，以及工作区 LaTeX 模板的国赛式结构。
- 自评检查：
  - 正文按“预测需求 -> 制定价格 -> 车辆分配 -> 基地选址”的闭环决策链组织。
  - Q3 已写明 N=200 时 176 辆分配、24 辆备用，避免旧版硬分配问题。
  - Q4 已使用 `33;111;222` 新选址结果，并强调派车方向为基地到需求区。
  - 文本中无占位语、待办标记和旧版基地编号残留。
  - 正文引用的关键图片均已复制到 `paper/figures/`。
- 本轮修改：补齐图片资源；Q1 指标表保留指标完整的基线与融合模型，Poisson GBDT 单模型 MAE 改在正文说明，避免表格出现缺失项。
- 编译状态：当前机器未检测到 TeX Live/MacTeX；bundled Tectonic 可执行但需联网下载基础 bundle，因证书/网络错误失败。源码已按 XeLaTeX/ctex 编写，等待可用中文 LaTeX 环境编译。
## 节点 3：论文逻辑审阅与定价约束修正
- 审阅来源：子 agent 对 `paper/main.tex` 进行只读审阅，重点指出拼车折扣下界、需求转化、利润率口径和灵敏度展示问题。
- 代码修正：`src/pricing_model.py` 与 `src/sensitivity_analysis.py` 中拼车折扣后的价格下界统一为 `cost * (1 + minimum_profit_rate)`，不再允许低于最低利润底线。
- 结果刷新：基于已有 `fhv_pricing_results.csv` 重新计算 Q2 定价、Q3 车辆分配、Q4 选址权重与敏感性表；核心结果未发生数值变化，Q2 平均价格 15.96 美元、成本口径平均利润率 56.18%，Q3/Q4 表与修正前一致。
- 论文修订：补充需求转化系数 `rho`，说明当前 `rho=1` 为可争取需求上界；明确利润率为逐单 `(price-cost)/cost` 的样本均值；改写拼车定价公式；说明 Q3 静态调度为未扣接驾等待的理想上界；将 Q4 目标解释为业务价值加权派车时间而非美元成本；新增关键参数灵敏度表。
- 编译风险：本机仍缺少完整中文 LaTeX 环境；源码按 XeLaTeX/ctex 编写，可上传 Overleaf 或任一可用 TeX Live 环境编译。
## 节点 4：最终检查与交付打包
- 通过检查：`scripts/check_node.py --node node09/node10/node11/node12` 均通过；`pytest tests/test_dispatch.py tests/test_base_location.py tests/test_submission_export.py tests/test_sensitivity_analysis.py -q -p no:cacheprovider` 通过，6 项测试全部成功。
- 论文结构检查：`main.tex` 中 equation/table/figure/cases/subfigure 环境数量成对匹配；未发现 `TODO`、`待补充`、旧基地 `65;111;222` 或拼车旧下界表述。
- LaTeX 编译：本地 `compile_latex.py` 检测到项目要求 XeLaTeX，但当前环境没有 TeX Live/MacTeX，因此未生成 PDF。
- Overleaf 包：已生成 `paper/overleaf_upload.zip`，包含 `main.tex`、`figures/` 和 `template/`，上传 Overleaf 后请选择 XeLaTeX 编译。
## 节点 5：优秀论文风格评估与图表增强
- 评估结论：第一版结构完整、数值一致，但图表支撑不足，正文偏技术说明，缺少优秀数模论文常见的“总流程-分问题可视化-结果解释-敏感性支撑”层次。
- 新增图表：`model_framework.png`、`pricing_economics.png`、`vehicle_profit_sensitivity.png`，并把已有 `top20_zones.png`、`weekday_weekend_pattern.png`、`weather_demand_relation.png` 纳入正文。
- 写作增强：重写摘要，使其按“问题-方法-结果-价值”展开；在问题分析中加入闭环模型流程；在数据探索、定价和车辆分配部分增加图文互证。
- 检查：论文结构检查通过，figure/table/subfigure/equation/cases 环境成对匹配；所有图片引用存在；相关 pytest 通过 6 项。
- 交付：重新生成 `paper/overleaf_upload.zip`，需在 Overleaf 选择 XeLaTeX 重新编译新版 PDF。
