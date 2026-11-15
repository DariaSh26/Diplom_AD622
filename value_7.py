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

df_orders_clean = df_orders[df_orders['payment_status'] == 'paid'].copy()

# Формирование когорт (Standard vs Promo 1 руб.)
cohort_map = {
    'standard': 'Standard (Тариф 399 ₽)',
    'promo_1rub': 'Promo-driven (Акция 1 ₽)'
}
df_users['cohort'] = df_users['experiment_group'].map(cohort_map)

# Пользователи с первичной оплатой (initial) и перешедшие на 1-е продление (renewal_1)
initial_users = df_orders_clean[df_orders_clean['payment_type'] == 'initial'][['user_id']].drop_duplicates()
renewal_users = df_orders_clean[df_orders_clean['payment_type'] == 'renewal_1'][['user_id']].drop_duplicates()
renewal_users['returned'] = 1

df_analysis = pd.merge(initial_users, df_users[['user_id', 'cohort']], on='user_id', how='left')
df_analysis = pd.merge(df_analysis, renewal_users, on='user_id', how='left')
df_analysis['returned'] = df_analysis['returned'].fillna(0)

# Расчет долей удержания и Z-статистики
cohort_stats = df_analysis.groupby('cohort').agg(
    total_users=('user_id', 'count'),
    returned_users=('returned', 'sum')
).reset_index()

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

print("--- Результаты z-теста для долей ---")
print(f"Доля удержания Standard: {p_standard * 100:.1f}%")
print(f"Доля удержания Promo: {p_promo * 100:.1f}%")
print(f"Z-статистика: {z_stat:.4f}")
print(f"p-value: {p_value:.5f}")

# Построение графика нормального распределения с критической зоной
sns.set_theme(style="white")
fig, ax = plt.subplots(figsize=(9, 5), dpi=100)
fig.patch.set_facecolor('#f8f9fa')

x = np.linspace(-4, 4, 500)
y = (1 / np.sqrt(2 * np.pi)) * np.exp(-x ** 2 / 2)

ax.plot(x, y, color="#082F6B", linewidth=2.5, label="Стандартное нормальное распределение")

z_critical = 1.645
ax.fill_between(x, y, where=(x >= z_critical), color="#ffcdd2", alpha=0.8, label="Критическая зона (alpha = 0.05)")

ax.axvline(z_stat, color="#FF5500", linestyle="--", linewidth=2.5)
ax.text(
    z_stat - 0.15, 0.22,
    f"Наша Z-статистика\n= {z_stat:.2f}\n(p-value = {p_value:.3f})",
    color="#FF5500", weight="bold", ha="right", fontsize=10, va="bottom",
    bbox=dict(boxstyle='round,pad=0.3', fc='white', edgecolor='#FF5500', alpha=0.9, lw=1)
)

ax.set_title("Результат статистического Z-теста для долей удержания", fontsize=14, weight="bold", pad=20, color="#212121")
ax.set_xlabel("Z-значение", fontsize=11)
ax.set_ylabel("Плотность вероятности", fontsize=11)
ax.set_ylim(0, 0.45)
ax.legend(loc="upper left", frameon=True, facecolor="white")

sns.despine()
plt.tight_layout()
plt.show()
