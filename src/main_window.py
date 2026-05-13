# 任务看板 - 主窗口
# 三列看板布局、拖拽支持、添加/编辑/删除任务、侧边栏分类筛选

from datetime import datetime
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QMessageBox, QSizePolicy, QGraphicsDropShadowEffect,
    QListWidget, QListWidgetItem, QSplitter,
)
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QColor, QIcon, QFont, QAction

from models import (
    Task, Category, get_tasks, get_task_by_id, add_task, update_task,
    delete_task, move_task, get_all_categories, get_task_count_by_status,
)
from card_widget import TaskCard, STATUS_CONFIG
from dialogs import TaskDialog, CategoryDialog


class ColumnWidget(QFrame):
    """看板中的单列（待办/进行中/已完成）"""

    def __init__(self, status: str, parent=None):
        super().__init__(parent)
        self.status = status
        self.config = STATUS_CONFIG[status]
        self.cards: list[TaskCard] = []
        self.setAcceptDrops(True)

        self._build_ui()

    def _build_ui(self):
        """构建列布局"""
        self.setStyleSheet(f"""
            QFrame {{
                background: {self.config['bg']};
                border-radius: 16px;
                border: 1px solid #e2e8f0;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 14, 12, 12)
        layout.setSpacing(10)

        # 列头
        header = QHBoxLayout()
        title = QLabel(self.config["title"])
        title.setStyleSheet(f"""
            font-size: 15px;
            font-weight: 700;
            color: {self.config['color']};
            background: transparent;
        """)
        header.addWidget(title)

        self.count_label = QLabel("0")
        self.count_label.setStyleSheet(f"""
            background: {self.config['color']}20;
            color: {self.config['color']};
            border-radius: 10px;
            padding: 2px 8px;
            font-size: 12px;
            font-weight: 600;
        """)
        header.addWidget(self.count_label)
        header.addStretch()
        layout.addLayout(header)

        # 可滚动的卡片区域
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
            QScrollBar:vertical {
                background: transparent;
                width: 6px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #cbd5e1;
                border-radius: 3px;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
        """)

        self.card_container = QWidget()
        self.card_container.setStyleSheet("background: transparent;")
        self.card_layout = QVBoxLayout(self.card_container)
        self.card_layout.setContentsMargins(0, 0, 0, 0)
        self.card_layout.setSpacing(8)
        self.card_layout.addStretch()

        self.scroll.setWidget(self.card_container)
        layout.addWidget(self.scroll)

    def add_card(self, card: TaskCard):
        """添加卡片到列中"""
        self.cards.append(card)
        # 插入到 stretch 之前
        self.card_layout.insertWidget(self.card_layout.count() - 1, card)

    def clear_cards(self):
        """清空所有卡片"""
        for card in self.cards:
            card.setParent(None)
            card.deleteLater()
        self.cards.clear()

    def update_count(self, count: int):
        """更新计数标签"""
        self.count_label.setText(str(count))

    def dragEnterEvent(self, event):
        """拖拽进入：接受事件"""
        if event.mimeData().hasText():
            event.acceptProposedAction()
            self.setStyleSheet(f"""
                QFrame {{
                    background: {self.config['bg']};
                    border-radius: 16px;
                    border: 2px dashed {self.config['color']};
                }}
            """)

    def dragLeaveEvent(self, event):
        """拖拽离开：恢复样式"""
        self.setStyleSheet(f"""
            QFrame {{
                background: {self.config['bg']};
                border-radius: 16px;
                border: 1px solid #e2e8f0;
            }}
        """)

    def dropEvent(self, event):
        """拖拽放下：移动任务到本列"""
        if event.mimeData().hasText():
            try:
                task_id = int(event.mimeData().text())
            except (ValueError, TypeError):
                return
            # 获取当前列中最大 position
            tasks_in_col = get_tasks(status=self.status)
            max_pos = max((t.position for t in tasks_in_col), default=0)
            move_task(task_id, self.status, max_pos + 1)
            event.acceptProposedAction()
            # 恢复样式并刷新
            self.setStyleSheet(f"""
                QFrame {{
                    background: {self.config['bg']};
                    border-radius: 16px;
                    border: 1px solid #e2e8f0;
                }}
            """)
            # 通知主窗口刷新
            main = self.window()
            if hasattr(main, 'refresh_board'):
                main.refresh_board()


