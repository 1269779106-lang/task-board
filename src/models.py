# 任务看板 - 数据模型层
# 定义 Task、Category 数据类和所有 CRUD 操作

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from database import get_connection


@dataclass
class Category:
    """分类数据类"""
    id: int = 0
    name: str = ""
    color: str = "#6366f1"
    icon: str = "📁"
    position: int = 0
    created_at: str = ""

    @staticmethod
    def from_row(row) -> "Category":
        """从数据库行创建 Category 对象"""
        return Category(
            id=row["id"], name=row["name"], color=row["color"],
            icon=row["icon"], position=row["position"],
            created_at=row["created_at"],
        )


@dataclass
class Task:
    """任务数据类"""
    id: int = 0
    title: str = ""
    description: str = ""
    status: str = "todo"        # todo / doing / done
    priority: str = "medium"    # low / medium / high
    category_id: Optional[int] = None
    due_date: Optional[str] = None
    reminder_time: Optional[str] = None
    is_important: bool = False
    position: int = 0
    created_at: str = ""
    updated_at: str = ""

    @staticmethod
    def from_row(row) -> "Task":
        """从数据库行创建 Task 对象"""
        return Task(
            id=row["id"], title=row["title"], description=row["description"],
            status=row["status"], priority=row["priority"],
            category_id=row["category_id"], due_date=row["due_date"],
            reminder_time=row["reminder_time"],
            is_important=bool(row["is_important"]),
            position=row["position"],
            created_at=row["created_at"], updated_at=row["updated_at"],
        )


# ─── 分类 CRUD ─────────────────────────────────────────────

def get_all_categories() -> list[Category]:
    """获取所有分类，按 position 排序"""
    conn = get_connection()
    rows = conn.execute("SELECT * FROM categories ORDER BY position").fetchall()
    conn.close()
    return [Category.from_row(r) for r in rows]


def add_category(name: str, color: str = "#6366f1", icon: str = "📁") -> int:
    """添加分类，返回新分类 ID"""
    conn = get_connection()
    max_pos = conn.execute("SELECT COALESCE(MAX(position), 0) FROM categories").fetchone()[0]
    cursor = conn.execute(
        "INSERT INTO categories (name, color, icon, position) VALUES (?, ?, ?, ?)",
        (name, color, icon, max_pos + 1),
    )
    conn.commit()
    conn.close()
    return cursor.lastrowid


def update_category(cat_id: int, name: str = None, color: str = None, icon: str = None):
    """更新分类信息"""
    conn = get_connection()
    if name is not None:
        conn.execute("UPDATE categories SET name=? WHERE id=?", (name, cat_id))
    if color is not None:
        conn.execute("UPDATE categories SET color=? WHERE id=?", (color, cat_id))
    if icon is not None:
        conn.execute("UPDATE categories SET icon=? WHERE id=?", (icon, cat_id))
    conn.commit()
    conn.close()


def delete_category(cat_id: int):
    """删除分类，关联任务的 category_id 会自动置 NULL"""
    conn = get_connection()
    conn.execute("DELETE FROM categories WHERE id=?", (cat_id,))
    conn.commit()
    conn.close()


# ─── 任务 CRUD ─────────────────────────────────────────────

def get_tasks(status: str = None, category_id: int = None,
              is_important: bool = None, due_date: str = None) -> list[Task]:
    """查询任务，支持按状态、分类、重要性、日期过滤"""
    conn = get_connection()
    sql = "SELECT * FROM tasks WHERE 1=1"
    params = []
    if status:
        sql += " AND status=?"
        params.append(status)
    if category_id is not None:
        sql += " AND category_id=?"
        params.append(category_id)
    if is_important is not None:
        sql += " AND is_important=?"
        params.append(int(is_important))
    if due_date:
        sql += " AND due_date=?"
        params.append(due_date)
    sql += " ORDER BY position, created_at DESC"
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [Task.from_row(r) for r in rows]


def get_task_by_id(task_id: int) -> Optional[Task]:
    """根据 ID 获取单个任务"""
    conn = get_connection()
    row = conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
    conn.close()
    return Task.from_row(row) if row else None


def add_task(title: str, status: str = "todo", priority: str = "medium",
             category_id: int = None, due_date: str = None,
             reminder_time: str = None, is_important: bool = False,
             description: str = "") -> int:
    """添加任务，返回新任务 ID"""
    conn = get_connection()
    max_pos = conn.execute(
        "SELECT COALESCE(MAX(position), 0) FROM tasks WHERE status=?", (status,)
    ).fetchone()[0]
    cursor = conn.execute(
        """INSERT INTO tasks (title, description, status, priority, category_id,
           due_date, reminder_time, is_important, position)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (title, description, status, priority, category_id,
         due_date, reminder_time, int(is_important), max_pos + 1),
    )
    conn.commit()
    conn.close()
    return cursor.lastrowid


def update_task(task_id: int, **kwargs):
    """更新任务字段，支持任意字段更新"""
    if not kwargs:
        return
    conn = get_connection()
    # 自动更新 updated_at 时间戳
    kwargs["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # 布尔值转整数
    if "is_important" in kwargs:
        kwargs["is_important"] = int(kwargs["is_important"])
    sets = ", ".join(f"{k}=?" for k in kwargs)
    values = list(kwargs.values()) + [task_id]
    conn.execute(f"UPDATE tasks SET {sets} WHERE id=?", values)
    conn.commit()
    conn.close()


def delete_task(task_id: int):
    """删除任务"""
    conn = get_connection()
    conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))
    conn.commit()
    conn.close()


def move_task(task_id: int, new_status: str, new_position: int = 0):
    """移动任务到新状态列（拖拽时调用）"""
    conn = get_connection()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        "UPDATE tasks SET status=?, position=?, updated_at=? WHERE id=?",
        (new_status, new_position, now, task_id),
    )
    conn.commit()
    conn.close()


def get_task_count_by_status() -> dict[str, int]:
    """获取各状态的任务数量"""
    conn = get_connection()
    rows = conn.execute(
        "SELECT status, COUNT(*) as cnt FROM tasks GROUP BY status"
    ).fetchall()
    conn.close()
    result = {"todo": 0, "doing": 0, "done": 0}
    for r in rows:
        result[r["status"]] = r["cnt"]
    return result


def get_overdue_tasks() -> list[Task]:
    """获取所有已过期未完成的任务"""
    conn = get_connection()
    today = datetime.now().strftime("%Y-%m-%d")
    rows = conn.execute(
        "SELECT * FROM tasks WHERE due_date < ? AND status != 'done' ORDER BY due_date",
        (today,),
    ).fetchall()
    conn.close()
    return [Task.from_row(r) for r in rows]


def get_tasks_with_reminder() -> list[Task]:
    """获取所有设置了提醒且未完成的任务"""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM tasks WHERE reminder_time IS NOT NULL AND status != 'done'"
    ).fetchall()
    conn.close()
    return [Task.from_row(r) for r in rows]
