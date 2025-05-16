import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import pandas as pd
from sklearn.linear_model import LinearRegression
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import webbrowser
from matplotlib.ticker import MaxNLocator
import ast
import json
from tkinter import font as tkfont
import matplotlib.patches as mpatches
from matplotlib import animation
import time
from PIL import Image, ImageTk


# Цветовая палитра
class SmoothTheme:
    def __init__(self):
        self.colors = {
            "bg": "#2a2a2e",
            "panel": "#3a3a3f",
            "accent": "#5a7bb5",
            "text": "#e0e0e0",
            "text_secondary": "#b0b0b0",
            "entry_bg": "#4a4a4f",
            "border": "#5a5a5f",
            "graph_bg": "#2a2a2e",
            "graph_grid": "#4a4a4f",
            "button": "#4a4a4f",
            "button_hover": "#5a5a5f",
            "danger": "#9b4a4a",
            "success": "#4a9b6a",
            "highlight": "#3a4a6a",
            "tooltip_bg": "#3a3a3f",
            "tooltip_text": "#e0e0e0",
            "card_bg": "#3a3a3f",
            "card_border": "#5a5a5f"
        }


theme = SmoothTheme()

# Шрифты
FONT = ("Segoe UI", 10)
FONT_BOLD = ("Segoe UI", 10, "bold")
FONT_TITLE = ("Segoe UI", 12, "bold")
FONT_SMALL = ("Segoe UI", 9)
FONT_LARGE = ("Segoe UI", 14, "bold")


# Анимированная кнопка
class SmoothButton(tk.Canvas):
    def __init__(self, master=None, text="", command=None, width=120, height=36,
                 bg_color=theme.colors["button"], fg_color=theme.colors["text"],
                 hover_color=theme.colors["button_hover"], radius=6, font=FONT, **kwargs):
        super().__init__(master, width=width, height=height,
                         highlightthickness=0, bd=0, **kwargs)
        self.command = command
        self.bg_color = bg_color
        self.fg_color = fg_color
        self.hover_color = hover_color
        self.radius = radius
        self.text = text
        self.font = font
        self.after_id = None
        self.current_bg = bg_color

        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_click)

        self.draw_button()

    def draw_button(self):
        self.delete("all")
        self.create_rounded_rect(0, 0, self.winfo_reqwidth(), self.winfo_reqheight(),
                                 radius=self.radius, fill=self.current_bg, outline="")
        self.create_text(self.winfo_reqwidth() / 2, self.winfo_reqheight() / 2,
                         text=self.text, fill=self.fg_color, font=self.font)

    def create_rounded_rect(self, x1, y1, x2, y2, radius=10, **kwargs):
        points = [
            x1 + radius, y1,
            x2 - radius, y1,
            x2, y1,
            x2, y1 + radius,
            x2, y2 - radius,
            x2, y2,
            x2 - radius, y2,
            x1 + radius, y2,
            x1, y2,
            x1, y2 - radius,
            x1, y1 + radius,
            x1, y1
        ]
        return self.create_polygon(points, **kwargs, smooth=True)

    def animate_color(self, start_color, end_color, steps=10):
        if self.after_id:
            self.after_cancel(self.after_id)

        start_r = int(start_color[1:3], 16)
        start_g = int(start_color[3:5], 16)
        start_b = int(start_color[5:7], 16)

        end_r = int(end_color[1:3], 16)
        end_g = int(end_color[3:5], 16)
        end_b = int(end_color[5:7], 16)

        step_r = (end_r - start_r) / steps
        step_g = (end_g - start_g) / steps
        step_b = (end_b - start_b) / steps

        def update_step(step=0):
            if step <= steps:
                r = int(start_r + step * step_r)
                g = int(start_g + step * step_g)
                b = int(start_b + step * step_b)
                self.current_bg = f"#{r:02x}{g:02x}{b:02x}"
                self.draw_button()
                self.after_id = self.after(10, update_step, step + 1)

        update_step()

    def on_enter(self, event=None):
        self.animate_color(self.bg_color, self.hover_color)

    def on_leave(self, event=None):
        self.animate_color(self.current_bg, self.bg_color)

    def on_click(self, event=None):
        self.current_bg = self.hover_color
        self.draw_button()
        self.after(100, lambda: self.animate_color(self.hover_color, self.bg_color))
        if self.command:
            self.command()