# 需要导入 Signal
from PySide6.QtCore import Signal as _Signal


class MainWindow(QMainWindow):
    """任务看板主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("📋 任务看板")
        self.setMinimumSize(1000, 650)
        self.resize(1100, 700)

        # 当前筛选状态
        self._filter_category_id = None

        self._build_ui()
        self._apply_global_style()
        self.refresh_board()

        # 提醒定时器：每30秒检查一次
        self._reminder_timer = QTimer(self)
        self._reminder_timer.timeout.connect(self._check_reminders)
        self._reminder_timer.start(30000)

    def _build_ui(self):
        """构建主界面"""
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── 顶部标题栏 ──────────────────────────────────
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6366f1, stop:0.5 #8b5cf6, stop:1 #a78bfa);
                border: none;
            }
        """)
        header.setFixedHeight(64)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(24, 0, 24, 0)

        app_title = QLabel("📋 任务看板")
        app_title.setStyleSheet("""
            color: white;
            font-size: 20px;
            font-weight: 700;
            background: transparent;
        """)
        h_layout.addWidget(app_title)

        h_layout.addStretch()

        # 统计信息
        self.stats_label = QLabel("")
        self.stats_label.setStyleSheet("color: rgba(255,255,255,0.85); font-size: 13px; background: transparent;")
        h_layout.addWidget(self.stats_label)

        h_layout.addSpacing(16)

        # 管理分类按钮
        cat_btn = QPushButton("📁 分类")
        cat_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.2);
                color: white;
                border: 1px solid rgba(255,255,255,0.3);
                border-radius: 8px;
                padding: 6px 16px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover { background: rgba(255,255,255,0.3); }
        """)
        cat_btn.clicked.connect(self._open_category_manager)
        h_layout.addWidget(cat_btn)

        h_layout.addSpacing(8)

        # 添加任务按钮
        add_btn = QPushButton("+ 新建任务")
        add_btn.setStyleSheet("""
            QPushButton {
                background: white;
                color: #6366f1;
                border: none;
                border-radius: 8px;
                padding: 6px 20px;
                font-size: 13px;
                font-weight: 700;
            }
            QPushButton:hover { background: #f0f0ff; }
        """)
        add_btn.clicked.connect(self._add_task)
        h_layout.addWidget(add_btn)

        main_layout.addWidget(header)

        # ── 分类筛选栏 ──────────────────────────────────
        filter_bar = QFrame()
        filter_bar.setStyleSheet("QFrame { background: #f8fafc; border: none; border-bottom: 1px solid #e2e8f0; }")
        filter_bar.setFixedHeight(44)
        self._filter_layout = QHBoxLayout(filter_bar)
        self._filter_layout.setContentsMargins(24, 0, 24, 0)
        self._filter_layout.setSpacing(8)

        f_label = QLabel("筛选：")
        f_label.setStyleSheet("color: #64748b; font-size: 12px; font-weight: 600; background: transparent;")
        self._filter_layout.addWidget(f_label)

        # "全部" 按钮
        self.filter_all_btn = QPushButton("全部")
        self.filter_all_btn.setCheckable(True)
        self.filter_all_btn.setChecked(True)
        self.filter_all_btn.setStyleSheet(self._filter_btn_style(True))
        self.filter_all_btn.clicked.connect(lambda: self._set_filter(None))
        self._filter_layout.addWidget(self.filter_all_btn)

        self._filter_buttons = [self.filter_all_btn]

        # 动态分类按钮
        self._build_filter_buttons()

        self._filter_layout.addStretch()
        main_layout.addWidget(filter_bar)

        # ── 看板主体（三列） ──────────────────────────────
        board = QWidget()
        board.setStyleSheet("background: #f1f5f9;")
        board_layout = QHBoxLayout(board)
        board_layout.setContentsMargins(20, 16, 20, 16)
        board_layout.setSpacing(16)

        self.columns: dict[str, ColumnWidget] = {}
        for status in ["todo", "doing", "done"]:
            col = ColumnWidget(status)
            self.columns[status] = col
            board_layout.addWidget(col)

        main_layout.addWidget(board)

    def _build_filter_buttons(self):
        """构建分类筛选按钮"""
        # 清理旧按钮
        for btn in getattr(self, '_cat_filter_btns', []):
            btn.setParent(None)
            btn.deleteLater()
        self._cat_filter_btns = []

        for cat in get_all_categories():
            btn = QPushButton(f"{cat.icon} {cat.name}")
            btn.setCheckable(True)
            btn.setStyleSheet(self._filter_btn_style(False))
            btn.clicked.connect(lambda checked, cid=cat.id: self._set_filter(cid))
            self._filter_layout.addWidget(btn)
            self._cat_filter_btns.append(btn)

    def _set_filter(self, category_id):
        """设置分类筛选"""
        self._filter_category_id = category_id
        # 更新按钮状态
        self.filter_all_btn.setChecked(category_id is None)
        self.filter_all_btn.setStyleSheet(self._filter_btn_style(category_id is None))
        for btn in self._cat_filter_btns:
            cat = [c for c in get_all_categories() if f"{c.icon} {c.name}" == btn.text()]
            is_checked = cat and cat[0].id == category_id
            btn.setChecked(is_checked)
            btn.setStyleSheet(self._filter_btn_style(is_checked))
        self.refresh_board()

    def _filter_btn_style(self, checked: bool) -> str:
        if checked:
            return """
                QPushButton {
                    background: #6366f1; color: white; border: none;
                    border-radius: 6px; padding: 4px 14px; font-size: 12px; font-weight: 600;
                }
            """
        return """
            QPushButton {
                background: white; color: #64748b; border: 1px solid #e2e8f0;
                border-radius: 6px; padding: 4px 14px; font-size: 12px; font-weight: 600;
            }
            QPushButton:hover { background: #f1f5f9; }
        """

    def refresh_board(self):
        """刷新看板：重新加载所有任务卡片"""
        counts = get_task_count_by_status()
        total = sum(counts.values())

        for status, col in self.columns.items():
            col.clear_cards()
            tasks = get_tasks(status=status, category_id=self._filter_category_id)
            col.update_count(len(tasks))

            for task in tasks:
                cat = None
                if task.category_id:
                    cats = get_all_categories()
                    cat = next((c for c in cats if c.id == task.category_id), None)

                card = TaskCard(task, cat)
                card.edit_requested.connect(self._edit_task)
                card.delete_requested.connect(self._delete_task)
                card.status_changed.connect(self._move_task)
                col.add_card(card)

        # 更新统计
        self.stats_label.setText(f"共 {total} 个任务 | 待办 {counts['todo']} | 进行中 {counts['doing']} | 已完成 {counts['done']}")

    def _add_task(self):
        """添加新任务"""
        dialog = TaskDialog(parent=self)
        if dialog.exec() == TaskDialog.Accepted and dialog.result_data:
            data = dialog.result_data
            add_task(**data)
            self.refresh_board()

    def _edit_task(self, task_id: int):
        """编辑任务"""
        task = get_task_by_id(task_id)
        if not task:
            return
        dialog = TaskDialog(task=task, parent=self)
        if dialog.exec() == TaskDialog.Accepted and dialog.result_data:
            update_task(task_id, **dialog.result_data)
            self.refresh_board()

    def _delete_task(self, task_id: int):
        """删除任务"""
        task = get_task_by_id(task_id)
        if not task:
            return
        reply = QMessageBox.question(
            self, "确认删除", f"确定删除任务「{task.title}」？",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            delete_task(task_id)
            self.refresh_board()

    def _move_task(self, task_id: int, new_status: str):
        """移动任务到新状态"""
        move_task(task_id, new_status)
        self.refresh_board()

    def _open_category_manager(self):
        """打开分类管理对话框"""
        dialog = CategoryDialog(parent=self)
        dialog.exec()
        # 刷新分类筛选按钮和看板
        self._build_filter_buttons()
        self.refresh_board()

    def _check_reminders(self):
        """检查是否有需要提醒的任务"""
        from models import get_tasks_with_reminder
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        for task in get_tasks_with_reminder():
            if task.reminder_time and task.reminder_time[:16] == now:
                self._show_reminder(task)

    def _show_reminder(self, task: Task):
        """显示提醒弹窗"""
        msg = QMessageBox(self)
        msg.setWindowTitle("⏰ 任务提醒")
        msg.setText(f"<b>{task.title}</b>")
        if task.description:
            msg.setInformativeText(task.description)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec()

    def _apply_global_style(self):
        """应用全局样式"""
        self.setStyleSheet("""
            QMainWindow { background: #f1f5f9; }
            QToolTip {
                background: #1e293b;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 12px;
            }
        """)
