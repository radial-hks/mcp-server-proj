"""
MCP Server PROJ - 坐标系统转换服务器

这个包提供了一个基于 MCP 协议的坐标系统转换服务器，支持多种坐标系统格式之间的转换。
"""

__version__ = "0.1.0"
__author__ = "radial-hks"

from .server import Server, main
from .core.transformation import CoordinateTransformer

__all__ = ['Server', 'main', 'CoordinateTransformer']