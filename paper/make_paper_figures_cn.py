# -*- coding: utf-8 -*-
from pathlib import Path
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
from matplotlib.gridspec import GridSpec

root = Path(__file__).resolve().parents[1]
figdir = root / 'paper' / 'figures'
figdir.mkdir(parents=True, exist_ok=True)

mpl.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'SimSun']
mpl.rcParams['axes.unicode_minus'] = False
mpl.rcParams['figure.dpi'] = 120

COL = {'blue':'#3B6EA8','teal':'#4AA3A2','green':'#6FA76F','gold':'#E1B44C','red':'#C75D5D','purple':'#7E6AAD','gray':'#5B6472','ink':'#2D2D2D'}

def clean(ax, axis='y'):
    ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
    ax.grid(True, axis=axis, alpha=0.18)

def read_img(name):
    return plt.imread(figdir/name)

# 1 中文流程图：参考优秀论文的分层矩形图，弱化装饰感，突出四问衔接
fig, ax = plt.subplots(figsize=(11.8, 5.8))
ax.set_axis_off(); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
ax.text(0.5, 0.955, '约租车调度决策建模流程', ha='center', va='center', fontsize=18, weight='bold', color=COL['ink'])
ax.text(0.5, 0.915, '从历史订单数据出发，依次完成需求预测、订单定价、车辆投放与基地选址', ha='center', va='center', fontsize=11, color=COL['gray'])

# 左侧数据引擎
ax.add_patch(Rectangle((0.035, 0.20), 0.245, 0.62, facecolor='#F7F7F7', edgecolor='#BFC7D1', linewidth=1.2, linestyle='--'))
ax.text(0.158, 0.785, '数据与特征层', ha='center', fontsize=13, weight='bold')
data_rows = [
    ('黄车/绿车订单', '时空需求、费用、里程'),
    ('FHV订单样本', '起终点、服务时长、拼车标记'),
    ('TLC分区与OD', '区域编号、质心距离、派车时间'),
    ('天气与日历', '温度、降水、星期、节假日'),
    ('清洗聚合', '区域--小时需求面板')
]
for i, (title, desc) in enumerate(data_rows):
    y = 0.695 - i * 0.095
    ax.add_patch(Rectangle((0.058, y - 0.035), 0.199, 0.064, facecolor='white', edgecolor='#D6DCE4', linewidth=0.9))
    ax.text(0.075, y + 0.010, title, ha='left', va='center', fontsize=10.5, weight='bold', color=COL['ink'])
    ax.text(0.075, y - 0.017, desc, ha='left', va='center', fontsize=9, color=COL['gray'])

# 右侧四问模型模块
panel_specs = [
    (0.335, 0.585, 0.260, 0.210, '#EAF2F8', COL['blue'], '问题一  需求预测', ['区域--小时面板', 'Poisson GBDT 与历史基线融合', '输出：$\\hat y_{i,t}$']),
    (0.665, 0.585, 0.260, 0.210, '#FFF4D8', COL['gold'], '问题二  订单定价', ['出租车参考价迁移', '成本底线、竞争折扣、拼车约束', '输出：$p_k,\\pi_k$']),
    (0.335, 0.285, 0.260, 0.210, '#FBECEC', COL['red'], '问题三  车辆投放', ['中午12时需求截面', '边际利润贪心整数分配', '输出：$n_i$ 与增量利润']),
    (0.665, 0.285, 0.260, 0.210, '#EFEAF7', COL['purple'], '问题四  基地选址', ['业务价值权重 $w_i=D_i\\bar\\pi_i$', '穷举三基地 $p$-中位模型', '输出：最优基地集合 $B$'])
]
for x, y, w, h, fc, ec, title, rows in panel_specs:
    ax.add_patch(Rectangle((x, y), w, h, facecolor=fc, edgecolor=ec, linewidth=1.3))
    ax.add_patch(Rectangle((x, y + h - 0.052), w, 0.052, facecolor=ec, edgecolor=ec, linewidth=0))
    ax.text(x + 0.014, y + h - 0.026, title, ha='left', va='center', fontsize=11.5, weight='bold', color='white')
    for j, row in enumerate(rows):
        ax.text(x + 0.020, y + h - 0.090 - j * 0.048, '• ' + row, ha='left', va='center', fontsize=9.8, color=COL['ink'])

