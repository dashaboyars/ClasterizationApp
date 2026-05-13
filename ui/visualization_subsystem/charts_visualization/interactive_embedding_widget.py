import numpy as np
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import QToolTip
from matplotlib import pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.patches as mpatches
from scipy.spatial import KDTree


class InteractiveEmbeddingWidget(FigureCanvas):
    def __init__(self, parent=None):
        self.figure = Figure(figsize=(5, 3), facecolor='#f5f5f5')
        super().__init__(self.figure)

        self.ax = self.figure.add_subplot(111)
        self.ax.tick_params(axis='both', labelsize=6)
        self.ax.set_title("Карта эмбеддингов (t-SNE)", fontsize=8, fontweight='bold')

        #для интерактива
        self.embeddings_2d = None
        self.cluster_labels = None
        self.images_list = None
        self.points = []

        # Для быстрого поиска
        self.kdtree = None
        self.point_positions = None

        # Для подсветки
        self.current_hover_index = -1

        self.scatter_plot = None
        self.legend = None
        self.highlight_artist = None

        # Подключаем события мыши
        self.mpl_connect('motion_notify_event', self.on_hover)

    def clear_map(self):
        # Удаляем scatter, если он есть
        if hasattr(self, 'scatter_plot') and self.scatter_plot:
            try:
                self.scatter_plot.remove()
            except:
                pass
            self.scatter_plot = None

        # Удаляем легенду, если она есть
        if hasattr(self, 'legend') and self.legend:
            try:
                self.legend.remove()
            except:
                pass
            self.legend = None

        # Очищаем оси
        self.ax.clear()

        # Сбрасываем KDTree
        self.kdtree = None
        self.embeddings_2d = None
        self.cluster_labels = None
        self.images_list = None
        self.current_hover_index = -1
        self.draw_idle()


    def draw_points(self, embeddings_2d, cluster_labels, images_list):
        self.clear_map()

        self.embeddings_2d = embeddings_2d
        self.cluster_labels = cluster_labels
        self.images_list = images_list

        self.point_positions = embeddings_2d
        self.kdtree = KDTree(embeddings_2d)

        unique_clusters = np.unique(cluster_labels)

        # Создаем цветовую палитру
        if len(unique_clusters) <= 10:
            colors = plt.cm.tab10(np.linspace(0, 1, len(unique_clusters)))
        else:
            colors = plt.cm.tab20(np.linspace(0, 1, len(unique_clusters)))

        cluster_to_color = {cluster: colors[i] for i, cluster in enumerate(unique_clusters)}

        # Рисуем точки
        all_x = embeddings_2d[:, 0]
        all_y = embeddings_2d[:, 1]
        all_colors = [cluster_to_color[cluster] for cluster in cluster_labels]

        # Рисуем все точки одним вызовом (гораздо быстрее)
        self.scatter_plot = self.ax.scatter(
            all_x, all_y,
            c=all_colors,
            alpha=0.6,
            s=20,
            edgecolors='white',
            linewidth=0.5,
            picker=True,
            pickradius=5
        )

        # Настройка осей
        self.ax.set_aspect('auto')

        x_min, x_max = embeddings_2d[:, 0].min(), embeddings_2d[:, 0].max()
        y_min, y_max = embeddings_2d[:, 1].min(), embeddings_2d[:, 1].max()
        x_padding = (x_max - x_min) * 0.1
        y_padding = (y_max - y_min) * 0.1

        self.ax.set_xlim(x_min - x_padding, x_max + x_padding)
        self.ax.set_ylim(y_min - y_padding, y_max + y_padding)

        self.ax.set_title("Карта эмбеддингов (t-SNE)", fontsize=8, fontweight='bold')
        self.ax.tick_params(axis='both', labelsize=5)

        # Легенда
        self.figure.subplots_adjust(right=0.75)

        legend_elements = []
        for cluster in unique_clusters:
            color = cluster_to_color[cluster]
            legend_elements.append(
                mpatches.Patch(color=color, label=str(cluster), alpha=0.6)
            )

        legend = self.ax.legend(
            handles=legend_elements,
            loc='center left',
            bbox_to_anchor=(1.02, 0.5),
            fontsize=5,
            framealpha=0.9,
            title_fontsize=6
        )

        legend.get_frame().set_linewidth(0.5)
        legend.get_frame().set_facecolor('#f5f5f5')
        legend.get_frame().set_edgecolor('#cccccc')

        # Сетка и границы
        self.ax.grid(True, alpha=0.2, linestyle='--', linewidth=0.3)
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.spines['bottom'].set_color('#cccccc')
        self.ax.spines['left'].set_color('#cccccc')

        self.draw()

        self.legend = legend  # сохраняем легенду
        self.draw_idle()

    #обработка наведения мыши на позицию
    def on_hover(self, event):
        if event.inaxes != self.ax:
            self.unhighlight_point()
            QToolTip.hideText()
            return

        if self.kdtree is None:
            return

        # Находим ближайшую точку
        ind = self.find_closest_point(event.xdata, event.ydata)

        if ind is not None and self.current_hover_index != ind:
            self.current_hover_index = ind
            self.highlight_point(ind)
            if self.images_list and ind < len(self.images_list):
                img = self.images_list[ind]
                cluster = self.cluster_labels[ind]

                if cluster == "Аномалии":
                    tooltip_text = f"Файл: {img.filename}\nАномалия"
                else:
                    tooltip_text = f"Файл: {img.filename}\nКластер: {cluster}"
                if hasattr(img, 'width') and hasattr(img, 'height'):
                    tooltip_text += f"\nРазмер: {img.width}x{img.height}"

                QToolTip.showText(QCursor.pos(), tooltip_text, self)
        else:
            if self.current_hover_index != ind:
                self.unhighlight_point()
                QToolTip.hideText()

    #поиск индекса ближайшей точки с использованием KDTree
    def find_closest_point(self, x, y, max_distance=10):
        if self.kdtree is None or len(self.embeddings_2d) == 0:
            return None

        # Ищем ближайшую точку
        dist, idx = self.kdtree.query([x, y])

        # Проверяем, что расстояние не слишком большое
        if isinstance(idx, np.integer) or isinstance(idx, int):
            closest_idx = idx
        else:
            closest_idx = idx[0] if len(idx) > 0 else None
        if closest_idx is not None and dist < max_distance:
            return closest_idx
        return None


    def unhighlight_point(self):
        try:
            if self.highlight_artist is not None:
                # Проверяем, находится ли объект еще на графике
                if self.highlight_artist.axes is not None:
                    self.highlight_artist.remove()
                self.highlight_artist = None
        except (ValueError, AttributeError):
            # Игнорируем ошибки удаления
            self.highlight_artist = None

        #self.draw()

    def highlight_point(self, index):
        self.unhighlight_point()

        x, y = self.embeddings_2d[index]

        self.highlight_artist = self.ax.scatter(
            x, y,
            c='red',
            s=60,
            edgecolors='black',
            linewidth=1.5,
            alpha=0.8,
            zorder=10
        )
        self.draw_idle()



