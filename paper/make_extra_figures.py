from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

root = Path(r'D:\A比赛相关\数学建模\校赛\_external_Comp')
figdir = root / 'paper' / 'figures'
figdir.mkdir(parents=True, exist_ok=True)

plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False

# Figure 1: modeling framework
fig, ax = plt.subplots(figsize=(10, 3.8))
ax.set_axis_off()
boxes = [
    (0.04, 0.55, 'Data Cleaning\nTaxi/FHV + Weather', '#d8eef5'),
    (0.29, 0.55, 'Q1 Demand\nPoisson GBDT + Baseline', '#e4f3d2'),
    (0.54, 0.55, 'Q2 Pricing\nReference Fare + Cost Floor', '#fff0c7'),
    (0.29, 0.15, 'Q3 Allocation\nMarginal Profit Greedy', '#f4d7d7'),
    (0.54, 0.15, 'Q4 Base Location\nWeighted p-median', '#dedbf5'),
]
for x, y, text, color in boxes:
    patch = FancyBboxPatch((x, y), 0.19, 0.22, boxstyle='round,pad=0.025,rounding_size=0.02',
                           linewidth=1.4, edgecolor='#333333', facecolor=color)
    ax.add_patch(patch)
    ax.text(x+0.095, y+0.11, text, ha='center', va='center', fontsize=10, weight='bold')
for (x1,y1),(x2,y2) in [((0.23,0.66),(0.29,0.66)), ((0.48,0.66),(0.54,0.66)), ((0.635,0.55),(0.635,0.37)), ((0.54,0.26),(0.48,0.26)), ((0.385,0.55),(0.385,0.37))]:
    ax.add_patch(FancyArrowPatch((x1,y1),(x2,y2), arrowstyle='-|>', mutation_scale=14, linewidth=1.4, color='#333333'))
ax.text(0.76, 0.64, 'Decision outputs', fontsize=11, weight='bold')
ax.text(0.76, 0.52, 'Hourly demand forecast\nFHV order prices\nZone-level vehicle counts\nThree base zones', fontsize=10, va='top')
plt.tight_layout()
fig.savefig(figdir/'model_framework.png', dpi=220, bbox_inches='tight')
plt.close(fig)

# Figure 2: Q2 pricing comparison
pricing = pd.read_csv(root/'outputs'/'tables'/'fhv_pricing_results.csv')
fig, axes = plt.subplots(1,2,figsize=(10,4))
axes[0].hist(pricing['taxi_reference_price'], bins=16, alpha=0.65, label='Taxi reference', color='#4c78a8')
axes[0].hist(pricing['fhv_price'], bins=16, alpha=0.65, label='FHV price', color='#f58518')
axes[0].set_xlabel('Price / USD')
axes[0].set_ylabel('Orders')
axes[0].legend(frameon=False)
axes[0].set_title('Reference fare vs FHV price')
means = [pricing['taxi_reference_price'].mean(), pricing['fhv_price'].mean(), pricing['estimated_cost'].mean(), pricing['estimated_profit'].mean()]
labels = ['Taxi ref', 'FHV price', 'Cost', 'Profit']
axes[1].bar(labels, means, color=['#4c78a8','#f58518','#54a24b','#e45756'])
axes[1].set_ylabel('USD per order')
axes[1].set_title('Average order economics')
for i,v in enumerate(means): axes[1].text(i, v+0.25, f'{v:.2f}', ha='center', fontsize=9)
plt.tight_layout()
fig.savefig(figdir/'pricing_economics.png', dpi=220, bbox_inches='tight')
plt.close(fig)

# Figure 3: vehicle count sensitivity
sens = pd.read_csv(root/'outputs'/'tables'/'sensitivity_analysis.csv')
veh = sens[sens['analysis_type'].eq('vehicle_count')].copy()
veh['N'] = veh['parameter'].str.extract(r'N=(\d+)').astype(int)
fig, ax1 = plt.subplots(figsize=(8,4.6))
ax1.plot(veh['N'], veh['estimated_incremental_profit'], marker='o', linewidth=2.2, color='#e45756', label='Incremental profit')
ax1.set_xlabel('Added vehicles')
ax1.set_ylabel('Incremental profit / USD')
ax1.grid(True, alpha=0.25)
ax1.axvline(200, color='#666666', linestyle='--', linewidth=1)
ax1.text(202, veh['estimated_incremental_profit'].max()*0.72, 'Demand saturation\nN=200', fontsize=9)
ax2 = ax1.twinx()
ax2.plot(veh['N'], veh['estimated_incremental_revenue'], marker='s', linewidth=1.8, color='#4c78a8', label='Incremental revenue')
ax2.set_ylabel('Incremental revenue / USD')
lines = ax1.get_lines()+ax2.get_lines()
ax1.legend(lines, [l.get_label() for l in lines], frameon=False, loc='lower right')
plt.tight_layout()
fig.savefig(figdir/'vehicle_profit_sensitivity.png', dpi=220, bbox_inches='tight')
plt.close(fig)

print('created', figdir/'model_framework.png')
print('created', figdir/'pricing_economics.png')
print('created', figdir/'vehicle_profit_sensitivity.png')