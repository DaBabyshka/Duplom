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
import time
from PIL import Image, ImageTk
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.animation as animation
from tkinter import font as tkfont


# Настройки темы
class Theme:
    def __init__(self):
        self.light = {
            "bg": "#f0f8ff",
            "button": "#4a90e2",
            "button_hover": "#3a7bd5",
            "delete": "#e74c3c",
            "delete_hover": "#c0392b",
            "accent": "#3d85c6",
            "text": "#2c3e50",
            "panel": "#e1f0fa",
            "border": "#2c3e50",
            "entry_bg": "white",
            "graph_bg": "white",
            "graph_text": "black",
            "highlight": "#f5f9ff"
        }
        self.dark = {
            "bg": "#1a1a2e",
            "button": "#16213e",
            "button_hover": "#0f3460",
            "delete": "#e94560",
            "delete_hover": "#d23350",
            "accent": "#3d85c6",
            "text": "#e6e6e6",
            "panel": "#16213e",
            "border": "#0f3460",
            "entry_bg": "#2a2a4a",
            "graph_bg": "#1a1a2e",
            "graph_text": "white",
            "highlight": "#2a2a4a"
        }
        self.current = self.light

    def toggle(self):
        self.current = self.dark if self.current == self.light else self.light
        return self.current


theme = Theme()

FONT = ("Segoe UI", 11)
FONT_BOLD = ("Segoe UI", 11, "bold")
FONT_TITLE = ("Segoe UI", 14, "bold")


# Анимированная кнопка
class ModernButton(tk.Canvas):
    def __init__(self, master=None, text="", command=None, width=140, height=40,
                 bg_color=theme.current["button"], fg_color="white",
                 hover_color=theme.current["button_hover"], radius=10, font=FONT_BOLD, **kwargs):
        super().__init__(master, width=width, height=height,
                         highlightthickness=0, bd=0, **kwargs)
        self.command = command
        self.bg_color = bg_color
        self.fg_color = fg_color
        self.hover_color = hover_color
        self.radius = radius
        self.text = text
        self.font = font
        self.is_pressed = False

        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<ButtonPress-1>", self.on_press)
        self.bind("<ButtonRelease-1>", self.on_release)

        self.draw_button()

    def draw_button(self):
        self.delete("all")
        # Фон кнопки
        self.create_rounded_rect(0, 0, self.winfo_reqwidth(), self.winfo_reqheight(),
                                 radius=self.radius, fill=self.bg_color, outline="")

        # Разбиваем текст на несколько строк если он слишком длинный
        if len(self.text) > 15:
            words = self.text.split()
            lines = []
            current_line = words[0]
            for word in words[1:]:
                if len(current_line) + len(word) + 1 <= 15:
                    current_line += " " + word
                else:
                    lines.append(current_line)
                    current_line = word
            lines.append(current_line)
            text = "\n".join(lines)
            font = (self.font[0], self.font[1] - 1)  # Уменьшаем шрифт для многострочного текста
        else:
            text = self.text
            font = self.font

        # Текст
        self.create_text(self.winfo_reqwidth() / 2, self.winfo_reqheight() / 2,
                         text=text, fill=self.fg_color, font=font,
                         width=self.winfo_reqwidth() - 20)  # Добавляем перенос по словам

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

    def on_enter(self, event=None):
        self.current_color = self.hover_color
        self.draw_button()

    def on_leave(self, event=None):
        if not self.is_pressed:
            self.current_color = self.bg_color
            self.draw_button()

    def on_press(self, event=None):
        self.is_pressed = True
        self.scale("all", self.winfo_reqwidth() / 2, self.winfo_reqheight() / 2, 0.95, 0.95)

    def on_release(self, event=None):
        self.is_pressed = False
        self.scale("all", self.winfo_reqwidth() / 2, self.winfo_reqheight() / 2, 1 / 0.95, 1 / 0.95)
        self.on_enter()

        if self.command:
            self.command()

    def config(self, **kwargs):
        if "text" in kwargs:
            self.text = kwargs["text"]
            self.draw_button()
        if "bg" in kwargs or "bg_color" in kwargs:
            self.bg_color = kwargs.get("bg", kwargs.get("bg_color", self.bg_color))
            self.current_color = self.bg_color
            self.draw_button()
        if "fg" in kwargs or "fg_color" in kwargs:
            self.fg_color = kwargs.get("fg", kwargs.get("fg_color", self.fg_color))
            self.draw_button()
        if "activebackground" in kwargs or "hover_color" in kwargs:
            self.hover_color = kwargs.get("activebackground", kwargs.get("hover_color", self.hover_color))
        if "command" in kwargs:
            self.command = kwargs["command"]


