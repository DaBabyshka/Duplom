import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import pandas as pd
from sklearn.linear_model import LinearRegression
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.widgets import Cursor
import webbrowser
from matplotlib.ticker import MaxNLocator
import ast

# Обновленная цветовая палитра
BACKGROUND_COLOR = "#f0f8ff"  # Светло-голубой фон
BUTTON_COLOR = "#4a90e2"  # Яркий синий для основных кнопок
HIGHLIGHT_COLOR = "#3a7bd5"  # Темнее синий для hover-эффекта
DELETE_COLOR = "#e74c3c"  # Красный для кнопки удаления
DELETE_HIGHLIGHT = "#c0392b"  # Темнее красный для hover-эффекта
ACCENT_COLOR = "#3d85c6"  # Акцентный цвет для графиков
TEXT_COLOR = "#2c3e50"  # Темно-синий для текста
BUTTON_FRAME_COLOR = "#e1f0fa"  # Светлый фон для панели кнопок
BUTTON_BORDER_COLOR = "#2c3e50"  # Цвет контура кнопок

FONT = ("Segoe UI", 11)  # Более современный шрифт
FONT_BOLD = ("Segoe UI", 11, "bold")


# Стилизованная кнопка с закругленными углами и контуром
class ModernButton(tk.Button):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.default_bg = kwargs.get('bg', BUTTON_COLOR)
        self.hover_bg = kwargs.get('activebackground', HIGHLIGHT_COLOR)
        self.default_fg = kwargs.get('fg', 'white')
        self.active_fg = kwargs.get('activeforeground', 'white')

        self.config(
            relief=tk.FLAT,
            bd=0,
            padx=15,
            pady=6,
            font=FONT_BOLD,
            bg=self.default_bg,
            fg=self.default_fg,
            activebackground=self.hover_bg,
            activeforeground=self.active_fg,
            highlightbackground=BUTTON_BORDER_COLOR,
            highlightthickness=0,
            borderwidth=0
        )

        # Закругленные углы
        self.bind("<Configure>", self._configure_button)
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)

    def _configure_button(self, event=None):
        self.config(highlightthickness=0)
        self.update()
        # Создаем эффект закругленных углов
        self.config(borderwidth=0, highlightthickness=0)
        self['border'] = 0
        self['highlightthickness'] = 0

    def on_enter(self, e):
        self.config(bg=self.hover_bg)

    def on_leave(self, e):
        self.config(bg=self.default_bg)


# Стилизованная кнопка удаления
class DeleteButton(ModernButton):
    def __init__(self, master=None, **kwargs):
        kwargs['bg'] = DELETE_COLOR
        kwargs['activebackground'] = DELETE_HIGHLIGHT
        super().__init__(master, **kwargs)


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


def delete_city_from_db(city):
    try:
        conn = sqlite3.connect("real_estate.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM prices WHERE city = ?", (city,))
        conn.commit()
        conn.close()
        messagebox.showinfo("Успех", f"Город {city} успешно удален из базы данных.")
        return True
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось удалить город: {str(e)}")
        return False


def open_wiki(url):
    if url:
        webbrowser.open(url)
    else:
        messagebox.showwarning("Ошибка", "Ссылка на Википедию отсутствует.")


# Функция для загрузки данных из TXT файла
def load_from_txt():
    file_path = filedialog.askopenfilename(
        title="Выберите файл с данными",
        filetypes=(("Текстовые файлы", "*.txt"), ("Все файлы", "*.*"))
    )

    if not file_path:
        return

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()

            # Пытаемся преобразовать содержимое файла в список кортежей
            try:
                data = ast.literal_eval(content)
                if not isinstance(data, list):
                    raise ValueError("Файл должен содержать список кортежей")
            except (SyntaxError, ValueError) as e:
                messagebox.showerror("Ошибка", f"Неверный формат файла: {str(e)}")
                return

            conn = sqlite3.connect("real_estate.db")
            cursor = conn.cursor()

            added_cities = set()

            for record in data:
                if len(record) != 5:
                    messagebox.showerror("Ошибка",
                                         "Каждая запись должна содержать 5 элементов: город, год, цена, описание, ссылка")
                    conn.close()
                    return

                city, year, price, description, wiki_link = record
                cursor.execute("""
                    INSERT OR REPLACE INTO prices (city, year, average_price, description, wiki_link)
                    VALUES (?, ?, ?, ?, ?)
                """, (city, year, price, description, wiki_link))

                added_cities.add(city)

            conn.commit()
            conn.close()

            messagebox.showinfo("Успех", f"Данные для городов {', '.join(added_cities)} успешно загружены!")
            update_city_list()

    except Exception as e:
        messagebox.showerror("Ошибка", f"Произошла ошибка при загрузке файла: {str(e)}")


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
        delete_city_btn.config(state="normal", command=lambda: confirm_delete_city(city))

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
        fig.patch.set_facecolor(BACKGROUND_COLOR)
        ax.set_facecolor(BACKGROUND_COLOR)

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
        chart_window.configure(bg=BACKGROUND_COLOR)

        canvas = FigureCanvasTkAgg(fig, master=chart_window)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Стилизованная кнопка закрытия
        close_button = ModernButton(chart_window, text="Закрыть", command=chart_window.destroy)
        close_button.pack(pady=10)

    except Exception as e:
        messagebox.showerror("Ошибка", f"Произошла ошибка: {str(e)}")


