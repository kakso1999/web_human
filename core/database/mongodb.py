"""
MongoDB 数据库访问模块
提供 MongoDB 数据库实例的获取方法
"""

from core.config.database import Database, get_database

__all__ = ['Database', 'get_database']