# Кнопка удаления
class DeleteButton(ModernButton):
    def __init__(self, master=None, **kwargs):
        kwargs['bg_color'] = theme.current["delete"]
        kwargs['hover_color'] = theme.current["delete_hover"]
        super().__init__(master, **kwargs)


# Анимированный список
class AnimatedListbox(tk.Listbox):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.config(
            font=FONT,
            selectbackground=theme.current["button_hover"],
            selectforeground="white",
            bd=0,
            highlightthickness=0,
            bg=theme.current["panel"],
            fg=theme.current["text"]
        )
        self.bind("<MouseWheel>", self.on_scroll)
        self.scroll_speed = 2
        self.scroll_anim = None

    def on_scroll(self, event):
        if self.scroll_anim:
            self.after_cancel(self.scroll_anim)

        if event.delta > 0:
            self.yview_scroll(-1, "units")
        else:
            self.yview_scroll(1, "units")

        # Плавная остановка
        self.scroll_speed = 5
        self.decelerate_scroll(event)

    def decelerate_scroll(self, event):
        if self.scroll_speed > 0:
            if event.delta > 0:
                self.yview_scroll(-1, "units")
            else:
                self.yview_scroll(1, "units")
            self.scroll_speed -= 1
            self.scroll_anim = self.after(20, self.decelerate_scroll, event)
        else:
            self.scroll_anim = None


# Радиальная анимация загрузки
class LoadingAnimation(tk.Canvas):
    def __init__(self, master=None, size=50, color=theme.current["button"], **kwargs):
        super().__init__(master, width=size, height=size,
                         highlightthickness=0, bd=0, **kwargs)
        self.size = size
        self.color = color
        self.angle = 0
        self.arc = None
        self.animation_id = None
        self.start_animation()

    def start_animation(self):
        self.delete("all")
        self.angle = (self.angle + 5) % 360
        extent = 60  # Длина дуги

        # Рисуем фон
        self.create_oval(5, 5, self.size - 5, self.size - 5,
                         outline=theme.current["panel"], width=3)

        # Рисуем анимированную дугу
        self.arc = self.create_arc(5, 5, self.size - 5, self.size - 5,
                                   start=self.angle, extent=extent,
                                   style=tk.ARC, outline=self.color, width=3)

        self.animation_id = self.after(50, self.start_animation)

    def stop_animation(self):
        if self.animation_id:
            self.after_cancel(self.animation_id)
            self.animation_id = None
        self.delete("all")


