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
#
# print("--- Финансовые метрики по группам (Очищенные данные) ---")
# print(eda_finance.to_string(index=False))

funnel = df_events.groupby(['group', 'event_type'])['user_id'].nunique().unstack(fill_value=0).reset_index()
funnel['CR_to_checkout'] = funnel['checkout_start'] / funnel['offer_view'] * 100
funnel['CR_checkout_to_buy'] = funnel['payment_success'] / funnel['checkout_start'] * 100
funnel['CR_total'] = funnel['payment_success'] / funnel['offer_view'] * 100
#
# print("\n--- Конверсия воронки (CR) по группам ---")
# print(funnel[['group', 'offer_view', 'checkout_start', 'payment_success', 'CR_total']].to_string(index=False))