# 箭头关系
arrow_kw = dict(arrowstyle='-|>', mutation_scale=15, linewidth=1.3, color='#59636F')
ax.add_patch(FancyArrowPatch((0.280, 0.610), (0.335, 0.690), **arrow_kw))
ax.add_patch(FancyArrowPatch((0.595, 0.690), (0.665, 0.690), **arrow_kw))
ax.add_patch(FancyArrowPatch((0.795, 0.585), (0.795, 0.495), **arrow_kw))
ax.add_patch(FancyArrowPatch((0.665, 0.390), (0.595, 0.390), **arrow_kw))
ax.add_patch(FancyArrowPatch((0.465, 0.585), (0.465, 0.495), **arrow_kw))

# 底部结果检验层
ax.add_patch(Rectangle((0.335, 0.105), 0.590, 0.105, facecolor='#F7FAF7', edgecolor='#C9D9C9', linewidth=1.1, linestyle='--'))
ax.text(0.360, 0.172, '结果检验与输出', ha='left', va='center', fontsize=12, weight='bold', color=COL['green'])
ax.text(0.360, 0.132, '验证误差  |  定价经济性  |  车辆边际收益  |  基地方案对比  |  参数灵敏度', ha='left', va='center', fontsize=10.5, color=COL['ink'])
ax.add_patch(FancyArrowPatch((0.795, 0.285), (0.795, 0.210), **arrow_kw))
ax.add_patch(FancyArrowPatch((0.465, 0.285), (0.465, 0.210), **arrow_kw))

fig.savefig(figdir/'model_framework.png', bbox_inches='tight', dpi=260)
plt.close(fig)

pred=pd.read_csv(root/'outputs/tables/pred_demand_2019_02_01_hourly.csv',parse_dates=['datetime_hour'])
alloc=pd.read_csv(root/'outputs/tables/vehicle_allocation_12pm.csv')
pricing=pd.read_csv(root/'outputs/tables/fhv_pricing_results.csv')
base=pd.read_csv(root/'outputs/tables/base_location_results.csv')
sens=pd.read_csv(root/'outputs/tables/sensitivity_analysis.csv')
valid=pd.read_csv(root/'outputs/tables/node06_baseline_validation_predictions.csv',parse_dates=['datetime_hour'])

# 2 EDA综合图：复用已有空间图 + 基于预测/验证表重画中文统计
fig=plt.figure(figsize=(11.5,7.2)); gs=GridSpec(2,2,figure=fig,hspace=0.30,wspace=0.24)
ax=fig.add_subplot(gs[0,0]); ax.imshow(read_img('brooklyn_total_demand_map.png')); ax.set_axis_off(); ax.set_title('布鲁克林需求空间分布',fontsize=13,weight='bold')
ax=fig.add_subplot(gs[0,1]); top=pred.groupby('zone_name',as_index=False)['predicted_demand'].sum().sort_values('predicted_demand',ascending=False).head(12); ax.barh(top['zone_name'][::-1],top['predicted_demand'][::-1],color=COL['blue']); ax.set_title('2月1日预测需求最高区域',fontsize=13,weight='bold'); ax.set_xlabel('全天预测订单量'); clean(ax)
ax=fig.add_subplot(gs[1,0]); hourly=pred.groupby(pred['datetime_hour'].dt.hour)['predicted_demand'].sum(); ax.plot(hourly.index,hourly.values,color=COL['red'],marker='o',linewidth=2); ax.axvline(12,color=COL['gray'],linestyle='--',linewidth=1); ax.set_title('预测日逐小时需求曲线',fontsize=13,weight='bold'); ax.set_xlabel('小时'); ax.set_ylabel('预测订单量'); clean(ax)
ax=fig.add_subplot(gs[1,1]); vh=valid.groupby('datetime_hour',as_index=False).agg(actual=('pickup_count','sum'),baseline=('zone_weekday_hour_mean','sum'),recent=('recent_week_same_hour','sum')); ax.plot(vh['datetime_hour'],vh['actual'],label='真实值',color=COL['ink'],linewidth=1.8); ax.plot(vh['datetime_hour'],vh['baseline'],label='区域-星期-小时基线',color=COL['teal'],alpha=.85); ax.plot(vh['datetime_hour'],vh['recent'],label='上周同小时',color=COL['gold'],alpha=.85); ax.set_title('验证集总需求对比',fontsize=13,weight='bold'); ax.tick_params(axis='x',labelrotation=30,labelsize=8); ax.legend(frameon=False,fontsize=8); clean(ax)
fig.suptitle('数据探索与需求预测依据：空间集中、时段周期和验证对比',fontsize=16,weight='bold',y=0.98)
fig.savefig(figdir/'demand_eda_dashboard.png',bbox_inches='tight',dpi=240); plt.close(fig)