# Функции для работы с базой данных
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
            if isinstance(widget, FigureCanvasTkAgg):
                widget.get_tk_widget().destroy()
            elif widget not in [description_label, link_button, show_bar_chart_button, control_frame, button_frame]:
                widget.destroy()

        # Показываем анимацию загрузки
        loading = LoadingAnimation(frame_graph, size=100, color=theme.current["accent"])
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

        fig, ax = plt.subplots(figsize=(8, 6), dpi=100, facecolor=theme.current["graph_bg"])
        ax.set_facecolor(theme.current["graph_bg"])

        # Анимированный график
        def animate(i):
            ax.clear()
            if i < len(df["year"]):
                ax.plot(df["year"][:i + 1], y[:i + 1], marker='o', color=theme.current["accent"],
                        label="Исторические данные")
            else:
                ax.plot(df["year"], y, marker='o', color=theme.current["accent"],
                        label="Исторические данные")

                if i < len(df["year"]) + 10:
                    progress = (i - len(df["year"]) + 1) / 10
                    ax.plot(df["year"], model.predict(X), linestyle='--', color='green',
                            alpha=progress, label="Базовый тренд")
                else:
                    ax.plot(df["year"], model.predict(X), linestyle='--', color='green',
                            label="Базовый тренд")

                    if i < len(df["year"]) + 20:
                        progress = (i - len(df["year"]) - 9) / 10
                        ax.plot(df["year"], optimistic_model.predict(X), linestyle=':', color='blue',
                                alpha=progress, label="Оптимистичный прогноз (+15%)")
                        ax.plot(df["year"], pessimistic_model.predict(X), linestyle=':', color='red',
                                alpha=progress, label="Пессимистичный прогноз (-15%)")
                    else:
                        ax.plot(df["year"], optimistic_model.predict(X), linestyle=':', color='blue',
                                label="Оптимистичный прогноз (+15%)")
                        ax.plot(df["year"], pessimistic_model.predict(X), linestyle=':', color='red',
                                label="Пессимистичный прогноз (-15%)")

                        if i < len(df["year"]) + 30:
                            progress = (i - len(df["year"]) - 19) / 10
                            ax.scatter(2025, predicted_price, color='green',
                                       alpha=progress, label=f"Прогноз 2025: {predicted_price[0]:.0f} ₽/м²")
                            ax.scatter(2025, optimistic_price, color='blue',
                                       alpha=progress, label=f"Оптим. 2025: {optimistic_price[0]:.0f} ₽/м²")
                            ax.scatter(2025, pessimistic_price, color='red',
                                       alpha=progress, label=f"Песс. 2025: {pessimistic_price[0]:.0f} ₽/м²")
                        else:
                            ax.scatter(2025, predicted_price, color='green',
                                       label=f"Прогноз 2025: {predicted_price[0]:.0f} ₽/м²")
                            ax.scatter(2025, optimistic_price, color='blue',
                                       label=f"Оптим. 2025: {optimistic_price[0]:.0f} ₽/м²")
                            ax.scatter(2025, pessimistic_price, color='red',
                                       label=f"Песс. 2025: {pessimistic_price[0]:.0f} ₽/м²")

            ax.set_title(f"Динамика цен в {city} с прогнозом", fontsize=14, color=theme.current["graph_text"])
            ax.set_xlabel("Год", fontsize=12, color=theme.current["graph_text"])
            ax.set_ylabel("Цена, ₽/м²", fontsize=12, color=theme.current["graph_text"])
            ax.grid(True, color='gray' if theme.current == theme.dark else 'lightgray')
            ax.legend(facecolor=theme.current["graph_bg"], edgecolor=theme.current["graph_bg"],
                      labelcolor=theme.current["graph_text"])
            ax.xaxis.set_major_locator(MaxNLocator(integer=True))

            # Настройка цветов осей
            ax.spines['bottom'].set_color(theme.current["graph_text"])
            ax.spines['top'].set_color(theme.current["graph_text"])
            ax.spines['right'].set_color(theme.current["graph_text"])
            ax.spines['left'].set_color(theme.current["graph_text"])
            ax.tick_params(axis='x', colors=theme.current["graph_text"])
            ax.tick_params(axis='y', colors=theme.current["graph_text"])

        canvas = FigureCanvasTkAgg(fig, master=frame_graph)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Запускаем анимацию
        ani = animation.FuncAnimation(fig, animate, frames=len(df["year"]) + 30, interval=100, repeat=False)

        description, wiki_url = get_city_info(city)
        description_label.config(text=description)
        if wiki_url:
            link_button.config(state="normal", command=lambda: open_wiki(wiki_url))
        else:
            link_button.config(state="disabled")

        show_bar_chart_button.config(state="normal", command=lambda: show_bar_chart(city))
        delete_city_btn.config(state="normal", command=lambda: confirm_delete_city(city))

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
        df = get_city_data(city)
        if df.empty:
            messagebox.showerror("Ошибка", f"Нет данных для города {city}")
            return

        fig, ax = plt.subplots(figsize=(8, 6), dpi=100)
        fig.patch.set_facecolor(theme.current["graph_bg"])
        ax.set_facecolor(theme.current["graph_bg"])

        bars = ax.bar(df["year"], df["average_price"], color=theme.current["accent"])

        ax.set_title(f"Цены за м² в {city} по годам", fontsize=14, color=theme.current["graph_text"])
        ax.set_xlabel("Год", fontsize=12, color=theme.current["graph_text"])
        ax.set_ylabel("Цена, ₽/м²", fontsize=12, color=theme.current["graph_text"])
        ax.grid(True, axis='y', color='gray' if theme.current == theme.dark else 'lightgray')
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))

        # Настройка цветов осей
        ax.spines['bottom'].set_color(theme.current["graph_text"])
        ax.spines['top'].set_color(theme.current["graph_text"])
        ax.spines['right'].set_color(theme.current["graph_text"])
        ax.spines['left'].set_color(theme.current["graph_text"])
        ax.tick_params(axis='x', colors=theme.current["graph_text"])
        ax.tick_params(axis='y', colors=theme.current["graph_text"])

        # Добавляем подсказки
        def hover(event):
            if event.inaxes == ax:
                for bar in bars:
                    if bar.contains(event)[0]:
                        year = int(bar.get_x() + bar.get_width() / 2)
                        price = bar.get_height()
                        ax.set_title(f"{city}: {year} год - {price:.0f} ₽/м²",
                                     fontsize=14, color=theme.current["graph_text"])
                        fig.canvas.draw_idle()
                        break

        fig.canvas.mpl_connect("motion_notify_event", hover)

        # Создаем новое окно для диаграммы
        chart_window = tk.Toplevel(root)
        chart_window.title(f"Диаграмма цен - {city}")
        chart_window.geometry("800x600")
        chart_window.configure(bg=theme.current["bg"])

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
    add_city_window.configure(bg=theme.current["bg"])
    add_city_window.resizable(False, False)

    # Стилизованный заголовок
    header = tk.Frame(add_city_window, bg=theme.current["button"])
    header.pack(fill=tk.X)
    tk.Label(header, text="Добавление нового города", bg=theme.current["button"],
             fg="white", font=FONT_TITLE).pack(pady=10)

    # Основной контейнер
    container = tk.Frame(add_city_window, bg=theme.current["bg"])
    container.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)

    def create_entry_row(parent, label_text):
        frame = tk.Frame(parent, bg=theme.current["bg"])
        frame.pack(fill=tk.X, pady=5)
        tk.Label(frame, text=label_text, bg=theme.current["bg"], font=FONT,
                 fg=theme.current["text"], width=25, anchor="w").pack(side=tk.LEFT)
        entry = ttk.Entry(frame, font=FONT, background=theme.current["entry_bg"])
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
    tk.Label(container, text="Описание города:", bg=theme.current["bg"],
             font=FONT, fg=theme.current["text"], anchor="w").pack(fill=tk.X, pady=5)
    description_text = tk.Text(container, height=5, font=FONT, bg=theme.current["entry_bg"],
                               fg=theme.current["text"])
    description_text.pack(fill=tk.X, pady=5)

    # Ссылка на Википедию
    wiki_entry = create_entry_row(container, "Ссылка на Википедию:")

    # Кнопки
    button_frame = tk.Frame(container, bg=theme.current["panel"])
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

    cancel_btn = ModernButton(button_frame, text="Отмена", command=add_city_window.destroy,
                              bg_color="#95a5a6", hover_color="#7f8c8d")
    cancel_btn.pack(side=tk.RIGHT)