# Карточка с информацией
class InfoCard(tk.Frame):
    def __init__(self, master=None, title="", value="", unit="", color=theme.colors["accent"], **kwargs):
        super().__init__(master, bg=theme.colors["card_bg"], bd=1,
                         relief=tk.RIDGE, highlightbackground=theme.colors["card_border"],
                         highlightthickness=1, **kwargs)

        self.title_label = tk.Label(self, text=title, bg=theme.colors["card_bg"],
                                    fg=theme.colors["text_secondary"], font=FONT_SMALL)
        self.title_label.pack(pady=(5, 0))

        self.value_label = tk.Label(self, text=value, bg=theme.colors["card_bg"],
                                    fg=color, font=FONT_LARGE)
        self.value_label.pack()

        if unit:
            self.unit_label = tk.Label(self, text=unit, bg=theme.colors["card_bg"],
                                       fg=theme.colors["text_secondary"], font=FONT_SMALL)
            self.unit_label.pack(pady=(0, 5))

    def update_value(self, new_value, new_unit=None):
        self.value_label.config(text=new_value)
        if new_unit and hasattr(self, 'unit_label'):
            self.unit_label.config(text=new_unit)


# Список городов с плавной прокруткой
class CityListbox(tk.Listbox):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.config(
            font=FONT,
            selectbackground=theme.colors["accent"],
            selectforeground="white",
            bd=0,
            highlightthickness=0,
            bg=theme.colors["panel"],
            fg=theme.colors["text"],
            activestyle="none"
        )


# Анимация загрузки
class LoadingAnimation(tk.Canvas):
    def __init__(self, master=None, size=50, color=theme.colors["accent"], **kwargs):
        super().__init__(master, width=size, height=size,
                         highlightthickness=0, bd=0, **kwargs)
        self.size = size
        self.color = color
        self.angle = 0
        self.animation_id = None
        self.start_animation()

    def start_animation(self):
        self.delete("all")
        self.angle = (self.angle + 10) % 360

        # Рисуем круговую анимацию
        self.create_arc(10, 10, self.size - 10, self.size - 10,
                        start=self.angle, extent=60,
                        style=tk.ARC, outline=self.color, width=3)

        self.animation_id = self.after(50, self.start_animation)

    def stop_animation(self):
        if self.animation_id:
            self.after_cancel(self.animation_id)
        self.delete("all")