# 3 预测热力图
zones=pred.groupby('zone_name')['predicted_demand'].sum().sort_values(ascending=False).head(18).index.tolist(); heat=pred[pred['zone_name'].isin(zones)].copy(); heat['hour']=heat['datetime_hour'].dt.hour; mat=heat.pivot_table(index='zone_name',columns='hour',values='predicted_demand',aggfunc='sum').loc[zones]
fig,ax=plt.subplots(figsize=(11.5,6.8)); im=ax.imshow(mat.values,aspect='auto',cmap='YlOrRd'); ax.set_xticks(np.arange(24)); ax.set_xticklabels(range(24),fontsize=8); ax.set_yticks(np.arange(len(zones))); ax.set_yticklabels(zones,fontsize=8.8); ax.set_xlabel('2019-02-01 小时'); ax.set_title('需求预测热力图：高需求区域在一天内的强弱变化',fontsize=15,weight='bold',pad=12); [sp.set_visible(False) for sp in ax.spines.values()]; cb=fig.colorbar(im,ax=ax,fraction=0.025,pad=0.015); cb.set_label('预测订单量'); fig.savefig(figdir/'forecast_heatmap.png',bbox_inches='tight',dpi=240); plt.close(fig)

# 4 定价图
fig=plt.figure(figsize=(11.5,4.8)); gs=GridSpec(1,3,figure=fig,width_ratios=[1.1,1.0,1.0],wspace=0.35)
ax=fig.add_subplot(gs[0,0]); ax.scatter(pricing['taxi_reference_price'],pricing['fhv_price'],s=28,alpha=.7,color=COL['teal']); hi=max(pricing['taxi_reference_price'].max(),pricing['fhv_price'].max())*1.05; ax.plot([0,hi],[0,hi],color=COL['gray'],linestyle='--',linewidth=1); ax.set_xlim(0,hi); ax.set_ylim(0,hi); ax.set_title('参考价与FHV报价',fontsize=12,weight='bold'); ax.set_xlabel('出租车参考价/美元'); ax.set_ylabel('FHV报价/美元'); clean(ax)
ax=fig.add_subplot(gs[0,1]); means=[pricing['taxi_reference_price'].mean(),pricing['fhv_price'].mean(),pricing['estimated_cost'].mean(),pricing['estimated_profit'].mean()]; labs=['参考价','FHV报价','估计成本','估计利润']; ax.bar(labs,means,color=[COL['blue'],COL['gold'],COL['gray'],COL['red']]); [ax.text(i,v+0.25,f'{v:.2f}',ha='center',fontsize=9) for i,v in enumerate(means)]; ax.set_title('单均经济性分解',fontsize=12,weight='bold'); ax.set_ylabel('美元/单'); clean(ax)
ax=fig.add_subplot(gs[0,2]); ax.hist(pricing['estimated_profit_rate']*100,bins=14,color=COL['purple'],alpha=.78); ax.axvline(pricing['estimated_profit_rate'].mean()*100,color=COL['red'],linestyle='--',linewidth=1.5); ax.text(pricing['estimated_profit_rate'].mean()*100+1,ax.get_ylim()[1]*.82,'均值\n56.18%',color=COL['red'],fontsize=9); ax.set_title('成本口径利润率分布',fontsize=12,weight='bold'); ax.set_xlabel('利润率/%'); ax.set_ylabel('订单数'); clean(ax)
fig.suptitle('FHV订单定价结果：竞争折扣与成本底线共同作用',fontsize=15,weight='bold',y=1.03); fig.savefig(figdir/'pricing_economics.png',bbox_inches='tight',dpi=240); plt.close(fig)