# Функция для отображения справки
def show_help():
    help_window = tk.Toplevel(root)
    help_window.title("Справка по приложению")
    help_window.geometry("700x600")
    help_window.configure(bg=theme.current["bg"])
    help_window.resizable(False, False)

    # Создаем Notebook (вкладки)
    notebook = ttk.Notebook(help_window)
    notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # Вкладка о формате файла
    file_frame = tk.Frame(notebook, bg=theme.current["bg"])
    notebook.add(file_frame, text="Формат TXT файла")

    tk.Label(file_frame, text="Пример содержимого TXT файла:",
             bg=theme.current["bg"], font=FONT_BOLD, fg=theme.current["text"],
             anchor="w").pack(fill=tk.X, pady=10, padx=10)

    example_text = """[
    ("Москва", 2020, 195000, "Столица России", "https://ru.wikipedia.org/wiki/Москва"),
    ("Москва", 2021, 210000, "Столица России", "https://ru.wikipedia.org/wiki/Москва"),
    ("Москва", 2022, 230000, "Столица России", "https://ru.wikipedia.org/wiki/Москва"),
    ("Санкт-Петербург", 2020, 120000, "Северная столица", "https://ru.wikipedia.org/wiki/Санкт-Петербург"),
    ("Санкт-Петербург", 2021, 125000, "Северная столица", "https://ru.wikipedia.org/wiki/Санкт-Петербург")
]"""

    text_widget = tk.Text(file_frame, height=15, width=80, font=("Consolas", 10), wrap=tk.WORD,
                          bg=theme.current["entry_bg"], fg=theme.current["text"])
    text_widget.insert(tk.END, example_text)
    text_widget.config(state="disabled")
    text_widget.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

    tk.Label(file_frame, text="Файл должен содержать список кортежей, где каждый кортеж состоит из:",
             bg=theme.current["bg"], font=FONT, fg=theme.current["text"],
             anchor="w").pack(fill=tk.X, padx=10)

    tk.Label(file_frame,
             text="1. Название города\n2. Год (2020-2024)\n3. Средняя цена за м²\n4. Описание города\n5. Ссылка на Википедию",
             bg=theme.current["bg"], font=FONT, fg=theme.current["text"],
             anchor="w", justify=tk.LEFT).pack(fill=tk.X, padx=20, pady=5)

    # Вкладка о функционале
    func_frame = tk.Frame(notebook, bg=theme.current["bg"])
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

    text_widget = tk.Text(func_frame, height=25, width=80, font=FONT, wrap=tk.WORD,
                          bg=theme.current["entry_bg"], fg=theme.current["text"])
    text_widget.insert(tk.END, info_text)
    text_widget.config(state="disabled")
    text_widget.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    # Кнопка закрытия
    close_btn = ModernButton(help_window, text="Закрыть", command=help_window.destroy)
    close_btn.pack(pady=10)