# Подтверждение удаления города
def confirm_delete_city(city):
    if messagebox.askyesno("Подтверждение", f"Вы уверены, что хотите удалить город {city} из базы данных?"):
        if delete_city_from_db(city):
            update_city_list()
            # Очищаем график и информацию о городе
            for widget in frame_graph.winfo_children():
                if isinstance(widget, FigureCanvasTkAgg):
                    widget.get_tk_widget().destroy()
                elif widget not in [description_label, link_button, show_bar_chart_button, control_frame, button_frame]:
                    widget.destroy()

            description_label.config(text="Выберите город для отображения данных")
            link_button.config(state="disabled")
            show_bar_chart_button.config(state="disabled")
            delete_city_btn.config(state="disabled")


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
             fg="white", font=("Segoe UI", 14, "bold")).pack(pady=10)

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
    button_frame = tk.Frame(container, bg=BUTTON_FRAME_COLOR)
    button_frame.pack(fill=tk.X, pady=20, padx=5, ipady=10)

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

    save_btn = ModernButton(button_frame, text="Сохранить", command=save_city)
    save_btn.pack(side=tk.RIGHT, padx=10)

    cancel_btn = ModernButton(button_frame, text="Отмена", command=add_city_window.destroy, bg="#95a5a6")
    cancel_btn.pack(side=tk.RIGHT)


def update_city_list():
    global all_cities
    all_cities = get_cities()
    city_listbox.delete(0, tk.END)
    for city in all_cities:
        city_listbox.insert(tk.END, city)


# Функция для отображения справки
def show_help():
    help_window = tk.Toplevel(root)
    help_window.title("Справка по приложению")
    help_window.geometry("700x600")
    help_window.configure(bg=BACKGROUND_COLOR)
    help_window.resizable(False, False)

    # Создаем Notebook (вкладки)
    notebook = ttk.Notebook(help_window)
    notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # Вкладка о формате файла
    file_frame = tk.Frame(notebook, bg=BACKGROUND_COLOR)
    notebook.add(file_frame, text="Формат TXT файла")

    tk.Label(file_frame, text="Пример содержимого TXT файла:",
             bg=BACKGROUND_COLOR, font=FONT_BOLD, anchor="w").pack(fill=tk.X, pady=10, padx=10)

    example_text = """[
    ("Москва", 2020, 195000, "Столица России", "https://ru.wikipedia.org/wiki/Москва"),
    ("Москва", 2021, 210000, "Столица России", "https://ru.wikipedia.org/wiki/Москва"),
    ("Москва", 2022, 230000, "Столица России", "https://ru.wikipedia.org/wiki/Москва"),
    ("Санкт-Петербург", 2020, 120000, "Северная столица", "https://ru.wikipedia.org/wiki/Санкт-Петербург"),
    ("Санкт-Петербург", 2021, 125000, "Северная столица", "https://ru.wikipedia.org/wiki/Санкт-Петербург")
]"""

    text_widget = tk.Text(file_frame, height=15, width=80, font=("Consolas", 10), wrap=tk.WORD)
    text_widget.insert(tk.END, example_text)
    text_widget.config(state="disabled")
    text_widget.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

    tk.Label(file_frame, text="Файл должен содержать список кортежей, где каждый кортеж состоит из:",
             bg=BACKGROUND_COLOR, font=FONT, anchor="w").pack(fill=tk.X, padx=10)

    tk.Label(file_frame,
             text="1. Название города\n2. Год (2020-2024)\n3. Средняя цена за м²\n4. Описание города\n5. Ссылка на Википедию",
             bg=BACKGROUND_COLOR, font=FONT, anchor="w", justify=tk.LEFT).pack(fill=tk.X, padx=20, pady=5)

    # Вкладка о функционале
    func_frame = tk.Frame(notebook, bg=BACKGROUND_COLOR)
    notebook.add(func_frame, text="Функционал приложения")

    info_text = """Приложение для анализа цен на недвижимость в городах России:

Основные функции:
1. Просмотр динамики цен по годам
2. Прогноз цен на 2025 год (базовый, оптимистичный и пессимистичный)
3. Добавление новых городов в базу данных
4. Удаление городов из базы данных
5. Загрузка данных из текстового файла
6. Просмотр дополнительной информации о городах

График показывает:
- Исторические данные (точки с фактическими ценами)
- Базовый тренд (линейная регрессия)
- Оптимистичный прогноз (+15% к данным)
- Пессимистичный прогноз (-15% к данным)
- Прогнозируемые цены на 2025 год

Кнопки:
- 'Добавить город' - ручной ввод данных о новом городе
- 'Удалить город' - удаление выбранного города из базы
- 'Загрузить из TXT' - импорт данных из текстового файла
- 'Перейти на Википедию' - открытие страницы города
- 'Показать диаграмму' - отображение столбчатой диаграммы цен"""

    text_widget = tk.Text(func_frame, height=25, width=80, font=FONT, wrap=tk.WORD)
    text_widget.insert(tk.END, info_text)
    text_widget.config(state="disabled")
    text_widget.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    # Кнопка закрытия
    close_btn = ModernButton(help_window, text="Закрыть", command=help_window.destroy)
    close_btn.pack(pady=10)


