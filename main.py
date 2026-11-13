import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

df_orders = pd.read_csv("orders.csv")    # Загрузка таблицы

df_orders_clean = df_orders[df_orders['payment_status'] == 'paid'].copy()   # Очистка данных: оставляем только оплаченные транзакции

total_revenue = df_orders['amount_rub'].sum()    # Расчет основных финансовых показателей
clean_revenue = df_orders_clean['amount_rub'].sum()
lost_revenue = total_revenue - clean_revenue

print(f"Общая сумма транзакций (включая ошибки оплаты): {total_revenue:,.2f} руб.")
print(f"Реальная очищенная выручка компании: {clean_revenue:,.2f} руб.")
print(f"Отсеяно из-за ошибок оплаты (failed): {lost_revenue:,.2f} руб.")

sns.set_theme(style="white")                    # Построение карточек KPI
fig, axes = plt.subplots(1, 3, figsize=(14, 3.5), dpi=100)
fig.patch.set_facecolor('#f8f9fa')

kpis = [
    {"title": "ОБЩИЙ ОБЪЕМ ТРАНЗАКЦИЙ\n(Грязные данные)","value": f"{total_revenue:,.0f} ₽", "color": "#082F6B", "bg": "#e3f2fd"},
    {"title": "РЕАЛЬНАЯ ВЫРУЧКА\n(Чистые деньги)", "value": f"{clean_revenue:,.0f} ₽", "color": "#FF5500", "bg": "#FFF0E6"},
    {"title": "ОТСЕЯНО ПРИ ОЧИСТКЕ\n(Ошибки оплаты / Failed)", "value": f"{lost_revenue:,.0f} ₽", "color": "#c62828", "bg": "#ffebee"},
]

for i, kpi in enumerate(kpis):
    ax = axes[i]
    ax.set_facecolor(kpi["bg"])

    for spine in ax.spines.values():
        spine.set_color(kpi["color"])
        spine.set_linewidth(1.5)

    ax.text(0.5, 0.75, kpi["title"], ha="center", va="center", fontsize=11, fontweight="bold", color="#37474f")
    ax.text(0.5, 0.35, kpi["value"], ha="center", va="center", fontsize=24, fontweight="bold", color=kpi["color"])

    ax.set_xticks([])
    ax.set_yticks([])


plt.tight_layout()
plt.show()





