# -*- coding: utf-8 -*-
"""
易语言风格的INI配置文件读写函数
完全模仿易语言的 读配置项 和 写配置项 用法。
函数名和参数顺序与易语言保持一致，开箱即用。
"""

import configparser
import os


def 读配置项(路径, 配置节名, 配置项, 默认文本数据=""):
    """
    读取INI配置文件中的指定项。

    参数:
        路径: 配置文件路径 (例如 "config.ini")
        配置节名: 节名称 (例如 "数据库")
        配置项: 键名称 (例如 "主机")
        默认文本数据: 如果节或键不存在，返回此默认值

    返回:
        字符串值，若读取失败或不存在则返回默认文本数据
    """
    # 文件不存在则直接返回默认值
    if not os.path.exists(路径):
        return 默认文本数据

    config = configparser.ConfigParser()
    try:
        config.read(路径, encoding='utf-8')
        if config.has_section(配置节名) and config.has_option(配置节名, 配置项):
            return config.get(配置节名, 配置项)
        else:
            return 默认文本数据
    except Exception:
        return 默认文本数据


def 写配置项(路径, 配置节名, 配置项, 写入的文本数据):
    """
    写入或修改INI配置文件中的指定项。

    参数:
        路径: 配置文件路径 (例如 "config.ini")
        配置节名: 节名称 (例如 "数据库")
        配置项: 键名称 (例如 "主机")
        写入的文本数据: 要写入的字符串值

    返回:
        True 表示成功，False 表示失败（如路径不可写）
    """
    config = configparser.ConfigParser()

    # 如果文件已存在，读取现有内容（保留其他节和项）
    if os.path.exists(路径):
        try:
            config.read(路径, encoding='utf-8')
        except Exception:
            # 文件损坏时重新创建
            config = configparser.ConfigParser()

    # 确保节存在
    if not config.has_section(配置节名):
        config.add_section(配置节名)

    # 设置配置项的值
    config.set(配置节名, 配置项, str(写入的文本数据))

    # 写入文件（自动创建目录）
    try:
        dirname = os.path.dirname(路径)
        if dirname and not os.path.exists(dirname):
            os.makedirs(dirname, exist_ok=True)
        with open(路径, 'w', encoding='utf-8') as f:
            config.write(f)
        return True
    except Exception:
        return False


# ===== 使用示例（直接运行本文件时会执行以下测试代码）=====
if __name__ == '__main__':
    # 写配置
    if 写配置项('test.ini', '系统设置', '版本', '1.0'):
        print('✓ 写配置成功')
    else:
        print('✗ 写配置失败')

    # 读配置
    version = 读配置项('test.ini', '系统设置', '版本', '未知')
    print('版本号:', version)

    # 读不存在的项（返回默认值）
    none_val = 读配置项('test.ini', '系统设置', '不存在的项', '默认值')
    print('不存在的项:', none_val)