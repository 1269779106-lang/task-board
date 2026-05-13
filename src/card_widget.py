# 任务看板 - 任务卡片组件
# 圆角卡片、阴影效果、优先级颜色、悬停动画、拖拽支持

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGraphicsDropShadowEffect,
    QMenu, QApplication,
)
from PySide6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve, QPoint, Signal, QMimeData,
)
from PySide6.QtGui import QColor, QPainter, QPainterPath, QFont, QDrag, QPixmap, QAction

from models import Task, Category, get_all_categories


# 优先级颜色映射
PRIORITY_COLORS = {
    "high": "#ef4444",    # 红色 - 高优先级
    "medium": "#f59e0b",  # 橙色 - 中优先级
    "low": "#22c55e",     # 绿色 - 低优先级
}

# 优先级标签文本
PRIORITY_LABELS = {
    "high": "紧急",
    "medium": "普通",
    "low": "低",
}

# 状态列标题和颜色
STATUS_CONFIG = {
    "todo":  {"title": "📥 待办",   "color": "#6366f1", "bg": "#eef2ff"},
    "doing": {"title": "🔄 进行中", "color": "#f59e0b", "bg": "#fffbeb"},
    "done":  {"title": "✅ 已完成",  "color": "#22c55e", "bg": "#f0fdf4"},
}


