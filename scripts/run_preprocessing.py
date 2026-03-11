"""
运行数据预处理脚本
"""

import argparse
import yaml
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data import build_and_save_data


def main():
    parser = argparse.ArgumentParser(description='数据预处理')
    parser.add_argument('--config', type=str, default='config/default.yaml',
                        help='配置文件路径')
    args = parser.parse_args()

    # 加载配置
    with open(args.config, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # 获取输出路径
    output_path = config.get('data', {}).get('processed_data_path', './data/processed/data.pt')

    print(f"开始数据预处理...")
    print(f"配置文件: {args.config}")
    print(f"输出路径: {output_path}")

    # 执行预处理
    build_and_save_data(output_path, config)

    print("数据预处理完成!")


if __name__ == '__main__':
    main()
