import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import pandas as pd
from sklearn.linear_model import LinearRegression
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.widgets import Cursor
import webbrowser
from matplotlib.ticker import MaxNLocator

# Цветовая палитра
BACKGROUND_COLOR = "#eaf4fb"
BUTTON_COLOR = "#a3c9f1"
HIGHLIGHT_COLOR = "#6fa8dc"
FONT = ("Helvetica", 12)
ACCENT_COLOR = "#3d85c6"


# Подключение к базе данных
def get_cities():
    conn = sqlite3.connect("real_estate.db")
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT city FROM prices ORDER BY city")
    cities = [row[0] for row in cursor.fetchall()]
    conn.close()
    return cities


def get_city_data(city):
    conn = sqlite3.connect("real_estate.db")
    query = "SELECT year, average_price, description, wiki_link FROM prices WHERE city = ? ORDER BY year"
    df = pd.read_sql_query(query, conn, params=(city,))
    conn.close()
    return df


def get_city_info(city):
    conn = sqlite3.connect("real_estate.db")
    cursor = conn.cursor()
    cursor.execute("SELECT description, wiki_link FROM prices WHERE city = ? LIMIT 1", (city,))
    city_info = cursor.fetchone()
    conn.close()
    return city_info if city_info else ("Описание отсутствует", "")


def add_city_to_db(city, prices, description, wiki_link):
    conn = sqlite3.connect("real_estate.db")
    cursor = conn.cursor()
    for year, price in prices:
        cursor.execute("""
            INSERT INTO prices (city, year, average_price, description, wiki_link)
            VALUES (?, ?, ?, ?, ?)
        """, (city, year, price, description, wiki_link))
    conn.commit()
    conn.close()
    messagebox.showinfo("Успех", f"Город {city} успешно добавлен в базу данных.")


def open_wiki(url):
    if url:
        webbrowser.open(url)
    else:
        messagebox.showwarning("Ошибка", "Ссылка на Википедию отсутствует.")


# Построение основного графика с прогнозами
def plot_forecast(city):
    try:
        # Очищаем предыдущий график перед созданием нового
        for widget in frame_graph.winfo_children():
            if isinstance(widget, FigureCanvasTkAgg):
                widget.get_tk_widget().destroy()
            elif widget not in [description_label, link_button, show_bar_chart_button, control_frame, button_frame]:
                widget.destroy()

        df = get_city_data(city)
        if df.empty:
            messagebox.showerror("Ошибка", f"Нет данных для города {city}")
            return

        X = df["year"].values.reshape(-1, 1)
        y = df["average_price"].values

        model = LinearRegression()
        model.fit(X, y)

        optimistic_model = LinearRegression()
        optimistic_model.fit(X, y * 1.15)

        pessimistic_model = LinearRegression()
        pessimistic_model.fit(X, y * 0.85)

        year_to_predict = np.array([[2025]])
        predicted_price = model.predict(year_to_predict)
        optimistic_price = optimistic_model.predict(year_to_predict)
        pessimistic_price = pessimistic_model.predict(year_to_predict)

        fig, ax = plt.subplots(figsize=(8, 6), dpi=100)
        ax.plot(df["year"], y, marker='o', color=ACCENT_COLOR, label="Исторические данные")
        ax.plot(df["year"], model.predict(X), linestyle='--', color='green', label="Базовый тренд")
        ax.plot(df["year"], optimistic_model.predict(X), linestyle=':', color='blue',
                label="Оптимистичный прогноз (+15%)")
        ax.plot(df["year"], pessimistic_model.predict(X), linestyle=':', color='red',
                label="Пессимистичный прогноз (-15%)")

        ax.scatter(2025, predicted_price, color='green', label=f"Прогноз 2025: {predicted_price[0]:.0f} ₽/м²")
        ax.scatter(2025, optimistic_price, color='blue', label=f"Оптим. 2025: {optimistic_price[0]:.0f} ₽/м²")
        ax.scatter(2025, pessimistic_price, color='red', label=f"Песс. 2025: {pessimistic_price[0]:.0f} ₽/м²")

        ax.set_title(f"Динамика цен в {city} с прогнозом", fontsize=14)
        ax.set_xlabel("Год", fontsize=12)
        ax.set_ylabel("Цена, ₽/м²", fontsize=12)
        ax.grid(True)
        ax.legend()
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))

        canvas = FigureCanvasTkAgg(fig, master=frame_graph)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        description, wiki_url = get_city_info(city)
        description_label.config(text=description)
        if wiki_url:
            link_button.config(state="normal", command=lambda: open_wiki(wiki_url))
        else:
            link_button.config(state="disabled")

        show_bar_chart_button.config(state="normal", command=lambda: show_bar_chart(city))

    except Exception as e:
        messagebox.showerror("Ошибка", f"Произошла ошибка: {str(e)}")