class TaskCard(QWidget):
    """任务卡片组件：圆角、阴影、悬停动画、拖拽"""

    # 信号：任务被点击、右键菜单操作
    clicked = Signal(int)          # 发送任务 ID
    edit_requested = Signal(int)   # 请求编辑
    delete_requested = Signal(int) # 请求删除
    status_changed = Signal(int, str)  # 任务ID, 新状态

    def __init__(self, task: Task, category: Category = None, parent=None):
        super().__init__(parent)
        self.task = task
        self.category = category
        self._hovered = False
        self._drag_start_pos = None

        self.setFixedSize(260, 130)
        self.setCursor(Qt.PointingHandCursor)
        self.setMouseTracking(True)

        # 阴影效果
        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(12)
        self._shadow.setOffset(0, 2)
        self._shadow.setColor(QColor(0, 0, 0, 40))
        self.setGraphicsEffect(self._shadow)

        self._build_ui()

    def _build_ui(self):
        """构建卡片内部布局"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(6)

        # 第一行：优先级标签 + 重要星标
        top_row = QHBoxLayout()
        top_row.setSpacing(6)

        # 优先级圆点 + 文字
        p_color = PRIORITY_COLORS.get(self.task.priority, "#999")
        p_label = QLabel(f"● {PRIORITY_LABELS.get(self.task.priority, '普通')}")
        p_label.setStyleSheet(f"""
            color: {p_color};
            font-size: 11px;
            font-weight: 600;
            background: transparent;
        """)
        top_row.addWidget(p_label)

        top_row.addStretch()

        # 重要星标
        if self.task.is_important:
            star = QLabel("⭐")
            star.setStyleSheet("background: transparent; font-size: 14px;")
            top_row.addWidget(star)

        layout.addLayout(top_row)

        # 第二行：任务标题
        title = QLabel(self.task.title)
        title.setWordWrap(True)
        title.setStyleSheet("""
            color: #1e293b;
            font-size: 14px;
            font-weight: 600;
            background: transparent;
        """)
        # 已完成任务添加删除线
        if self.task.status == "done":
            title.setStyleSheet("""
                color: #94a3b8;
                font-size: 14px;
                font-weight: 600;
                background: transparent;
                text-decoration: line-through;
            """)
        layout.addWidget(title)

        # 第三行：分类标签 + 截止日期
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(8)

        # 分类标签
        if self.category:
            cat_label = QLabel(f"{self.category.icon} {self.category.name}")
            cat_label.setStyleSheet(f"""
                background: {self.category.color}20;
                color: {self.category.color};
                border-radius: 8px;
                padding: 2px 8px;
                font-size: 11px;
                font-weight: 500;
            """)
            bottom_row.addWidget(cat_label)

        bottom_row.addStretch()

        # 截止日期
        if self.task.due_date:
            from datetime import datetime
            today = datetime.now().strftime("%Y-%m-%d")
            is_overdue = self.task.due_date < today and self.task.status != "done"
            date_color = "#ef4444" if is_overdue else "#64748b"
            date_icon = "⚠️" if is_overdue else "📅"
            date_label = QLabel(f"{date_icon} {self.task.due_date}")
            date_label.setStyleSheet(f"""
                color: {date_color};
                font-size: 11px;
                background: transparent;
            """)
            bottom_row.addWidget(date_label)

        layout.addLayout(bottom_row)

        layout.addStretch()

    def paintEvent(self, event):
        """绘制圆角白色卡片背景"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        path = QPainterPath()
        rect = self.rect().adjusted(2, 2, -2, -2)
        path.addRoundedRect(rect, 12, 12)

        # 左侧优先级色条
        p_color = QColor(PRIORITY_COLORS.get(self.task.priority, "#999"))
        painter.setPen(Qt.NoPen)
        painter.setBrush(p_color)
        bar_rect = rect.adjusted(0, 8, 0, -8)
        bar_rect.setWidth(4)
        painter.drawRoundedRect(bar_rect, 2, 2)

        # 卡片背景
        bg_color = QColor("#ffffff")
        if self._hovered:
            bg_color = QColor("#f8fafc")
        if self.task.status == "done":
            bg_color = QColor("#f1f5f9")

        painter.setBrush(bg_color)
        painter.setPen(QColor("#e2e8f0"))
        painter.drawRoundedRect(rect, 12, 12)

        painter.end()

    def enterEvent(self, event):
        """鼠标进入：悬停效果"""
        self._hovered = True
        self._shadow.setBlurRadius(16)
        self._shadow.setOffset(0, 4)
        self._shadow.setColor(QColor(0, 0, 0, 60))
        self.update()

    def leaveEvent(self, event):
        """鼠标离开：恢复原状"""
        self._hovered = False
        self._shadow.setBlurRadius(12)
        self._shadow.setOffset(0, 2)
        self._shadow.setColor(QColor(0, 0, 0, 40))
        self.update()

    def mousePressEvent(self, event):
        """鼠标按下：记录位置（准备拖拽）"""
        if event.button() == Qt.LeftButton:
            self._drag_start_pos = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """鼠标移动：如果距离足够则启动拖拽"""
        if self._drag_start_pos is None:
            return
        if (event.pos() - self._drag_start_pos).manhattanLength() < 10:
            return

        # 创建拖拽对象
        drag = QDrag(self)
        mime = QMimeData()
        mime.setText(str(self.task.id))
        drag.setMimeData(mime)

        # 拖拽时显示卡片缩略图
        pixmap = self.grab()
        drag.setPixmap(pixmap.scaled(200, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        drag.setHotSpot(event.pos())

        self._drag_start_pos = None
        drag.exec(Qt.MoveAction)

    def mouseReleaseEvent(self, event):
        """鼠标释放：重置拖拽位置"""
        self._drag_start_pos = None
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        """双击：触发编辑"""
        if event.button() == Qt.LeftButton:
            self.edit_requested.emit(self.task.id)

    def contextMenuEvent(self, event):
        """右键菜单"""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background: white;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 4px;
                font-size: 13px;
            }
            QMenu::item {
                padding: 8px 24px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background: #f1f5f9;
            }
        """)

        edit_action = QAction("✏️ 编辑", self)
        edit_action.triggered.connect(lambda: self.edit_requested.emit(self.task.id))
        menu.addAction(edit_action)

        # 重要性切换
        star_text = "☆ 取消重要" if self.task.is_important else "⭐ 设为重要"
        star_action = QAction(star_text, self)
        star_action.triggered.connect(self._toggle_important)
        menu.addAction(star_action)

        menu.addSeparator()

        # 状态切换子菜单
        status_menu = menu.addMenu("📋 移动到")
        for status_key, config in STATUS_CONFIG.items():
            if status_key != self.task.status:
                action = QAction(config["title"], self)
                action.triggered.connect(
                    lambda checked, s=status_key: self.status_changed.emit(self.task.id, s)
                )
                status_menu.addAction(action)

        menu.addSeparator()

        delete_action = QAction("🗑️ 删除", self)
        delete_action.triggered.connect(lambda: self.delete_requested.emit(self.task.id))
        menu.addAction(delete_action)

        menu.exec(event.globalPos() if hasattr(event, 'globalPos') else event.globalPosition().toPoint())

    def _toggle_important(self):
        """切换任务重要性"""
        from models import update_task
        update_task(self.task.id, is_important=not self.task.is_important)
        self.task.is_important = not self.task.is_important
        self.update()
