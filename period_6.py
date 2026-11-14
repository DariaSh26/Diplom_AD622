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

df_events = df_events.merge(df_users[['user_id', 'experiment_group']], on='user_id', how='left')

group_map = {
    'standard': '1. Стандартный тариф (399 ₽)',
    'promo_1rub': '2. Промо-акция (1 ₽)'
}
df_events['group'] = df_events['experiment_group'].map(group_map)

funnel = df_events.groupby(['group', 'event_type'])['user_id'].nunique().unstack(fill_value=0).reset_index()

funnel['CR_to_checkout'] = funnel['checkout_start'] / funnel['offer_view'] * 100
funnel['CR_checkout_to_buy'] = funnel['payment_success'] / funnel['checkout_start'] * 100
funnel['CR_total'] = funnel['payment_success'] / funnel['offer_view'] * 100

funnel_melted = pd.melt(funnel, id_vars=['group'], value_vars=['CR_to_checkout', 'CR_checkout_to_buy', 'CR_total'], var_name='Метрика конверсии', value_name='Процент, %')

metric_labels = {
    'CR_to_checkout': 'К оформлению (из просмотра)',
    'CR_checkout_to_buy': 'В оплату (из начала оформления)',
    'CR_total': 'Общая конверсия (CR)'
}

funnel_melted['Метрика конверсии'] = funnel_melted['Метрика конверсии'].map(metric_labels)

print(funnel_melted)

fig, ax = plt.subplots(figsize=(11, 6), dpi=100)

palette_kp = ['#082F6B', '#FF5500']

sns.barplot(data=funnel_melted, x='Метрика конверсии', y='Процент, %', hue='group', palette=palette_kp, edgecolor='black', linewidth=0.6)
for p in ax.patches:
    if p.get_height() > 0:
        ax.annotate(f"{p.get_height():.1f}%",(p.get_x() + p.get_width() / 2., p.get_height()), ha='center', va='bottom', fontsize=9, weight='bold', xytext=(0, 3),
                    textcoords='offset points')

ax.set_title("Эффективность продуктовой воронки по группам эксперимента", fontsize=14, weight='bold', pad=20, color='#212121')
ax.set_ylabel("Конверсия, %", fontsize=12)
ax.set_xlabel("")

ax.legend(title="Группа эксперимента", loc='upper left', frameon=True, facecolor='white')

sns.despine()
plt.tight_layout()
plt.show()