# Функция для отображения столбчатой диаграммы
def show_bar_chart(city):
    try:
        df = get_city_data(city)
        if df.empty:
            messagebox.showerror("Ошибка", f"Нет данных для города {city}")
            return

        fig, ax = plt.subplots(figsize=(8, 6), dpi=100)
        bars = ax.bar(df["year"], df["average_price"], color=ACCENT_COLOR)

        ax.set_title(f"Цены за м² в {city} по годам", fontsize=14)
        ax.set_xlabel("Год", fontsize=12)
        ax.set_ylabel("Цена, ₽/м²", fontsize=12)
        ax.grid(True, axis='y')
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))

        # Добавляем подсказки
        def hover(event):
            if event.inaxes == ax:
                for bar in bars:
                    if bar.contains(event)[0]:
                        year = int(bar.get_x() + bar.get_width() / 2)
                        price = bar.get_height()
                        ax.set_title(f"{city}: {year} год - {price:.0f} ₽/м²", fontsize=14)
                        fig.canvas.draw_idle()
                        break

        fig.canvas.mpl_connect("motion_notify_event", hover)

        # Создаем новое окно для диаграммы
        chart_window = tk.Toplevel(root)
        chart_window.title(f"Диаграмма цен - {city}")
        chart_window.geometry("800x600")

        canvas = FigureCanvasTkAgg(fig, master=chart_window)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Кнопка закрытия
        close_button = tk.Button(chart_window, text="Закрыть", command=chart_window.destroy,
                                 bg=BUTTON_COLOR, font=FONT)
        close_button.pack(pady=10)

    except Exception as e:
        messagebox.showerror("Ошибка", f"Произошла ошибка: {str(e)}")


# Обработка выбора города
def on_city_select(event):
    try:
        selected_index = city_listbox.curselection()
        if not selected_index:
            return
        selected = city_listbox.get(selected_index)
        plot_forecast(selected)
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось загрузить данные: {str(e)}")


# Поиск города по вводу
def filter_cities(event):
    search_term = city_search_var.get().lower()
    filtered = [c for c in all_cities if search_term in c.lower()]
    city_listbox.delete(0, tk.END)
    for city in filtered:
        city_listbox.insert(tk.END, city)


# Функция для добавления города
def add_city():
    add_city_window = tk.Toplevel(root)
    add_city_window.title("Добавить новый город")
    add_city_window.geometry("500x650")
    add_city_window.configure(bg=BACKGROUND_COLOR)
    add_city_window.resizable(False, False)

    # Стилизованный заголовок
    header = tk.Frame(add_city_window, bg=HIGHLIGHT_COLOR)
    header.pack(fill=tk.X)
    tk.Label(header, text="Добавление нового города", bg=HIGHLIGHT_COLOR,
             fg="white", font=("Helvetica", 14, "bold")).pack(pady=10)

    # Основной контейнер
    container = tk.Frame(add_city_window, bg=BACKGROUND_COLOR)
    container.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)

    def create_entry_row(parent, label_text):
        frame = tk.Frame(parent, bg=BACKGROUND_COLOR)
        frame.pack(fill=tk.X, pady=5)
        tk.Label(frame, text=label_text, bg=BACKGROUND_COLOR, font=FONT, width=25, anchor="w").pack(side=tk.LEFT)
        entry = ttk.Entry(frame, font=FONT)
        entry.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        return entry

    # Поля ввода
    city_entry = create_entry_row(container, "Название города:")

    price_2020_entry = create_entry_row(container, "Цена за м² в 2020:")
    price_2021_entry = create_entry_row(container, "Цена за м² в 2021:")
    price_2022_entry = create_entry_row(container, "Цена за м² в 2022:")
    price_2023_entry = create_entry_row(container, "Цена за м² в 2023:")
    price_2024_entry = create_entry_row(container, "Цена за м² в 2024:")

    # Описание
    tk.Label(container, text="Описание города:", bg=BACKGROUND_COLOR, font=FONT, anchor="w").pack(fill=tk.X, pady=5)
    description_text = tk.Text(container, height=5, font=FONT)
    description_text.pack(fill=tk.X, pady=5)

    # Ссылка на Википедию
    wiki_entry = create_entry_row(container, "Ссылка на Википедию:")

    # Кнопки
    button_frame = tk.Frame(container, bg=BACKGROUND_COLOR)
    button_frame.pack(fill=tk.X, pady=20)

    def save_city():
        try:
            city = city_entry.get()
            if not city:
                raise ValueError("Название города не может быть пустым")

            prices = [
                (2020, float(price_2020_entry.get())),
                (2021, float(price_2021_entry.get())),
                (2022, float(price_2022_entry.get())),
                (2023, float(price_2023_entry.get())),
                (2024, float(price_2024_entry.get()))
            ]

            description = description_text.get("1.0", tk.END).strip()
            wiki_link = wiki_entry.get()

            add_city_to_db(city, prices, description, wiki_link)
            add_city_window.destroy()
            update_city_list()

        except ValueError as e:
            messagebox.showerror("Ошибка", f"Проверьте введенные данные:\n{str(e)}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при сохранении: {str(e)}")

    tk.Button(button_frame, text="Сохранить", command=save_city,
              bg=HIGHLIGHT_COLOR, fg="white", font=FONT, width=15).pack(side=tk.RIGHT, padx=5)

    tk.Button(button_frame, text="Отмена", command=add_city_window.destroy,
              bg=BUTTON_COLOR, font=FONT, width=15).pack(side=tk.RIGHT)


