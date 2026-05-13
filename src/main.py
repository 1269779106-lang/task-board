# 任务看板 - 主入口
# 初始化数据库、启动应用

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont
from database import init_db
from main_window import MainWindow


def main():
    """主函数：初始化数据库 -> 启动 GUI"""
    # 初始化数据库和表结构
    init_db()

    # 创建应用
    app = QApplication(sys.argv)
    app.setApplicationName("任务看板")
    app.setStyle("Fusion")  # 跨平台统一样式

    # 设置默认字体
    font = QFont("Microsoft YaHei", 10)
    font.setStyleStrategy(QFont.PreferAntialias)
    app.setFont(font)

    # 创建并显示主窗口
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
