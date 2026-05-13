from PyQt6.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem, QStyle
from PyQt6.QtGui import QPainter, QPen, QColor, QFont, QPalette, QPixmap
from PyQt6.QtCore import Qt, QRect, QSize, QPoint
import os


class ImageDelegate(QStyledItemDelegate):
    def __init__(self, dataset_id, parent=None, search_query=None, search_mode=None):
        super().__init__(parent)
        self.thumbnail_cache = {}  # кэш для миниатюр
        self.dataset_id = dataset_id
        self.search_query = search_query
        self.search_mode = search_mode


    def paint(self, painter, option, index):
        # Сохраняем состояние
        painter.save()

        # Получаем данные
        img = index.data(Qt.ItemDataRole.UserRole)

        # Определяем, выбран ли элемент
        is_selected = option.state & QStyle.StateFlag.State_Selected

        # Рисуем фон
        if is_selected:
            painter.fillRect(option.rect, QColor("#0078d4"))
            text_color = Qt.GlobalColor.white
        else:
            painter.fillRect(option.rect, Qt.GlobalColor.transparent)
            text_color = Qt.GlobalColor.black

        #МИНИАТЮРА
        thumbnail_rect = QRect(option.rect.x() + 5, option.rect.y() + 5, 100, 80)

        if type(img) is list:
            img = img[0]
        # Загружаем миниатюру (с кэшированием)
        if img.id not in self.thumbnail_cache:
            if os.path.exists(img.filepath):
                pixmap = QPixmap(img.filepath)
                if not pixmap.isNull():
                    pixmap = pixmap.scaled(80, 80,
                                           Qt.AspectRatioMode.KeepAspectRatio,
                                           Qt.TransformationMode.SmoothTransformation)
                    self.thumbnail_cache[img.id] = pixmap
                else:
                    self.thumbnail_cache[img.id] = None
            else:
                self.thumbnail_cache[img.id] = None

        if self.thumbnail_cache[img.id]:
            painter.drawPixmap(thumbnail_rect, self.thumbnail_cache[img.id])
        else:
            # Placeholder
            painter.fillRect(thumbnail_rect, QColor("#e0e0e0"))
            painter.setPen(QColor("#999"))
            painter.drawText(thumbnail_rect, Qt.AlignmentFlag.AlignCenter, "🖼️")

        # ===== ТЕКСТОВАЯ ИНФОРМАЦИЯ =====
        text_x = option.rect.x() + 110
        text_y = option.rect.y() + 5
        text_width = option.rect.width() - 100

        # Шрифты
        title_font = QFont("Arial", 10, QFont.Weight.Bold)
        normal_font = QFont("Arial", 9)

        # 1. Имя файла
        text = img.filename
        self.draw_highlighted_textName(painter, title_font, text_color, text_x, text_y,
                                   text_width, img.filename)

        # 2. Статус
        painter.setFont(normal_font)
        status_y = text_y + 20
        status_color = QColor("green") if img.status == "quality_passed" or img.status == "uploaded" else QColor("red")
        painter.setPen(status_color if not is_selected else Qt.GlobalColor.white)
        status_rect = QRect(text_x, status_y, text_width, 18)
        status_text = f"Статус: {img.status}"
        painter.drawText(status_rect, Qt.AlignmentFlag.AlignLeft, status_text)

        # 3. Дата загрузки
        painter.setPen(text_color)
        date_y = status_y + 18
        date_rect = QRect(text_x, date_y, text_width, 18)
        date_str = img.uploaded_at[:10] if img.uploaded_at else "неизвестно"
        painter.drawText(date_rect, Qt.AlignmentFlag.AlignLeft, f"Загружено: {date_str}")

        # 4. Теги
        tags_y = date_y + 18
        tags_rect = QRect(text_x, tags_y, text_width, 18)
        tags = ','.join([tag.name for tag in img.tags_list])
        tags_str = f"Теги: {tags}" if img.tags_list else "Теги: нет"
        self.draw_highlighted_textTags(painter, tags_rect, tags_str)

        painter.restore()

    def draw_highlighted_textTags(self, painter, tags_rect, tags_str):
        if self.search_query is None or self.search_query not in tags_str or self.search_mode != "tags":
            painter.drawText(tags_rect, Qt.AlignmentFlag.AlignLeft, tags_str[:25])
        else:
            start_pos = tags_str.find(self.search_query)
            if start_pos >= 0:
                before = tags_str[:start_pos]
                match = tags_str[start_pos:start_pos + len(self.search_query)]
                after = tags_str[start_pos + len(self.search_query):]

                # Координаты для отрисовки
                x = tags_rect.x()
                y = tags_rect.y() + painter.fontMetrics().ascent()

                # Рисуем текст до подсветки
                if before:
                    painter.setPen(QColor("#666"))
                    painter.drawText(QPoint(x, y), before)
                    x += painter.fontMetrics().horizontalAdvance(before)

                # Рисуем подсвеченный текст
                if match:
                    # Желтый фон
                    match_rect = QRect(x, tags_rect.y(),
                                       painter.fontMetrics().horizontalAdvance(match),
                                       tags_rect.height())
                    painter.fillRect(match_rect, QColor(255, 235, 59))

                    # Черный текст для контраста
                    painter.setPen(QColor(0, 0, 0))
                    painter.drawText(QPoint(x, y), match)
                    x += painter.fontMetrics().horizontalAdvance(match)

                # Рисуем остаток текста
                if after:
                    painter.setPen(QColor("#666"))
                    # Обрезаем если нужно
                    remaining_width = tags_rect.width() - (x - tags_rect.x())
                    if painter.fontMetrics().horizontalAdvance(after) > remaining_width:
                        while after and painter.fontMetrics().horizontalAdvance(after + "...") > remaining_width:
                            after = after[:-1]
                        after = after + "..." if after else "..."

                    painter.drawText(QPoint(x, y), after)
            else:
                # Если не нашли - рисуем обычный текст
                painter.drawText(tags_rect, Qt.AlignmentFlag.AlignLeft, tags_str[:25])

    def draw_highlighted_textName(self, painter, title_font, text_color, text_x, text_y,
                              text_width, text):
        if self.search_query is None or self.search_query not in text or self.search_mode != "name":
            painter.setFont(title_font)
            painter.setPen(text_color)
            name_rect = QRect(text_x, text_y, text_width, 20)

            if len(text) > 20:
                file_name = f"{text[:20]}..."
            else:
                file_name = text
            painter.drawText(name_rect, Qt.AlignmentFlag.AlignLeft,
                             file_name)

        else:
            start_pos = text.find(self.search_query)
            if start_pos >= 0:
                match_text = text[start_pos:start_pos + len(self.search_query)]

                # Текст до совпадения
                before = text[:start_pos]
                # Текст после совпадения
                after = text[start_pos + len(self.search_query):]
                # Урезаем текст если слишком длинный
                if len(text) > 20:
                    # Сложная обрезка с сохранением подсветки
                    if start_pos > 20:
                        # Если совпадение далеко - показываем ... и часть текста
                        before = "..." + before[-15:] if len(before) > 15 else before
                        match_text = match_text
                        after = after[:15] + "..." if len(after) > 15 else after
                    else:
                        # Обрезаем только after
                        after = after[:20 - len(before) - len(match_text)] + "..." if len(after) > 20 - len(
                            before) - len(match_text) else after

                # Координаты для отрисовки
                painter.setFont(title_font)
                x = text_x
                y = text_y + painter.fontMetrics().ascent()

                # Рисуем текст до совпадения
                painter.setPen(text_color)
                if before:
                    painter.drawText(QPoint(x, y), before)
                    x += painter.fontMetrics().horizontalAdvance(before)

                # Рисуем подсвеченный текст
                # Сохраняем текущий цвет и устанавливаем фон
                highlight_color = QColor(255, 235, 59)  # Желтый
                # Рисуем фон под выделенным текстом
                match_rect = QRect(x, text_y,
                                   painter.fontMetrics().horizontalAdvance(match_text),
                                   20)
                painter.fillRect(match_rect, highlight_color)

                # Рисуем сам текст (черным цветом для контраста)
                painter.setPen(QColor(0, 0, 0))
                painter.drawText(QPoint(x, y), match_text)
                x += painter.fontMetrics().horizontalAdvance(match_text)

                # Рисуем текст после совпадения
                painter.setPen(text_color)
                if after:
                    painter.drawText(QPoint(x, y), after)


    def sizeHint(self, option, index):
        return QSize(300, 110)  # ширина под 2 колонки, высота