def update_city_list():
    global all_cities
    all_cities = get_cities()
    city_listbox.delete(0, tk.END)
    for city in all_cities:
        city_listbox.insert(tk.END, city)


# --- Создание основного интерфейса ---
root = tk.Tk()
root.title("Прогноз цен на недвижимость в городах России")
root.configure(bg=BACKGROUND_COLOR)
root.geometry("1000x750")

# Стилизация
style = ttk.Style()
style.configure("TFrame", background=BACKGROUND_COLOR)
style.configure("TLabel", background=BACKGROUND_COLOR, font=FONT)
style.configure("TEntry", font=FONT)

# Левый фрейм: выбор города
frame_left = tk.Frame(root, bg=BACKGROUND_COLOR)
frame_left.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

tk.Label(frame_left, text="Выберите город:", bg=BACKGROUND_COLOR, font=FONT).pack(anchor="w")

city_search_var = tk.StringVar()
city_search_entry = ttk.Entry(frame_left, textvariable=city_search_var)
city_search_entry.pack(fill=tk.X, pady=5)
city_search_entry.bind("<KeyRelease>", filter_cities)

city_listbox = tk.Listbox(frame_left, height=30, exportselection=False, font=FONT,
                          selectbackground=HIGHLIGHT_COLOR)
city_listbox.pack(fill=tk.BOTH, expand=True)
city_listbox.bind("<ButtonRelease-1>", on_city_select)

add_city_button = tk.Button(frame_left, text="Добавить город", bg=HIGHLIGHT_COLOR,
                            fg="white", font=FONT, command=add_city)
add_city_button.pack(fill=tk.X, pady=10)

# Правый фрейм: график
frame_graph = tk.Frame(root, bg=BACKGROUND_COLOR)
frame_graph.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

# Элементы управления графиком
control_frame = tk.Frame(frame_graph, bg=BACKGROUND_COLOR)
control_frame.pack(fill=tk.X)

description_label = tk.Label(frame_graph, text="Выберите город для отображения данных",
                             bg=BACKGROUND_COLOR, font=FONT, wraplength=800, justify=tk.LEFT)
description_label.pack(pady=10)

button_frame = tk.Frame(frame_graph, bg=BACKGROUND_COLOR)
button_frame.pack(fill=tk.X)

link_button = tk.Button(button_frame, text="Перейти на Википедию", bg=BUTTON_COLOR,
                        font=FONT, state="disabled")
link_button.pack(side=tk.LEFT, padx=5)

show_bar_chart_button = tk.Button(button_frame, text="Показать диаграмму", bg=BUTTON_COLOR,
                                  font=FONT, state="disabled")
show_bar_chart_button.pack(side=tk.LEFT, padx=5)

# Загрузка данных
all_cities = get_cities()
update_city_list()

root.mainloop()