# Функция для обновления списка городов
def update_city_list():
    global all_cities
    all_cities = get_cities()
    city_listbox.delete(0, tk.END)
    for city in all_cities:
        city_listbox.insert(tk.END, city)


# Функция для переключения темы
def toggle_theme():
    new_theme = theme.toggle()

    # Обновляем цвета главного окна
    root.config(bg=new_theme["bg"])
    frame_left.config(bg=new_theme["panel"])
    frame_graph.config(bg=new_theme["bg"])
    control_frame.config(bg=new_theme["bg"])
    button_frame.config(bg=new_theme["panel"])

    # Обновляем цвета виджетов
    city_search_label.config(bg=new_theme["panel"], fg=new_theme["text"])
    city_listbox.config(bg=new_theme["panel"], fg=new_theme["text"],
                        selectbackground=new_theme["button_hover"])
    description_label.config(bg=new_theme["bg"], fg=new_theme["text"])

    # Обновляем кнопки
    for btn in [add_city_btn, delete_city_btn, load_txt_btn, help_btn,
                theme_btn, link_button, show_bar_chart_button]:
        btn.config(bg_color=new_theme["button" if btn not in [delete_city_btn, theme_btn] else "delete"],
                   hover_color=new_theme["button_hover" if btn not in [delete_city_btn, theme_btn] else "delete_hover"],
                   fg_color="white")
        btn.draw_button()

    # Обновляем тему графика, если он есть
    for widget in frame_graph.winfo_children():
        if isinstance(widget, FigureCanvasTkAgg):
            plot_forecast(city_listbox.get(city_listbox.curselection()))
            break


# --- Создание основного интерфейса ---
root = tk.Tk()
root.title("Прогноз цен на недвижимость в городах России")
root.configure(bg=theme.current["bg"])
root.geometry("1100x800")