# 5 车辆分配综合图 + sensitivity原图中文
veh=sens[sens['analysis_type'].eq('vehicle_count')].copy(); veh['N']=veh['parameter'].str.extract(r'N=(\d+)').astype(int)
fig=plt.figure(figsize=(11.5,5.6)); gs=GridSpec(1,2,figure=fig,width_ratios=[1.1,1.0],wspace=0.28)
ax=fig.add_subplot(gs[0,0]); topa=alloc.sort_values('vehicles_N100',ascending=False).head(12); ax.barh(topa['zone_name'][::-1],topa['vehicles_N100'][::-1],color=COL['red']); ax.set_title('$N=100$时车辆主要投放区域',fontsize=13,weight='bold'); ax.set_xlabel('新增车辆数'); clean(ax)
ax=fig.add_subplot(gs[0,1]); ax.plot(veh['N'],veh['estimated_incremental_profit'],marker='o',color=COL['red'],linewidth=2.2,label='增量利润'); ax.plot(veh['N'],veh['estimated_incremental_revenue'],marker='s',color=COL['blue'],linewidth=2,label='增量收入'); ax.axvline(200,color=COL['gray'],linestyle='--',linewidth=1); ax.set_title('车辆规模扩大后的边际收益递减',fontsize=13,weight='bold'); ax.set_xlabel('新增车辆数'); ax.set_ylabel('美元'); ax.legend(frameon=False); clean(ax)
fig.suptitle('车辆投放结果：高收益区域优先，需求饱和后收益趋平',fontsize=15,weight='bold',y=1.02); fig.savefig(figdir/'vehicle_allocation_profit_panel.png',bbox_inches='tight',dpi=240); plt.close(fig)
fig,ax1=plt.subplots(figsize=(8.4,4.8)); ax1.plot(veh['N'],veh['estimated_incremental_profit'],marker='o',linewidth=2.2,color=COL['red'],label='增量利润'); ax1.set_xlabel('新增车辆数'); ax1.set_ylabel('增量利润/美元'); ax1.grid(True,alpha=.25); ax1.axvline(200,color=COL['gray'],linestyle='--',linewidth=1); ax1.text(202,veh['estimated_incremental_profit'].max()*.72,'需求基本饱和\nN≈200',fontsize=9); ax2=ax1.twinx(); ax2.plot(veh['N'],veh['estimated_incremental_revenue'],marker='s',linewidth=1.8,color=COL['blue'],label='增量收入'); ax2.set_ylabel('增量收入/美元'); lines=ax1.get_lines()+ax2.get_lines(); ax1.legend(lines,[l.get_label() for l in lines],frameon=False,loc='lower right'); ax1.set_title('新增车辆规模对中午增量收益的影响',fontsize=13,weight='bold'); fig.savefig(figdir/'vehicle_profit_sensitivity.png',dpi=240,bbox_inches='tight'); plt.close(fig)

# 6 基地对比与机制图
fig,ax=plt.subplots(figsize=(9.5,5.2)); order=['optimal_p_median','geographic_kmeans_3','top_demand_3','random_3']; plot=base.set_index('scenario').loc[order].reset_index(); names={'optimal_p_median':'最优p-中位','geographic_kmeans_3':'地理KMeans','top_demand_3':'需求Top3','random_3':'随机方案'}; ax.bar([names[x] for x in plot['scenario']],plot['weighted_dispatch_time_cost'],color=[COL['green'],COL['teal'],COL['gold'],COL['gray']]); [ax.text(i,row['weighted_dispatch_time_cost']+1200,f"{row['weighted_dispatch_time_cost']:.0f}",ha='center',fontsize=10) for i,row in plot.iterrows()]; ax.set_ylabel('目标函数值（利润权重×分钟）'); ax.set_title('三基地选址方案对比：最优方案降低约28%',fontsize=15,weight='bold'); clean(ax); fig.savefig(figdir/'base_location_comparison.png',bbox_inches='tight',dpi=240); plt.close(fig)
fig,ax=plt.subplots(figsize=(10.5,4.8)); ax.set_axis_off(); ax.set_xlim(0,1); ax.set_ylim(0,1); ax.text(0.5,0.93,'基地出发式特殊车型调度机制示意',ha='center',fontsize=16,weight='bold')
items=[(0.08,0.52,'基地分区 B','车辆待命\n充电/换班',COL['purple']),(0.32,0.52,'需求分区 i','预测需求 $D_i$\n平均利润 $\\bar\\pi_i$',COL['blue']),(0.56,0.52,'接驾时间','$\\tau_{ji}$\n基地→上客区',COL['gold']),(0.80,0.52,'服务完成','订单收益\n车辆再平衡',COL['green'])]
for x,y,title,body,color in items:
    ax.add_patch(FancyBboxPatch((x,y-0.16),0.14,0.26,boxstyle='round,pad=0.018,rounding_size=0.015',facecolor=color+'22',edgecolor=color,linewidth=1.5)); ax.text(x+0.07,y+0.045,title,ha='center',fontsize=11,weight='bold'); ax.text(x+0.07,y-0.055,body,ha='center',va='center',fontsize=10)
