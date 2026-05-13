# 任务看板 - 对话框模块
# 添加/编辑任务弹窗、分类管理弹窗

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit,
    QComboBox, QDateEdit, QCheckBox, QPushButton, QTimeEdit,
    QGridLayout, QWidget, QMessageBox, QListWidget, QListWidgetItem,
    QColorDialog,
)
from PySide6.QtCore import Qt, QDate, QTime
from PySide6.QtGui import QColor

from models import Task, Category, get_all_categories, add_category, delete_category, update_category


class TaskDialog(QDialog):
    """添加/编辑任务的对话框"""

    def __init__(self, task: Task = None, parent=None):
        super().__init__(parent)
        self.task = task  # 编辑模式时传入已有任务
        self.result_data = None

        self.setWindowTitle("编辑任务" if task else "新建任务")
        self.setMinimumWidth(420)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self._build_ui()
        self._load_categories()
        if task:
            self._fill_data()

    def _build_ui(self):
        """构建对话框界面"""
        # 外层容器（圆角白色背景）
        self.container = QWidget(self)
        self.container.setStyleSheet("""
            QWidget {
                background: white;
                border-radius: 16px;
                border: 1px solid #e2e8f0;
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.container)

        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(14)

        # 标题
        title = QLabel("编辑任务" if self.task else "新建任务")
        title.setStyleSheet("""
            font-size: 18px;
            font-weight: 700;
            color: #1e293b;
            background: transparent;
        """)
        layout.addWidget(title)

        # 任务名称
        name_label = QLabel("任务名称 *")
        name_label.setStyleSheet("font-size: 12px; color: #64748b; font-weight: 600; background: transparent;")
        layout.addWidget(name_label)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("输入任务名称...")
        self.name_input.setStyleSheet(self._input_style())
        layout.addWidget(self.name_input)

        # 任务描述
        desc_label = QLabel("描述")
        desc_label.setStyleSheet("font-size: 12px; color: #64748b; font-weight: 600; background: transparent;")
        layout.addWidget(desc_label)
        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("添加详细描述...")
        self.desc_input.setMaximumHeight(80)
        self.desc_input.setStyleSheet(self._input_style())
        layout.addWidget(self.desc_input)

        # 优先级 + 分类（一行两列）
        row1 = QHBoxLayout()
        row1.setSpacing(12)

        # 优先级
        p_col = QVBoxLayout()
        p_label = QLabel("优先级")
        p_label.setStyleSheet("font-size: 12px; color: #64748b; font-weight: 600; background: transparent;")
        p_col.addWidget(p_label)
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["🟢 低", "🟡 普通", "🔴 紧急"])
        self.priority_combo.setCurrentIndex(1)
        self.priority_combo.setStyleSheet(self._combo_style())
        p_col.addWidget(self.priority_combo)
        row1.addLayout(p_col)

        # 分类
        c_col = QVBoxLayout()
        c_label = QLabel("分类")
        c_label.setStyleSheet("font-size: 12px; color: #64748b; font-weight: 600; background: transparent;")
        c_col.addWidget(c_label)
        self.category_combo = QComboBox()
        self.category_combo.setStyleSheet(self._combo_style())
        c_col.addWidget(self.category_combo)
        row1.addLayout(c_col)

        layout.addLayout(row1)

        # 截止日期 + 提醒时间（一行两列）
        row2 = QHBoxLayout()
        row2.setSpacing(12)

        # 截止日期
        d_col = QVBoxLayout()
        d_label = QLabel("截止日期")
        d_label.setStyleSheet("font-size: 12px; color: #64748b; font-weight: 600; background: transparent;")
        d_col.addWidget(d_label)
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_edit.setStyleSheet(self._input_style())
        d_col.addWidget(self.date_edit)
        row2.addLayout(d_col)

        # 提醒时间
        r_col = QVBoxLayout()
        r_label = QLabel("提醒时间")
        r_label.setStyleSheet("font-size: 12px; color: #64748b; font-weight: 600; background: transparent;")
        r_col.addWidget(r_label)
        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm")
        self.time_edit.setTime(QTime(9, 0))
        self.time_edit.setStyleSheet(self._input_style())
        r_col.addWidget(self.time_edit)
        row2.addLayout(r_col)

        layout.addLayout(row2)

        # 复选框行
        checks = QHBoxLayout()
        self.important_check = QCheckBox("⭐ 设为重要")
        self.important_check.setStyleSheet("font-size: 13px; background: transparent;")
        checks.addWidget(self.important_check)

        self.no_date_check = QCheckBox("无截止日期")
        self.no_date_check.setStyleSheet("font-size: 13px; background: transparent;")
        checks.addWidget(self.no_date_check)
        checks.addStretch()
        layout.addLayout(checks)

        # 按钮行
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: #f1f5f9;
                color: #475569;
                border: none;
                border-radius: 8px;
                padding: 10px 24px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover { background: #e2e8f0; }
        """)
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("保存")
        save_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6366f1, stop:1 #8b5cf6);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 32px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4f46e5, stop:1 #7c3aed);
            }
        """)
        save_btn.clicked.connect(self._on_save)

        btn_row.addStretch()
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def _load_categories(self):
        """加载分类列表到下拉框"""
        self.category_combo.addItem("无分类", None)
        for cat in get_all_categories():
            self.category_combo.addItem(f"{cat.icon} {cat.name}", cat.id)

    def _fill_data(self):
        """编辑模式：填充已有任务数据"""
        self.name_input.setText(self.task.title)
        self.desc_input.setPlainText(self.task.description)

        # 优先级
        p_map = {"low": 0, "medium": 1, "high": 2}
        self.priority_combo.setCurrentIndex(p_map.get(self.task.priority, 1))

        # 分类
        if self.task.category_id:
            for i in range(self.category_combo.count()):
                if self.category_combo.itemData(i) == self.task.category_id:
                    self.category_combo.setCurrentIndex(i)
                    break

        # 日期
        if self.task.due_date:
            self.date_edit.setDate(QDate.fromString(self.task.due_date, "yyyy-MM-dd"))
        else:
            self.no_date_check.setChecked(True)

        # 提醒时间
        if self.task.reminder_time:
            parts = self.task.reminder_time.split(" ")
            if len(parts) == 2:
                self.time_edit.setTime(QTime.fromString(parts[1], "HH:mm:ss"))

        self.important_check.setChecked(self.task.is_important)

    def _on_save(self):
        """保存按钮点击"""
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "提示", "请输入任务名称")
            return

        p_index = self.priority_combo.currentIndex()
        priority = ["low", "medium", "high"][p_index]

        cat_id = self.category_combo.currentData()
        due_date = None if self.no_date_check.isChecked() else self.date_edit.date().toString("yyyy-MM-dd")
        reminder = f"{due_date} {self.time_edit.time().toString('HH:mm:ss')}" if due_date else None

        self.result_data = {
            "title": name,
            "description": self.desc_input.toPlainText().strip(),
            "priority": priority,
            "category_id": cat_id,
            "due_date": due_date,
            "reminder_time": reminder,
            "is_important": self.important_check.isChecked(),
        }
        self.accept()

    def _input_style(self) -> str:
        return """
            QLineEdit, QDateEdit, QTimeEdit, QTextEdit {
                background: #f8fafc;
                border: 1.5px solid #e2e8f0;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
                color: #1e293b;
            }
            QLineEdit:focus, QDateEdit:focus, QTimeEdit:focus, QTextEdit:focus {
                border-color: #6366f1;
                background: white;
            }
        """

    def _combo_style(self) -> str:
        return """
            QComboBox {
                background: #f8fafc;
                border: 1.5px solid #e2e8f0;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
                color: #1e293b;
            }
            QComboBox:focus { border-color: #6366f1; background: white; }
            QComboBox::drop-down {
                border: none;
                width: 24px;
            }
            QComboBox QAbstractItemView {
                background: white;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                selection-background-color: #eef2ff;
            }
        """


class CategoryDialog(QDialog):
    """分类管理对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("管理分类")
        self.setMinimumWidth(360)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._build_ui()
        self._load_categories()

    def _build_ui(self):
        self.container = QWidget(self)
        self.container.setStyleSheet("""
            QWidget { background: white; border-radius: 16px; border: 1px solid #e2e8f0; }
        """)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.container)

        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(12)

        title = QLabel("管理分类")
        title.setStyleSheet("font-size: 18px; font-weight: 700; color: #1e293b; background: transparent;")
        layout.addWidget(title)

        self.cat_list = QListWidget()
        self.cat_list.setStyleSheet("""
            QListWidget {
                background: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 4px;
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 4px;
            }
            QListWidget::item:selected { background: #eef2ff; }
        """)
        layout.addWidget(self.cat_list)

        # 添加新分类
        add_row = QHBoxLayout()
        self.new_cat_input = QLineEdit()
        self.new_cat_input.setPlaceholderText("新分类名称...")
        self.new_cat_input.setStyleSheet("""
            QLineEdit {
                background: #f8fafc;
                border: 1.5px solid #e2e8f0;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
                color: #1e293b;
            }
            QLineEdit:focus {
                border-color: #6366f1;
                background: white;
            }
        """)
        add_row.addWidget(self.new_cat_input)

        add_btn = QPushButton("添加")
        add_btn.setStyleSheet("""
            QPushButton {
                background: #6366f1; color: white; border: none;
                border-radius: 8px; padding: 8px 16px; font-weight: 600;
            }
            QPushButton:hover { background: #4f46e5; }
        """)
        add_btn.clicked.connect(self._add_category)
        add_row.addWidget(add_btn)
        layout.addLayout(add_row)

        # 删除按钮
        del_btn = QPushButton("删除选中分类")
        del_btn.setStyleSheet("""
            QPushButton {
                background: #fef2f2; color: #ef4444; border: 1px solid #fecaca;
                border-radius: 8px; padding: 8px; font-weight: 600;
            }
            QPushButton:hover { background: #fee2e2; }
        """)
        del_btn.clicked.connect(self._delete_category)
        layout.addWidget(del_btn)

        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.setStyleSheet("""
            QPushButton {
                background: #f1f5f9; color: #475569; border: none;
                border-radius: 8px; padding: 10px; font-weight: 600;
            }
            QPushButton:hover { background: #e2e8f0; }
        """)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def _load_categories(self):
        self.cat_list.clear()
        for cat in get_all_categories():
            self.cat_list.addItem(f"{cat.icon} {cat.name}")

    def _add_category(self):
        name = self.new_cat_input.text().strip()
        if not name:
            return
        try:
            add_category(name)
            self.new_cat_input.clear()
            self._load_categories()
        except Exception:
            QMessageBox.warning(self, "提示", "分类名称已存在")

    def _delete_category(self):
        row = self.cat_list.currentRow()
        if row < 0:
            return
        cats = get_all_categories()
        if row < len(cats):
            reply = QMessageBox.question(
                self, "确认", f"确定删除分类「{cats[row].name}」？\n关联任务不会被删除。",
            )
            if reply == QMessageBox.Yes:
                delete_category(cats[row].id)
                self._load_categories()