# Функции для работы с базой данных
def create_database():
    conn = sqlite3.connect("real_estate.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prices (
            city TEXT,
            year INTEGER,
            average_price REAL,
            description TEXT,
            wiki_link TEXT,
            PRIMARY KEY (city, year)
        )
    """)
    conn.commit()
    conn.close()


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
            INSERT OR REPLACE INTO prices (city, year, average_price, description, wiki_link)
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


# Функции для работы с файлами
def load_from_txt():
    file_path = filedialog.askopenfilename(
        title="Выберите файл с данными",
        filetypes=(("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")))
    if not file_path:
        return

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
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


def export_to_txt():
    file_path = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Text files", "*.txt")],
        title="Сохранить как TXT")
    if not file_path:
        return
    try:
        conn = sqlite3.connect("real_estate.db")
        cursor = conn.cursor()
        cursor.execute("SELECT city, year, average_price, description, wiki_link FROM prices")
        data = cursor.fetchall()
        conn.close()
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(str(data))
        messagebox.showinfo("Успех", "Данные успешно выгружены в TXT")
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось сохранить файл: {str(e)}")


def export_to_json():
    file_path = filedialog.asksaveasfilename(
        defaultextension=".json",
        filetypes=[("JSON files", "*.json")],
        title="Сохранить как JSON")
    if not file_path:
        return
    try:
        conn = sqlite3.connect("real_estate.db")
        cursor = conn.cursor()
        cursor.execute("SELECT city, year, average_price, description, wiki_link FROM prices")
        data = cursor.fetchall()
        conn.close()
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        messagebox.showinfo("Успех", "Данные успешно выгружены в JSON")
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось сохранить файл: {str(e)}")


def load_from_json():
    file_path = filedialog.askopenfilename(
        title="Выберите JSON-файл",
        filetypes=[("JSON файлы", "*.json")])
    if not file_path:
        return
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise ValueError("Файл должен содержать список записей")
        conn = sqlite3.connect("real_estate.db")
        cursor = conn.cursor()
        added_cities = set()
        for record in data:
            if len(record) != 5:
                raise ValueError("Каждая запись должна содержать 5 элементов")
            city, year, price, description, wiki_link = record
            cursor.execute("""
                INSERT OR REPLACE INTO prices (city, year, average_price, description, wiki_link)
                VALUES (?, ?, ?, ?, ?)
            """, (city, year, price, description, wiki_link))
            added_cities.add(city)
        conn.commit()
        conn.close()
        update_city_list()
        messagebox.showinfo("Успех", f"Данные успешно загружены для городов: {', '.join(added_cities)}")
    except Exception as e:
        messagebox.showerror("Ошибка", f"Ошибка загрузки JSON: {str(e)}")


# Графики и прогнозы
def plot_forecast(city):
    try:
        # Очищаем предыдущий график
        for widget in frame_graph.winfo_children():
            widget.destroy()

        # Показываем анимацию загрузки
        loading = LoadingAnimation(frame_graph, size=80, color=theme.colors["accent"])
        loading.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        frame_graph.update()

        df = get_city_data(city)
        if df.empty:
            messagebox.showerror("Ошибка", f"Нет данных для города {city}")
            loading.stop_animation()
            loading.destroy()
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

        # Создаем фигуру
        fig = plt.figure(figsize=(8, 5), dpi=100, facecolor=theme.colors["graph_bg"])
        ax = fig.add_subplot(111, facecolor=theme.colors["graph_bg"])

        # Цвета для графиков
        colors = {
            "historical": theme.colors["accent"],
            "trend": "#6fa54a",
            "optimistic": "#a56f4a",
            "pessimistic": "#a54a6f"
        }

        # Информационное окно
        info_text = tk.StringVar()
        info_text.set("Наведите курсор на точки графика для информации")

        info_frame = tk.Frame(frame_graph, bg=theme.colors["tooltip_bg"], padx=10, pady=5)
        info_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        tk.Label(info_frame, textvariable=info_text, bg=theme.colors["tooltip_bg"],
                 fg=theme.colors["tooltip_text"], font=FONT_SMALL).pack()

        # Создаем карточки с информацией
        stats_frame = tk.Frame(frame_graph, bg=theme.colors["bg"])
        stats_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        # Карточка с текущей ценой
        last_price = y[-1]
        current_price_card = InfoCard(stats_frame, title="Текущая цена",
                                      value=f"{last_price:,.0f}", unit="₽/м²",
                                      color=theme.colors["accent"])
        current_price_card.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # Карточка с прогнозом
        forecast_card = InfoCard(stats_frame, title="Прогноз на 2025",
                                 value=f"{predicted_price[0]:,.0f}", unit="₽/м²",
                                 color=colors["trend"])
        forecast_card.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # Карточка с оптимистичным прогнозом
        optimistic_card = InfoCard(stats_frame, title="Оптимистичный (+15%)",
                                   value=f"{optimistic_price[0]:,.0f}", unit="₽/м²",
                                   color=colors["optimistic"])
        optimistic_card.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # Карточка с пессимистичным прогнозом
        pessimistic_card = InfoCard(stats_frame, title="Пессимистичный (-15%)",
                                    value=f"{pessimistic_price[0]:,.0f}", unit="₽/м²",
                                    color=colors["pessimistic"])
        pessimistic_card.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # Анимированное построение графика
        def animate(i):
            ax.clear()

            # Настройки осей
            ax.set_facecolor(theme.colors["graph_bg"])
            for spine in ax.spines.values():
                spine.set_color(theme.colors["text"])
            ax.tick_params(colors=theme.colors["text"])
            ax.grid(True, color=theme.colors["graph_grid"], linestyle='--', alpha=0.5)

            # Постепенное построение графика
            if i < len(df["year"]):
                current_years = df["year"][:i + 1]
                current_prices = y[:i + 1]
                ax.plot(current_years, current_prices, 'o-', color=colors["historical"],
                        label="Исторические данные", linewidth=2, markersize=6)
            else:
                ax.plot(df["year"], y, 'o-', color=colors["historical"],
                        label="Исторические данные", linewidth=2, markersize=6)

                if i < len(df["year"]) + 15:
                    progress = min(1, (i - len(df["year"]) + 1) / 15)
                    ax.plot(df["year"], model.predict(X), '--', color=colors["trend"],
                            alpha=progress, label="Базовый тренд", linewidth=2)
                else:
                    ax.plot(df["year"], model.predict(X), '--', color=colors["trend"],
                            label="Базовый тренд", linewidth=2)

                    if i < len(df["year"]) + 30:
                        progress = min(1, (i - len(df["year"]) - 14) / 15)
                        ax.plot(df["year"], optimistic_model.predict(X), ':', color=colors["optimistic"],
                                alpha=progress, label="Оптимистичный (+15%)", linewidth=2)
                        ax.plot(df["year"], pessimistic_model.predict(X), ':', color=colors["pessimistic"],
                                alpha=progress, label="Пессимистичный (-15%)", linewidth=2)
                    else:
                        ax.plot(df["year"], optimistic_model.predict(X), ':', color=colors["optimistic"],
                                label="Оптимистичный (+15%)", linewidth=2)
                        ax.plot(df["year"], pessimistic_model.predict(X), ':', color=colors["pessimistic"],
                                label="Пессимистичный (-15%)", linewidth=2)

                        if i < len(df["year"]) + 45:
                            progress = min(1, (i - len(df["year"]) - 29) / 15)
                            ax.scatter(2025, predicted_price, color=colors["trend"], s=100,
                                       alpha=progress, label=f"2025: {predicted_price[0]:.0f} ₽/м²")
                            ax.scatter(2025, optimistic_price, color=colors["optimistic"], s=100,
                                       alpha=progress, label=f"2025 (+15%): {optimistic_price[0]:.0f} ₽/м²")
                            ax.scatter(2025, pessimistic_price, color=colors["pessimistic"], s=100,
                                       alpha=progress, label=f"2025 (-15%): {pessimistic_price[0]:.0f} ₽/м²")
                        else:
                            ax.scatter(2025, predicted_price, color=colors["trend"], s=100,
                                       label=f"2025: {predicted_price[0]:.0f} ₽/м²")
                            ax.scatter(2025, optimistic_price, color=colors["optimistic"], s=100,
                                       label=f"2025 (+15%): {optimistic_price[0]:.0f} ₽/м²")
                            ax.scatter(2025, pessimistic_price, color=colors["pessimistic"], s=100,
                                       label=f"2025 (-15%): {pessimistic_price[0]:.0f} ₽/м²")

            ax.set_title(f"Динамика цен в {city}", fontsize=12, color=theme.colors["text"], pad=10)
            ax.set_xlabel("Год", fontsize=10, color=theme.colors["text"])
            ax.set_ylabel("Цена, ₽/м²", fontsize=10, color=theme.colors["text"])
            ax.xaxis.set_major_locator(MaxNLocator(integer=True))

            # Легенда
            legend = ax.legend(facecolor=theme.colors["graph_bg"], edgecolor='none',
                               labelcolor=theme.colors["text"],
                               bbox_to_anchor=(0.5, -0.25),
                               loc='upper center',
                               ncol=2,
                               fontsize=9)

        # Обработчик движения мыши для отображения информации
        def on_motion(event):
            if event.inaxes == ax:
                for line in ax.lines:
                    if line.contains(event)[0]:
                        x, y = line.get_data()
                        idx = np.argmin(np.abs(x - event.xdata))
                        info_text.set(f"{city}, {int(x[idx])} год: {y[idx]:.0f} ₽/м²")
                        break
                else:
                    for collection in ax.collections:
                        if collection.contains(event)[0]:
                            x = collection.get_offsets()[:, 0]
                            y = collection.get_offsets()[:, 1]
                            info_text.set(f"Прогноз {city}, 2025 год: {y[0]:.0f} ₽/м²")
                            break

        fig.canvas.mpl_connect('motion_notify_event', on_motion)

        # Встраиваем график в интерфейс
        canvas = FigureCanvasTkAgg(fig, master=frame_graph)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Запускаем анимацию
        global anim
        anim = animation.FuncAnimation(fig, animate, frames=len(df["year"]) + 45, interval=50, repeat=False)

        # Описание города
        description, wiki_url = get_city_info(city)
        desc_frame = tk.Frame(frame_graph, bg=theme.colors["bg"])
        desc_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        tk.Label(desc_frame, text=description, wraplength=700, justify=tk.LEFT,
                 bg=theme.colors["bg"], fg=theme.colors["text_secondary"], font=FONT).pack(side=tk.LEFT)

        # Кнопки управления
        btn_frame = tk.Frame(frame_graph, bg=theme.colors["bg"])
        btn_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        if wiki_url:
            SmoothButton(btn_frame, text="Википедия", width=100,
                         command=lambda: open_wiki(wiki_url)).pack(side=tk.LEFT, padx=5)

        SmoothButton(btn_frame, text="Диаграмма", width=100,
                     command=lambda: show_bar_chart(city)).pack(side=tk.LEFT, padx=5)

        SmoothButton(btn_frame, text="Удалить", width=100, bg_color=theme.colors["danger"],
                     hover_color="#ab4a4a", command=lambda: confirm_delete_city(city)).pack(side=tk.RIGHT, padx=5)

        # Убираем анимацию загрузки
        loading.stop_animation()
        loading.destroy()

    except Exception as e:
        messagebox.showerror("Ошибка", f"Произошла ошибка: {str(e)}")
        if 'loading' in locals():
            loading.stop_animation()
            loading.destroy()


def show_bar_chart(city):
    try:
        # Показываем анимацию загрузки
        loading_window = tk.Toplevel(root)
        loading_window.title("Построение диаграммы...")
        loading_window.geometry("200x100")
        loading_window.resizable(False, False)
        loading_window.configure(bg=theme.colors["bg"])

        tk.Label(loading_window, text="Построение диаграммы...",
                 bg=theme.colors["bg"], fg=theme.colors["text"]).pack(pady=10)

        loading_anim = LoadingAnimation(loading_window, size=50, color=theme.colors["accent"])
        loading_anim.pack()

        loading_window.update()

        df = get_city_data(city)
        if df.empty:
            messagebox.showerror("Ошибка", f"Нет данных для города {city}")
            loading_window.destroy()
            return

        fig, ax = plt.subplots(figsize=(8, 5), dpi=100)
        fig.patch.set_facecolor(theme.colors["graph_bg"])
        ax.set_facecolor(theme.colors["graph_bg"])

        bars = ax.bar(df["year"], df["average_price"], color=theme.colors["accent"])

        ax.set_title(f"Цены за м² в {city}", fontsize=12, color=theme.colors["text"])
        ax.set_xlabel("Год", fontsize=10, color=theme.colors["text"])
        ax.set_ylabel("Цена, ₽/м²", fontsize=10, color=theme.colors["text"])
        ax.grid(True, axis='y', color=theme.colors["graph_grid"], linestyle='--', alpha=0.5)
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))

        # Настройка цветов осей
        for spine in ax.spines.values():
            spine.set_color(theme.colors["text"])
        ax.tick_params(colors=theme.colors["text"])

        # Информационное окно
        info_text = tk.StringVar()
        info_text.set("Наведите курсор на столбцы для информации")

        info_frame = tk.Frame(loading_window, bg=theme.colors["tooltip_bg"], padx=10, pady=5)
        info_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        tk.Label(info_frame, textvariable=info_text, bg=theme.colors["tooltip_bg"],
                 fg=theme.colors["tooltip_text"], font=FONT_SMALL).pack()

        # Добавляем подсказки
        def hover(event):
            if event.inaxes == ax:
                for bar in bars:
                    if bar.contains(event)[0]:
                        year = int(bar.get_x() + bar.get_width() / 2)
                        price = bar.get_height()
                        info_text.set(f"{city}, {year} год: {price:.0f} ₽/м²")
                        break

        fig.canvas.mpl_connect("motion_notify_event", hover)

        # Закрываем окно загрузки и открываем диаграмму
        loading_window.destroy()

        chart_window = tk.Toplevel(root)
        chart_window.title(f"Диаграмма цен - {city}")
        chart_window.geometry("800x600")
        chart_window.configure(bg=theme.colors["bg"])

        canvas = FigureCanvasTkAgg(fig, master=chart_window)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Кнопка закрытия
        btn_frame = tk.Frame(chart_window, bg=theme.colors["bg"])
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

        SmoothButton(btn_frame, text="Закрыть", command=chart_window.destroy).pack()

    except Exception as e:
        messagebox.showerror("Ошибка", f"Произошла ошибка: {str(e)}")
        if 'loading_window' in locals():
            loading_window.destroy()


# Подтверждение удаления города
def confirm_delete_city(city):
    if messagebox.askyesno("Подтверждение", f"Вы уверены, что хотите удалить город {city} из базы данных?"):
        if delete_city_from_db(city):
            update_city_list()
            # Очищаем график
            for widget in frame_graph.winfo_children():
                widget.destroy()

            # Добавляем сообщение о выборе города
            tk.Label(frame_graph, text="Выберите город для отображения данных",
                     bg=theme.colors["bg"], fg=theme.colors["text_secondary"], font=FONT_TITLE).pack(pady=50)


# Обработка выбора города
def on_city_select(event):
    try:
        if not city_listbox.curselection():
            return

        selected_city = city_listbox.get(city_listbox.curselection())
        if isinstance(selected_city, str):
            plot_forecast(selected_city)
        else:
            messagebox.showerror("Ошибка", "Выберите город из списка")
    except Exception as e:
        messagebox.showerror("Ошибка", f"Ошибка при выборе города: {str(e)}")


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
    add_city_window.configure(bg=theme.colors["bg"])
    add_city_window.resizable(False, False)

    # Стилизованный заголовок
    header = tk.Frame(add_city_window, bg=theme.colors["accent"])
    header.pack(fill=tk.X)
    tk.Label(header, text="Добавление нового города", bg=theme.colors["accent"],
             fg="white", font=FONT_TITLE).pack(pady=10)

    # Основной контейнер
    container = tk.Frame(add_city_window, bg=theme.colors["bg"])
    container.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)

    def create_entry_row(parent, label_text):
        frame = tk.Frame(parent, bg=theme.colors["bg"])
        frame.pack(fill=tk.X, pady=5)
        tk.Label(frame, text=label_text, bg=theme.colors["bg"], font=FONT,
                 fg=theme.colors["text"], width=25, anchor="w").pack(side=tk.LEFT)
        entry = tk.Entry(frame, bg=theme.colors["entry_bg"], fg=theme.colors["text"],
                         insertbackground=theme.colors["text"], relief=tk.FLAT)
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
    tk.Label(container, text="Описание города:", bg=theme.colors["bg"],
             font=FONT, fg=theme.colors["text"], anchor="w").pack(fill=tk.X, pady=5)
    description_text = tk.Text(container, height=5, font=FONT, bg=theme.colors["entry_bg"],
                               fg=theme.colors["text"])
    description_text.pack(fill=tk.X, pady=5)

    # Ссылка на Википедию
    wiki_entry = create_entry_row(container, "Ссылка на Википедию:")

    # Кнопки
    button_frame = tk.Frame(container, bg=theme.colors["panel"])
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

    save_btn = SmoothButton(button_frame, text="Сохранить", command=save_city)
    save_btn.pack(side=tk.RIGHT, padx=10)

    cancel_btn = SmoothButton(button_frame, text="Отмена", command=add_city_window.destroy,
                              bg_color="#5a5a5a", hover_color="#6a6a6a")
    cancel_btn.pack(side=tk.RIGHT)


# Функция для отображения справки
def show_help():
    help_window = tk.Toplevel(root)
    help_window.title("Справка по приложению")
    help_window.geometry("800x700")
    help_window.configure(bg=theme.colors["bg"])
    help_window.resizable(False, False)

    # Создаем Notebook (вкладки)
    notebook = ttk.Notebook(help_window)
    notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # Вкладка о формате файла
    file_frame = tk.Frame(notebook, bg=theme.colors["bg"])
    notebook.add(file_frame, text="Формат данных")

    tk.Label(file_frame, text="Поддерживаемые форматы данных:",
             bg=theme.colors["bg"], font=FONT_BOLD, fg=theme.colors["text"],
             anchor="w").pack(fill=tk.X, pady=10, padx=10)

    # Формат TXT
    tk.Label(file_frame, text="Текстовый файл (TXT):",
             bg=theme.colors["bg"], font=FONT_BOLD, fg=theme.colors["accent"],
             anchor="w").pack(fill=tk.X, padx=10, pady=(10, 5))

    example_text = """[
    ("Москва", 2020, 195000, "Столица России", "https://ru.wikipedia.org/wiki/Москва"),
    ("Москва", 2021, 210000, "Столица России", "https://ru.wikipedia.org/wiki/Москва"),
    ("Санкт-Петербург", 2020, 120000, "Северная столица", "https://ru.wikipedia.org/wiki/Санкт-Петербург")
]"""

    text_widget = tk.Text(file_frame, height=8, width=80, font=("Consolas", 10), wrap=tk.WORD,
                          bg=theme.colors["entry_bg"], fg=theme.colors["text"])
    text_widget.insert(tk.END, example_text)
    text_widget.config(state="disabled")
    text_widget.pack(padx=10, pady=5, fill=tk.X)

    # Формат JSON
    tk.Label(file_frame, text="JSON файл:",
             bg=theme.colors["bg"], font=FONT_BOLD, fg=theme.colors["accent"],
             anchor="w").pack(fill=tk.X, padx=10, pady=(10, 5))

    example_json = """[
    ["Москва", 2020, 195000, "Столица России", "https://ru.wikipedia.org/wiki/Москва"],
    ["Москва", 2021, 210000, "Столица России", "https://ru.wikipedia.org/wiki/Москва"],
    ["Санкт-Петербург", 2020, 120000, "Северная столица", "https://ru.wikipedia.org/wiki/Санкт-Петербург"]
]"""

    json_widget = tk.Text(file_frame, height=8, width=80, font=("Consolas", 10), wrap=tk.WORD,
                          bg=theme.colors["entry_bg"], fg=theme.colors["text"])
    json_widget.insert(tk.END, example_json)
    json_widget.config(state="disabled")
    json_widget.pack(padx=10, pady=5, fill=tk.X)

    # Вкладка о функционале
    func_frame = tk.Frame(notebook, bg=theme.colors["bg"])
    notebook.add(func_frame, text="Функционал")

    info_text = """Приложение для анализа цен на недвижимость в городах России:

Основные возможности:
1. Визуализация динамики цен по годам
2. Прогнозирование цен на 2025 год (3 сценария)
3. Интерактивные графики с подсказками
4. Управление базой данных городов
5. Импорт/экспорт данных в различных форматах

График показывает:
- Фактические цены по годам (синие точки)
- Базовый прогноз (зеленая линия)
- Оптимистичный сценарий (+15%, оранжевая линия)
- Пессимистичный сценарий (-15%, красная линия)
- Прогнозируемые значения на 2025 год

Инструкция:
1. Выберите город из списка слева
2. Изучите график и прогноз
3. Используйте кнопки под графиком для дополнительных действий
4. Добавляйте новые города через меню "Добавить город"

Форматы данных:
- TXT: список кортежей в Python-формате
- JSON: массив записей в формате JSON
Каждая запись содержит: город, год, цену, описание, ссылку"""

    text_widget = tk.Text(func_frame, height=25, width=80, font=FONT, wrap=tk.WORD,
                          bg=theme.colors["entry_bg"], fg=theme.colors["text"])
    text_widget.insert(tk.END, info_text)
    text_widget.config(state="disabled")
    text_widget.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    # Кнопка закрытия
    close_btn = SmoothButton(help_window, text="Закрыть", command=help_window.destroy)
    close_btn.pack(pady=10)


# Функция для обновления списка городов
def update_city_list():
    global all_cities
    all_cities = get_cities()
    city_listbox.delete(0, tk.END)
    for city in all_cities:
        city_listbox.insert(tk.END, city)


# Создание главного окна
root = tk.Tk()
root.title("Анализ цен на недвижимость")
root.geometry("1200x800")
root.configure(bg=theme.colors["bg"])

# Верхняя панель
top_frame = tk.Frame(root, bg=theme.colors["panel"], height=50)
top_frame.pack(fill=tk.X, padx=10, pady=10)

# Кнопки управления
SmoothButton(top_frame, text="Добавить город", width=140,
             command=add_city).pack(side=tk.LEFT, padx=5)

SmoothButton(top_frame, text="Импорт TXT", width=100,
             command=load_from_txt).pack(side=tk.LEFT, padx=5)

SmoothButton(top_frame, text="Импорт JSON", width=100,
             command=load_from_json).pack(side=tk.LEFT, padx=5)

SmoothButton(top_frame, text="Экспорт TXT", width=100,
             command=export_to_txt).pack(side=tk.LEFT, padx=5)

SmoothButton(top_frame, text="Экспорт JSON", width=100,
             command=export_to_json).pack(side=tk.LEFT, padx=5)

SmoothButton(top_frame, text="Справка", width=80,
             command=show_help).pack(side=tk.RIGHT, padx=5)

# Основное содержимое
main_frame = tk.Frame(root, bg=theme.colors["bg"])
main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

# Левая панель - список городов
left_panel = tk.Frame(main_frame, bg=theme.colors["panel"], width=280)
left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

tk.Label(left_panel, text="Поиск города:", bg=theme.colors["panel"],
         fg=theme.colors["text"], font=FONT_BOLD).pack(pady=(10, 5), padx=10, anchor="w")

city_search_var = tk.StringVar()
search_entry = tk.Entry(left_panel, bg=theme.colors["entry_bg"], fg=theme.colors["text"],
                        insertbackground=theme.colors["text"], relief=tk.FLAT,
                        textvariable=city_search_var)
search_entry.pack(fill=tk.X, padx=10, pady=(0, 10))
search_entry.bind("<KeyRelease>", filter_cities)

scrollbar = tk.Scrollbar(left_panel)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

city_listbox = CityListbox(left_panel, yscrollcommand=scrollbar.set, height=30)
city_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
city_listbox.bind("<<ListboxSelect>>", on_city_select)

scrollbar.config(command=city_listbox.yview)

# Правая панель - график
frame_graph = tk.Frame(main_frame, bg=theme.colors["bg"])
frame_graph.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

# Начальное сообщение
tk.Label(frame_graph, text="Выберите город для отображения данных",
         bg=theme.colors["bg"], fg=theme.colors["text_secondary"], font=FONT_TITLE).pack(pady=50)

# Загрузка данных
create_database()
all_cities = get_cities()
update_city_list()

root.mainloop()