import pandas as pd
import numpy as np
import math
import matplotlib.pyplot as plt
import seaborn as sns

df_users = pd.read_csv("users.csv")
df_orders = pd.read_csv("orders.csv")
df_events = pd.read_csv("events.csv")

df_users['reg_date'] = pd.to_datetime(df_users['reg_date'])
df_orders['order_date'] = pd.to_datetime(df_orders['order_date'])
df_events['timestamp'] = pd.to_datetime(df_events['timestamp'])

# Фильтр успешных оплат
df_orders_clean = df_orders[df_orders['payment_status'] == 'paid'].copy()

# Формирование когорт на основе группы эксперимента (Standard vs Promo 1 руб.)
cohort_map = {
    'standard': 'Standard (Тариф 399 ₽)',
    'promo_1rub': 'Promo-driven (Акция 1 ₽)'
}
df_users['cohort'] = df_users['experiment_group'].map(cohort_map)

# Отбор пользователей, которые оформили первичную подписку
initial_users = df_orders_clean[df_orders_clean['payment_type'] == 'initial'][['user_id']].drop_duplicates()

# Отбор пользователей, которые продлили подписку на 2-й месяц
renewal_users = df_orders_clean[df_orders_clean['payment_type'] == 'renewal_1'][['user_id']].drop_duplicates()
renewal_users['returned'] = 1

# Объединяем данные по всем подписчикам обеих когорт
df_analysis = pd.merge(initial_users, df_users[['user_id', 'cohort']], on='user_id', how='left')
df_analysis = pd.merge(df_analysis, renewal_users, on='user_id', how='left')
df_analysis['returned'] = df_analysis['returned'].fillna(0)

# Расчет метрик
cohort_stats = df_analysis.groupby('cohort').agg(
    total_users=('user_id', 'count'),
    returned_users=('returned', 'sum')
).reset_index()

cohort_stats['Retention_Rate_%'] = (cohort_stats['returned_users'] / cohort_stats['total_users']) * 100
cohort_stats['Churn_Rate_%'] = ((cohort_stats['total_users'] - cohort_stats['returned_users']) / cohort_stats['total_users']) * 100

print("--- Сравнительный анализ когорт (Переход на 1-е продление за 399 ₽) ---")
print(cohort_stats.to_string(index=False))

# Z-тест для проверки гипотезы об оттоке
n_standard = cohort_stats.loc[cohort_stats['cohort'] == 'Standard (Тариф 399 ₽)', 'total_users'].values[0]
x_standard = cohort_stats.loc[cohort_stats['cohort'] == 'Standard (Тариф 399 ₽)', 'returned_users'].values[0]

n_promo = cohort_stats.loc[cohort_stats['cohort'] == 'Promo-driven (Акция 1 ₽)', 'total_users'].values[0]
x_promo = cohort_stats.loc[cohort_stats['cohort'] == 'Promo-driven (Акция 1 ₽)', 'returned_users'].values[0]

p_standard = x_standard / n_standard
p_promo = x_promo / n_promo

p_pooled = (x_standard + x_promo) / (n_standard + n_promo)
se = np.sqrt(p_pooled * (1 - p_pooled) * (1 / n_standard + 1 / n_promo))

z_stat = (p_standard - p_promo) / se


p_value = 1 - (0.5 * (1 + math.erf(z_stat / np.sqrt(2))))

print("\n--- Результаты z-теста для долей ---")
print(f"Доля удержания Standard (399 ₽): {p_standard * 100:.1f}% ({int(x_standard)} из {n_standard})")
print(f"Доля удержания Promo (1 ₽): {p_promo * 100:.1f}% ({int(x_promo)} из {n_promo})")
print(f"Z-статистика: {z_stat:.4f}")
print(f"p-value: {p_value:.5f}")

alpha = 0.05
if p_value < alpha:
    print(f"Результат: Отклоняем H0 на уровне значимости {alpha}. Промо-когорта удерживается статистически значимо хуже.")
else:
    print("Результат: Не удалось отклонить H0. Разница в удержании статистически не значима.")

# Построение стековой столбчатой диаграммы
cohort_names = ['Standard\n(Тариф 399 ₽)', 'Promo-driven\n(Акция 1 ₽)']
retention_rate = [p_standard * 100, p_promo * 100]
churn_rates = [100 - (p_standard * 100), 100 - (p_promo * 100)]

sns.set_theme(style="white")
fig, ax = plt.subplots(figsize=(8, 6), dpi=100)
fig.patch.set_facecolor('#f8f9fa')

ax.bar(cohort_names, retention_rate, label='Retention Rate (Продлили за 399 ₽)', color='#FF5500', width=0.4, edgecolor='black', linewidth=0.6)
ax.bar(cohort_names, churn_rates, bottom=retention_rate, label='Churn Rate (Отток после 1-го мес.)', color='#c62828', width=0.4, alpha=0.85, edgecolor='black', linewidth=0.6)

for i in range(len(cohort_names)):
    ax.text(i, retention_rate[i] / 2, f"{retention_rate[i]:.1f}%", ha='center', va='center', color='white', weight='bold', fontsize=11)
    ax.text(i, retention_rate[i] + churn_rates[i] / 2, f"{churn_rates[i]:.1f}%", ha='center', va='center', color='white', weight='bold', fontsize=11)

ax.set_title("Структура когорт после 1-го месяца: Удержание vs Отток", fontsize=14, weight='bold', pad=20, color='#212121')
ax.set_ylabel("Процент подписчиков, %", fontsize=12)
ax.set_ylim(0, 118)
ax.legend(loc='upper right', frameon=True, facecolor='white')
sns.despine()

plt.tight_layout()
plt.show()