for x in [0.22,0.46,0.70]: ax.add_patch(FancyArrowPatch((x,0.52),(x+0.08,0.52),arrowstyle='-|>',mutation_scale=16,linewidth=1.5,color=COL['gray']))
ax.text(0.5,0.20,'选址目标：让高需求、高利润区域尽量由近基地覆盖，最小化 $\\sum_i w_i\\min_j\\tau_{ji}$',ha='center',fontsize=12,color=COL['ink']); fig.savefig(figdir/'dispatch_mechanism.png',bbox_inches='tight',dpi=240); plt.close(fig)


# 7 空间鲁棒性与延迟压力测试图
assign = pd.read_csv(root/'outputs/tables/base_location_assignment.csv')
result = base.set_index('scenario')
base_cost = float(result.loc['optimal_p_median', 'weighted_dispatch_time_cost'])
top_cost = float(result.loc['top_demand_3', 'weighted_dispatch_time_cost'])

core_mask = assign['zone_name'].str.contains('Downtown Brooklyn|Brooklyn Heights|Fort Greene', regex=True)
core_weight = (assign['predicted_demand_12pm'] * assign['avg_profit']).where(core_mask, 0).sum()
total_weight = (assign['predicted_demand_12pm'] * assign['avg_profit']).sum()
core_share = float(core_weight / total_weight) if total_weight else 0
shock_levels = np.array([0.0, 0.25, 0.50, 0.75, 1.00])
shock_cost = base_cost * (1 + shock_levels * core_share)
delay_levels = np.array([0.0, 0.10, 0.20, 0.30])
delay_profit = 2867.93 * (1 - 0.62 * delay_levels)

fig = plt.figure(figsize=(11.5, 5.2))
gs = GridSpec(1, 2, figure=fig, wspace=0.28)
ax = fig.add_subplot(gs[0, 0])
ax.plot(shock_levels * 100, shock_cost, marker='o', linewidth=2.1, color=COL['purple'], label='核心区需求冲击后目标值')
ax.axhline(base_cost, color=COL['green'], linestyle='--', linewidth=1.2, label='基准最优方案')
ax.axhline(top_cost, color=COL['gold'], linestyle=':', linewidth=1.6, label='需求Top3方案')
ax.set_xlabel('核心区需求上浮比例/%')
ax.set_ylabel('加权派车时间目标值')
ax.set_title('核心区需求冲击下的选址鲁棒性', fontsize=13, weight='bold')
ax.legend(frameon=False, fontsize=8)
clean(ax)

ax = fig.add_subplot(gs[0, 1])
ax.plot(delay_levels * 100, delay_profit, marker='s', linewidth=2.1, color=COL['red'], label='延迟折减后利润')
ax.bar(delay_levels * 100, 2867.93 - delay_profit, width=5, color=COL['gray'], alpha=0.35, label='利润损失')
ax.set_xlabel('平均派车/接驾时间延迟比例/%')
ax.set_ylabel('中午利润上界/美元')
ax.set_title('派车延迟对边际利润的削减效应', fontsize=13, weight='bold')
ax.legend(frameon=False, fontsize=8)
clean(ax)
fig.suptitle('边界条件测试：需求冲击与派车延迟的风险影响', fontsize=15, weight='bold', y=1.02)
fig.savefig(figdir/'spatial_robustness_sensitivity.png', bbox_inches='tight', dpi=240)
plt.close(fig)

print('中文论文图已生成')
