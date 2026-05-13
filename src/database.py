# 任务看板 - 数据库管理模块
# 负责 SQLite 数据库的初始化、表创建和连接管理

import sqlite3
import os
from pathlib import Path


# 数据库文件路径：存储在用户目录下
DB_DIR = Path(os.environ.get("APPDATA", "~")) / "TaskBoard"
DB_PATH = DB_DIR / "tasks.db"


def get_connection() -> sqlite3.Connection:
    """获取数据库连接，返回 Row 模式的连接对象"""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row  # 查询结果可用列名访问
    conn.execute("PRAGMA journal_mode=WAL")   # 写入性能优化
    conn.execute("PRAGMA foreign_keys=ON")     # 启用外键约束
    return conn


def init_db():
    """初始化数据库，创建所有表结构"""
    conn = get_connection()
    cursor = conn.cursor()

    # 分类表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL UNIQUE,
            color       TEXT    NOT NULL DEFAULT '#6366f1',
            icon        TEXT    NOT NULL DEFAULT '📁',
            position    INTEGER NOT NULL DEFAULT 0,
            created_at  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
        )
    """)

    # 任务表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            title         TEXT    NOT NULL,
            description   TEXT    DEFAULT '',
            status        TEXT    NOT NULL DEFAULT 'todo'
                          CHECK (status IN ('todo', 'doing', 'done')),
            priority      TEXT    NOT NULL DEFAULT 'medium'
                          CHECK (priority IN ('low', 'medium', 'high')),
            category_id   INTEGER DEFAULT NULL,
            due_date      TEXT    DEFAULT NULL,
            reminder_time TEXT    DEFAULT NULL,
            is_important  INTEGER NOT NULL DEFAULT 0,
            position      INTEGER NOT NULL DEFAULT 0,
            created_at    TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
            updated_at    TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
        )
    """)

    # 索引：加速常用查询
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_tasks_category ON tasks(category_id)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_tasks_due ON tasks(due_date)
    """)

    # 插入默认分类（如果表为空）
    cursor.execute("SELECT COUNT(*) FROM categories")
    if cursor.fetchone()[0] == 0:
        default_categories = [
            ("工作", "#ef4444", "💼", 0),
            ("学习", "#3b82f6", "📚", 1),
            ("生活", "#22c55e", "🏠", 2),
            ("其他", "#8b5cf6", "📌", 3),
        ]
        cursor.executemany(
            "INSERT INTO categories (name, color, icon, position) VALUES (?, ?, ?, ?)",
            default_categories,
        )

    conn.commit()
    conn.close()
