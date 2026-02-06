#!/usr/bin/env python3
"""
下载标准入侵检测数据集
UNSW-NB15 和 NSL-KDD
"""

import urllib.request
import os
import zipfile
import gzip
import shutil

DATASETS_DIR = os.path.join(os.path.dirname(__file__), '..', 'datasets')
os.makedirs(DATASETS_DIR, exist_ok=True)

# UNSW-NB15 下载地址
UNSW_URLS = {
    'UNSW-NB15_1.csv': 'https://www.unsw.edu.au/content/dam/unsw/administrative/dvc-operation/Office-Of-Digital-T/win-10-image/default/2023-11/UNSW-NB15%20-%20data%20set.zip',
    'UNSW-NB15_2.csv': 'https://www.unsw.edu.au/content/dam/unsw/administrative/dvc-operation/Office-Of-Digital-T/win-10-image/default/2023-11/UNSW-NB15%20-%20data%20set.zip',
}

# NSL-KDD 下载地址
NSL_KDD_URLS = {
    'KDDTrain+.csv': 'https://raw.githubusercontent.com/defcom17/NSL_KDD/master/KDDTrain+.csv',
    'KDDTest+.csv': 'https://raw.githubusercontent.com/defcom17/NSL_KDD/master/KDDTest+.csv',
}

def download_file(url, dest_path):
    """下载文件"""
    print(f"下载: {url}")
    print(f"保存到: {dest_path}")
    try:
        urllib.request.urlretrieve(url, dest_path)
        print(f"完成: {dest_path}")
        return True
    except Exception as e:
        print(f"下载失败: {e}")
        return False

def download_unsw_nb15():
    """下载 UNSW-NB15 数据集"""
    print("\n=== 下载 UNSW-NB15 数据集 ===")
    print("官方地址: https://research.unsw.edu.au/projects/unsw-nb15-dataset")

    # 官方下载页面需要注册，这里提供备用方案
    print("\n注意: UNSW-NB15 需要从官方页面下载")
    print("1. 访问: https://research.unsw.edu.au/projects/unsw-nb15-dataset")
    print("2. 注册账号并下载数据集")
    print("3. 解压后放到 datasets/ 目录")

def download_nsl_kdd():
    """下载 NSL-KDD 数据集"""
    print("\n=== 下载 NSL-KDD 数据集 ===")

    for filename, url in NSL_KDD_URLS.items():
        dest_path = os.path.join(DATASETS_DIR, filename)
        if os.path.exists(dest_path):
            print(f"已存在: {filename}")
            continue
        download_file(url, dest_path)

def convert_to_log_format():
    """将数据集转换为日志格式"""
    print("\n=== 转换为日志格式 ===")

    import pandas as pd

    # NSL-KDD 列名
    nsl_kdd_columns = [
        'duration', 'protocol_type', 'service', 'flag', 'src_bytes', 'dst_bytes',
        'land', 'wrong_fragment', 'urgent', 'hot', 'num_failed_logins', 'logged_in',
        'num_compromised', 'root_shell', 'su_attempted', 'num_root', 'num_file_creations',
        'num_shells', 'num_access_files', 'num_outbound_cmds', 'is_host_login',
        'is_guest_login', 'count', 'srv_count', 'serror_rate', 'srv_serror_rate',
        'rerror_rate', 'srv_rerror_rate', 'same_srv_rate', 'diff_srv_rate',
        'srv_diff_host_rate', 'dst_host_count', 'dst_host_srv_count',
        'dst_host_same_srv_rate', 'dst_host_diff_srv_rate', 'dst_host_same_src_port_rate',
        'dst_host_srv_diff_host_rate', 'dst_host_serror_rate', 'dst_host_srv_serror_rate',
        'dst_host_rerror_rate', 'dst_host_srv_rerror_rate', 'label', 'difficulty_level'
    ]

    # 读取并转换 NSL-KDD
    kdd_train_path = os.path.join(DATASETS_DIR, 'KDDTrain+.csv')
    kdd_test_path = os.path.join(DATASETS_DIR, 'KDDTest+.csv')

    if os.path.exists(kdd_train_path):
        print("转换 NSL-KDD 训练集...")
        df = pd.read_csv(kdd_train_path, header=None, names=nsl_kdd_columns)

        # 转换为日志格式
        logs = []
        for _, row in df.iterrows():
            log = f"[{row['protocol_type'].upper()}] {row['service']} | " \
                  f"SRC:{row['src_bytes']} DST:{row['dst_bytes']} | " \
                  f"FLAG:{row['flag']} | " \
                  f"ATTACK:{row['label']} (difficulty:{row['difficulty_level']})"
            logs.append(log)

        output_path = os.path.join(DATASETS_DIR, 'nsl_kdd_converted.log')
        with open(output_path, 'w') as f:
            f.write('\n'.join(logs))
        print(f"已保存: {output_path} ({len(logs)} 条记录)")

if __name__ == '__main__':
    print("=" * 60)
    print("DeepLog 标准数据集下载脚本")
    print("=" * 60)

    download_nsl_kdd()
    download_unsw_nb15()
    convert_to_log_format()

    print("\n" + "=" * 60)
    print("下载完成!")
    print("=" * 60)
