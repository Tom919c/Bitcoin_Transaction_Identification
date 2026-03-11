"""
启动可视化界面脚本
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from interface.main_window import run_app


def main():
    print("启动比特币交易节点分类系统...")
    run_app()


if __name__ == '__main__':
    main()
