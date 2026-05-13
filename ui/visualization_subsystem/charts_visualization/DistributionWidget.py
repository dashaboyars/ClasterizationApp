import numpy as np
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QFrame
from matplotlib import pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from sklearn.manifold import TSNE

from ui.interaction_subsystem.feedback_manager import FeedbackManager
from ui.visualization_subsystem.charts_visualization.interactive_embedding_widget import InteractiveEmbeddingWidget


class DistributionWidget(QWidget):
    def __init__(self, mainWindow, parent=None):
        super().__init__(parent)
        self.mainWin = mainWindow

        #основной вертикальный layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        #карта эмбеддингов
        top_frame = QFrame()
        top_frame.setFrameStyle(QFrame.Shape.Box)
        top_frame.setStyleSheet("""
                            QFrame {
                                border: 1px solid #ccc;
                                border-radius: 8px;
                                background-color: #f5f5f5;
                            }
                        """)
        top_layout = QVBoxLayout(top_frame)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(0)

        self.embedding_canvas = InteractiveEmbeddingWidget(self)
        top_layout.addWidget(self.embedding_canvas)

        # Нижняя часть: круговая диаграмма (30% высоты)
        bottom_frame = QFrame()
        bottom_frame.setFrameStyle(QFrame.Shape.Box)
        bottom_frame.setStyleSheet("""
                    QFrame {
                        border: 1px solid #ccc;
                        border-radius: 8px;
                        background-color: #f5f5f5;
                    }
                """)
        bottom_layout = QVBoxLayout(bottom_frame)
        bottom_layout.setContentsMargins(0, 0, 0, 0)  # Убираем отступы у layout
        bottom_layout.setSpacing(0)

        self.pie_canvas = FigureCanvas(Figure(figsize=(5, 2), facecolor='#f5f5f5'))
        self.pie_ax = self.pie_canvas.figure.add_subplot(111)
        self.pie_ax.axis('equal')
        self.pie_ax.set_title("Распределение по кластерам", fontsize=8, fontweight='bold')

        bottom_layout.addWidget(self.pie_canvas)

        # Добавляем фреймы в основной layout
        main_layout.addWidget(top_frame, 5)  # 70% высоты
        main_layout.addWidget(bottom_frame, 5)  # 30% высоты

        # Данные для хранения
        self.embeddings = None
        self.cluster_labels = None

    def tsne_computation(self, embeddings, cluster_labels, progress_callback, cancel_check):

        # обновление прогресса
        if progress_callback:
            progress_callback(10, "Подготовка...")
        if cancel_check and cancel_check():
            return None

        # преобразуем в numpy массивы
        if isinstance(embeddings, list):
            embeddings = np.array(embeddings)
        if isinstance(cluster_labels, list):
            cluster_labels = np.array(cluster_labels)

        n_samples = len(embeddings)
        perplexity = min(30, n_samples - 1)

        # обновление прогресса
        if progress_callback:
            progress_callback(30, "Расчет tsne...")
        if cancel_check and cancel_check():
            return None

        tsne = TSNE(n_components=2, random_state=42, perplexity=perplexity, max_iter=300,
                    learning_rate='auto',
                    init='pca',  # PCA инициализация быстрее
                    method='barnes_hut',  # Быстрый алгоритм
                    angle=0.5,  # Точность/скорость компромисс
                    n_jobs=-1)
        embeddings_2d = tsne.fit_transform(embeddings)

        # обновление прогресса
        if progress_callback:
            progress_callback(100, "Завершено!")
        if cancel_check and cancel_check():
            return None

        return (embeddings_2d, cluster_labels)


    def update_embedding_map(self, embeddings, cluster_labels):
        if not embeddings or not cluster_labels:
            FeedbackManager.NoImages_Warning(self.mainWin)
            if self.embedding_canvas:
                self.embedding_canvas.clear_map()
            return

        if np.all(embeddings == embeddings[0]):
            FeedbackManager.AllImagesSimilar_Warning(self.mainWin)
            if self.embedding_canvas:
                self.embedding_canvas.clear_map()
            return

        #ЗАПУСК В ФОНОВОМ ПОТОКЕ
        progress_id = FeedbackManager.ShowProgress_OnTSNE(self.mainWin)
        def tsne_task(progress_callback, cancel_check):
            return self.tsne_computation(embeddings, cluster_labels, progress_callback, cancel_check)
        self.mainWin.Start_Thread(tsne_task, "tsne", progress_id)



    def on_tsneTask_finished(self, result, progress_id):
        self.mainWin.progress_bars[progress_id].close()
        del self.mainWin.progress_bars[progress_id]
        del self.mainWin.threads[progress_id]

        embeddings_2d, cluster_labels= result

        # Получаем список изображений для текущей сессии
        images_list = []
        if self.mainWin.currentSession:
            for cluster in self.mainWin.currentSession.clusters_list:
                images_list.extend(cluster.images_list)
            if self.mainWin.currentSession.anomaly_group:
                images_list.extend(self.mainWin.currentSession.anomaly_group.images_list)

        #отрисовываем интерактивную карту
        self.embedding_canvas.draw_points(embeddings_2d, cluster_labels, images_list)

    def update_pie_chart(self, cluster_sizes):
        self.pie_ax.clear()
        labels = []
        sizes = []

        for cluster_name, size in cluster_sizes.items():
            labels.append(cluster_name)
            sizes.append(size)

        colors = plt.cm.tab10(np.linspace(0, 1, len(sizes)))

        wedges, texts, autotexts = self.pie_ax.pie(
            sizes,
            labels=labels,
            colors=colors,
            autopct='%1.1f%%',  # Показывать проценты
            startangle=90,  # Начинать с 90 градусов
            explode=[0.02] * len(sizes), # Небольшое разделение
            textprops={'fontsize': 6}
        )

        self.pie_ax.set_title("Распределение по кластерам", fontsize=8, fontweight='bold')
        self.pie_ax.axis('off')
        self.pie_canvas.draw()
