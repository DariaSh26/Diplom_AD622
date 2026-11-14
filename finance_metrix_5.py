import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


df_users = pd.read_csv("users.csv")
df_orders = pd.read_csv("orders.csv")
df_events = pd.read_csv("events.csv")

df_users['reg_date'] = pd.to_datetime(df_users['reg_date'])
df_orders['order_date'] = pd.to_datetime(df_orders['order_date'])
df_events['timestamp'] = pd.to_datetime(df_events['timestamp'])


df_orders_clean = df_orders[df_orders['payment_status'] == 'paid'].copy()

total_revenue = df_orders['amount_rub'].sum()
clean_revenue = df_orders_clean['amount_rub'].sum()
lost_revenue = total_revenue - clean_revenue


df_orders_clean = df_orders_clean.merge(df_users[['user_id', 'experiment_group']], on='user_id', how='left')
df_events = df_events.merge(df_users[['user_id', 'experiment_group']], on='user_id', how='left')

group_map = {
    'standard': '1. Стандартный тариф (399 ₽)',
    'promo_1rub': '2. Промо-акция (1 ₽)'
}

df_orders_clean['group'] = df_orders_clean['experiment_group'].map(group_map)
df_events['group'] = df_events['experiment_group'].map(group_map)

eda_finance = df_orders_clean.groupby('group').agg(
    clean_revenue=('amount_rub', 'sum'),       # Чистая выручка
    orders_count=('order_id', 'count'),        # Общее количество успешных оплат
    aov=('amount_rub', 'mean'),                # Средний чек
    unique_buyers=('user_id', 'nunique')       # Количество уникальных платящих
).reset_index()

print("--- Финансовые метрики по группам (Очищенные данные) ---")
print(eda_finance.to_string(index=False))

# Конверсия воронки (CR)
funnel = df_events.groupby(['group', 'event_type'])['user_id'].nunique().unstack(fill_value=0).reset_index()
funnel['CR_to_checkout'] = funnel['checkout_start'] / funnel['offer_view'] * 100
funnel['CR_checkout_to_buy'] = funnel['payment_success'] / funnel['checkout_start'] * 100
funnel['CR_total'] = funnel['payment_success'] / funnel['offer_view'] * 100

print("\n--- Конверсия воронки (CR) по группам ---")
print(funnel[['group', 'offer_view', 'checkout_start', 'payment_success', 'CR_total']].to_string(index=False))

# Построение комбинированного графика
sns.set_theme(style="white")
fig, ax1 = plt.subplots(figsize=(10, 6.5), dpi=100)
fig.patch.set_facecolor('#f8f9fa')


sns.barplot(
    data=eda_finance, x='group', y='clean_revenue', ax=ax1,
    color='#082F6B', alpha=0.9, width=0.45, edgecolor='#082F6B'
)
ax1.set_ylabel("Чистая выручка, руб.", color='#082F6B', fontsize=12, weight='bold', labelpad=15)
ax1.tick_params(axis='y', labelcolor='#082F6B', labelsize=11)
ax1.set_xlabel('')
ax1.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, loc: "{:,}".format(int(x))))

for p in ax1.patches:
    h = p.get_height()
    if h > 0:
        ax1.annotate(
            f"{h:,.0f} ₽", (p.get_x() + p.get_width() / 2., h),
            ha='center', va='bottom', fontsize=11, weight='bold', color='#082F6B',
            xytext=(0, 6), textcoords='offset points'
        )

ax2 = ax1.twinx()
sns.lineplot(
    data=eda_finance, x='group', y='orders_count', ax=ax2,
    color='#ff6d00', marker='o', linewidth=3.5, markersize=9, sort=False
)
ax2.set_ylabel("Количество успешных оплат", color='#e65100', fontsize=12, weight='bold', labelpad=15)
ax2.tick_params(axis='y', labelcolor='#e65100', labelsize=11)
ax2.grid(False)

for idx, row in eda_finance.iterrows():
    ax2.annotate(
        f"{int(row['orders_count'])} опл.", (row['group'], row['orders_count']),
        textcoords='offset points', xytext=(0, 12), ha='center', va='bottom',
        fontsize=11, weight='bold', color='#e65100',
        bbox=dict(boxstyle='round,pad=0.3', fc='white', edgecolor='#ff6d00', alpha=0.9, lw=1)
    )

ax1.set_ylim(0, eda_finance['clean_revenue'].max() * 1.9)
ax2.set_ylim(0, eda_finance['orders_count'].max() * 1.25)

plt.title("Сравнение чистой выручки и объема успешных оплат по группам", fontsize=14, weight='bold', pad=25, color='#212121')

sns.despine(ax=ax1, left=False, bottom=False, right=True)
sns.despine(ax=ax2, left=True, bottom=True, right=False)

plt.tight_layout()
plt.show()
