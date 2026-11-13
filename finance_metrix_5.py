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
    clean_revenue = ('amount_rub', 'sum'),       # Чистая выручка (сумма)
    orders_count = ('order_id', 'count'),        # Общее количество транзакций
    aov = ('amount_rub', 'mean'),                # Средний чек
    unique_buyers = ('user_id', 'nunique')       # Количество уникальных платящих
).reset_index()

print("--- Финансовые метрики по группам (Очищенные данные) ---")
print(eda_finance.to_string(index=False))

# Конверсия воронки (CR) по этапам из events.csv
funnel = df_events.groupby(['group', 'event_type'])['user_id'].nunique().unstack(fill_value=0).reset_index()
funnel['CR_to_checkout'] = funnel['checkout_start'] / funnel['offer_view'] * 100
funnel['CR_checkout_to_buy'] = funnel['payment_success'] / funnel['checkout_start'] * 100
funnel['CR_total'] = funnel['payment_success'] / funnel['offer_view'] * 100

print("\n--- Конверсия воронки (CR) по группам ---")
print(funnel[['group', 'offer_view', 'checkout_start', 'payment_success', 'CR_total']].to_string(index=False))

# Построение графика
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
ax1.set_ylim(0, eda_finance['clean_revenue'].max() * 1.15)
ax1.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, loc: "{:,}".format(int(x))))

for p in ax1.patches:
    h = p.get_height()
    if h > 0:
        ax1.annotate(
            f"{h:,.0f} ₽", (p.get_x() + p.get_width() / 2., h),
            ha='center', va='bottom', fontsize=11, weight='bold', color='#082F6B',
            xytext=(0, 6), textcoords='offset points'
        )

ax1.set_title("Чистая выручка по группам эксперимента (Стандарт vs Промо 1 ₽)", fontsize=13, fontweight='bold', pad=15, color='#212121')
sns.despine(top=True, right=True)

plt.tight_layout()
plt.show()
