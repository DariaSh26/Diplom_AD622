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

df_orders_clean = df_orders_clean.merge(df_users[['user_id', 'experiment_group']], on='user_id', how='left')
df_events = df_events.merge(df_users[['user_id', 'experiment_group']], on='user_id', how='left')

group_map = {
    'standard': '1. Стандартный тариф (399 ₽)',
    'promo_1rub': '2. Промо-акция (1 ₽)'
}
df_orders_clean['group'] = df_orders_clean['experiment_group'].map(group_map)
df_events['group'] = df_events['experiment_group'].map(group_map)

eda_finance = df_orders_clean.groupby('group').agg(
    clean_revenue=('amount_rub', 'sum'),       # Чистая выручка (сумма)
    orders_count=('order_id', 'count'),        # Общее количество успешных оплат
    aov=('amount_rub', 'mean'),                # Средний чек (AOV)
    unique_buyers=('user_id', 'nunique')       # Количество уникальных платящих
).reset_index()

print("--- Финансовые метрики по группам (Очищенные данные) ---")
print(eda_finance.to_string(index=False))

funnel = df_events.groupby(['group', 'event_type'])['user_id'].nunique().unstack(fill_value=0).reset_index()
funnel['CR_to_checkout'] = funnel['checkout_start'] / funnel['offer_view'] * 100
funnel['CR_checkout_to_buy'] = funnel['payment_success'] / funnel['checkout_start'] * 100
funnel['CR_total'] = funnel['payment_success'] / funnel['offer_view'] * 100

print("\n--- Конверсия воронки (CR) по группам ---")
print(funnel[['group', 'offer_view', 'checkout_start', 'payment_success', 'CR_total']].to_string(index=False))

rev_standard = eda_finance.loc[eda_finance['group'].str.contains('1.'), 'clean_revenue'].values[0]
rev_promo = eda_finance.loc[eda_finance['group'].str.contains('2.'), 'clean_revenue'].values[0]
aov_promo = eda_finance.loc[eda_finance['group'].str.contains('2.'), 'aov'].values[0]

print(f"\nСредний чек (AOV) в промо-группе: {aov_promo:.2f} ₽")

# Построение карточек KPI
sns.set_theme(style="white")
fig, axes = plt.subplots(1, 3, figsize=(10, 6), dpi=100)
fig.patch.set_facecolor('#f8f9fa')

selected_kpis = [
    {
        "title": "ВЫРУЧКА СТАНДАРТ\n(Тариф 399 ₽)",
        "value": f"{rev_standard:,.0f} ₽",
        "color": "#082F6B",
        "bg": "#e3f2fd"
    },
    {
        "title": "ВЫРУЧКА ПРОМО-АКЦИИ\n(Тариф 1 ₽ + продления)",
        "value": f"{rev_promo:,.0f} ₽",
        "color": "#FF5500",
        "bg": "#FFF0E6"
    },
    {
        "title": "СРЕДНИЙ ЧЕК (AOV)\nВ ПРОМО-ГРУППЕ",
        "value": f"{aov_promo:,.0f} ₽",
        "color": "#c62828",
        "bg": "#ffebee"
    }
]

for i, kpi in enumerate(selected_kpis):
    ax = axes[i]
    ax.set_facecolor(kpi['bg'])

    for spine in ax.spines.values():
        spine.set_color(kpi['color'])
        spine.set_linewidth(1.5)

    ax.text(0.5, 0.75, kpi['title'], ha='center', va='center', fontsize=10, fontweight='bold', color='#37474f')
    ax.text(0.5, 0.35, kpi['value'], ha='center', va='center', fontsize=24, fontweight='bold', color=kpi['color'])

    ax.set_xticks([])
    ax.set_yticks([])

plt.tight_layout(pad=2.0)
plt.show()