# --- Создание основного интерфейса ---
root = tk.Tk()
root.title("Прогноз цен на недвижимость в городах России")
root.configure(bg=BACKGROUND_COLOR)
root.geometry("1000x750")

# Установка иконки (если есть)
try:
    root.iconbitmap("home_icon.ico")  # Можно добавить свою иконку
except:
    pass

# Стилизация
style = ttk.Style()
style.theme_use("clam")
style.configure("TFrame", background=BACKGROUND_COLOR)
style.configure("TLabel", background=BACKGROUND_COLOR, font=FONT, foreground=TEXT_COLOR)
style.configure("TEntry", font=FONT, fieldbackground="white")
style.configure("TButton", font=FONT_BOLD, padding=6)

# Левый фрейм: выбор города
frame_left = tk.Frame(root, bg=BUTTON_FRAME_COLOR, bd=2, relief=tk.RIDGE)
frame_left.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

tk.Label(frame_left, text="Выберите город:", bg=BUTTON_FRAME_COLOR,
         font=FONT_BOLD, fg=TEXT_COLOR).pack(anchor="w", pady=(5, 0))

city_search_var = tk.StringVar()
city_search_entry = ttk.Entry(frame_left, textvariable=city_search_var)
city_search_entry.pack(fill=tk.X, pady=5, padx=5)
city_search_entry.bind("<KeyRelease>", filter_cities)

city_listbox = tk.Listbox(frame_left, height=30, exportselection=False, font=FONT,
                          selectbackground=HIGHLIGHT_COLOR, selectforeground="white",
                          bd=0, highlightthickness=0)
city_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
city_listbox.bind("<ButtonRelease-1>", on_city_select)

button_frame_left = tk.Frame(frame_left, bg=BUTTON_FRAME_COLOR)
button_frame_left.pack(fill=tk.X, pady=(5, 10), padx=5)

add_city_btn = ModernButton(button_frame_left, text="Добавить город")
add_city_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
add_city_btn.config(command=add_city)

delete_city_btn = DeleteButton(button_frame_left, text="Удалить город")
delete_city_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
delete_city_btn.config(state="disabled")

# Кнопка загрузки из файла
load_txt_btn = ModernButton(button_frame_left, text="Загрузить из TXT", bg="#2ecc71", activebackground="#27ae60")
load_txt_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
load_txt_btn.config(command=load_from_txt)

# Кнопка справки
help_btn = ModernButton(button_frame_left, text="Справка", bg="#9b59b6", activebackground="#8e44ad")
help_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
help_btn.config(command=show_help)

# Правый фрейм: график
frame_graph = tk.Frame(root, bg=BACKGROUND_COLOR, bd=2, relief=tk.RIDGE)
frame_graph.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

# Элементы управления графиком
control_frame = tk.Frame(frame_graph, bg=BACKGROUND_COLOR)
control_frame.pack(fill=tk.X)

description_label = tk.Label(frame_graph, text="Выберите город для отображения данных",
                             bg=BACKGROUND_COLOR, font=FONT, wraplength=800,
                             justify=tk.LEFT, fg=TEXT_COLOR)
description_label.pack(pady=10)

button_frame = tk.Frame(frame_graph, bg=BUTTON_FRAME_COLOR)
button_frame.pack(fill=tk.X, pady=5, padx=5, ipady=5)

link_button = ModernButton(button_frame, text="Перейти на Википедию")
link_button.pack(side=tk.LEFT, padx=5)
link_button.config(state="disabled")

show_bar_chart_button = ModernButton(button_frame, text="Показать диаграмму")
show_bar_chart_button.pack(side=tk.LEFT, padx=5)
show_bar_chart_button.config(state="disabled")

# Загрузка данных
all_cities = get_cities()
update_city_list()

root.mainloop()