# Установка иконки (если есть)
try:
    root.iconbitmap("home_icon.ico")
except:
    pass

# Стилизация
style = ttk.Style()
style.theme_use("clam")
style.configure("TFrame", background=theme.current["bg"])
style.configure("TLabel", background=theme.current["bg"], font=FONT,
                foreground=theme.current["text"])
style.configure("TEntry", font=FONT, fieldbackground=theme.current["entry_bg"],
                foreground=theme.current["text"])
style.configure("TButton", font=FONT_BOLD, padding=6)

# Верхняя панель с кнопками
top_frame = tk.Frame(root, bg=theme.current["panel"], height=60)
top_frame.pack(fill=tk.X, padx=10, pady=(10, 0))

# Кнопки в верхней панели
buttons = [
    ("Добавить город", add_city, theme.current["button"], theme.current["button_hover"]),
    ("Удалить город", lambda: confirm_delete_city(city_listbox.get(tk.ACTIVE)),
     theme.current["delete"], theme.current["delete_hover"]),
    ("Загрузить TXT", load_from_txt, "#2ecc71", "#27ae60"),  # Укороченный текст
    ("Загрузить JSON", load_from_json, "#2ecc71", "#27ae60"),
    ("Экспорт TXT", export_to_txt, "#3498db", "#2980b9"),  # Укороченный текст
    ("Экспорт JSON", export_to_json, "#3498db", "#2980b9"),
    ("Справка", show_help, "#9b59b6", "#8e44ad"),
    ("Тема", toggle_theme, "#34495e", "#2c3e50")  # Укороченный текст
]

for text, cmd, bg, hov in buttons:
    btn = ModernButton(top_frame, text=text, command=cmd, width=140, height=40,
                      bg_color=bg, hover_color=hov)
    btn.pack(side=tk.LEFT, padx=5, pady=10)

# Сохраняем ссылки на важные кнопки
add_city_btn = buttons[0][2]
delete_city_btn = buttons[1][2]
load_txt_btn = buttons[2][2]
help_btn = buttons[6][2]
theme_btn = buttons[7][2]

# Левый фрейм: выбор города
frame_left = tk.Frame(root, bg=theme.current["panel"], bd=0, relief=tk.RIDGE)
frame_left.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

city_search_label = tk.Label(frame_left, text="Поиск города:", bg=theme.current["panel"],
                             font=FONT_BOLD, fg=theme.current["text"])
city_search_label.pack(anchor="w", pady=(5, 0), padx=5)

city_search_var = tk.StringVar()
city_search_entry = ttk.Entry(frame_left, textvariable=city_search_var)
city_search_entry.pack(fill=tk.X, pady=5, padx=5)
city_search_entry.bind("<KeyRelease>", filter_cities)

city_listbox = AnimatedListbox(frame_left, height=30, exportselection=False)
city_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
city_listbox.bind("<ButtonRelease-1>", on_city_select)

# Правый фрейм: график
frame_graph = tk.Frame(root, bg=theme.current["bg"], bd=0, relief=tk.RIDGE)
frame_graph.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

# Элементы управления графиком
control_frame = tk.Frame(frame_graph, bg=theme.current["bg"])
control_frame.pack(fill=tk.X)

description_label = tk.Label(frame_graph, text="Выберите город для отображения данных",
                             bg=theme.current["bg"], font=FONT, wraplength=800,
                             justify=tk.LEFT, fg=theme.current["text"])
description_label.pack(pady=10)

button_frame = tk.Frame(frame_graph, bg=theme.current["panel"])
button_frame.pack(fill=tk.X, pady=5, padx=5, ipady=5)

link_button = ModernButton(button_frame, text="Перейти на Википедию", width=150)
link_button.pack(side=tk.LEFT, padx=5)
link_button.config(state="disabled")

show_bar_chart_button = ModernButton(button_frame, text="Показать диаграмму", width=150)
show_bar_chart_button.pack(side=tk.LEFT, padx=5)
show_bar_chart_button.config(state="disabled")

# Загрузка данных
all_cities = get_cities()
update_city_list()

root.mainloop()