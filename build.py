# 任务看板 - 打包脚本
# 使用 PyInstaller 将项目打包成单个 exe 文件

import subprocess
import sys


def build():
    """执行 PyInstaller 打包命令"""
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--noconsole",
        "--name", "TaskBoard",
        "--paths", "src",
        "--clean",
        "src/main.py",
    ]
    print(f"执行: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)
    print("\n打包完成！exe 位于: dist/TaskBoard.exe")


if __name__ == "__main__":
    build()
