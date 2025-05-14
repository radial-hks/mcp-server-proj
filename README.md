# MCP Server PROJ

基于 MCP 协议的坐标系统转换服务器，支持多种坐标系统格式之间的转换。

## 功能特点

- 支持多种坐标系统格式：
  - EPSG 代码
  - WKT 格式
  - Proj 字符串格式
- 批量坐标转换
- 简单易用的 API
- 支持作为服务器运行或库形式使用

## 安装

```bash
pip install mcp-server-proj
```

## 使用方法

### 作为服务器运行

```bash
mcp-server-proj
```

### 作为库使用

```python
from mcp_server_proj import CoordinateTransformer

# 创建转换器实例
transformer = CoordinateTransformer()

# 设置源和目标坐标系
transformer.set_source_crs("EPSG:4326")  # WGS84
transformer.set_target_crs("EPSG:3857")  # Web墨卡托

# 初始化转换器
transformer.initialize_transformer()

# 转换坐标
x, y = transformer.transform_point(116.3, 39.9)
print(f"转换后的坐标: ({x}, {y})")
```

## API 文档

### CoordinateTransformer

主要的坐标转换类，提供以下方法：

- `set_source_crs(crs: str)`: 设置源坐标系
- `set_target_crs(crs: str)`: 设置目标坐标系
- `initialize_transformer()`: 初始化转换器
- `transform_point(x: float, y: float) -> tuple[float, float]`: 转换单个点的坐标

### Server

MCP 协议服务器类，提供以下工具：

- `transform-coordinates`: 坐标转换工具
- `list-supported-crs`: 列出支持的坐标系统

## 依赖

- Python >= 3.12
- mcp >= 1.3.0
- pyproj >= 3.0.0

## 许可证

MIT

## 作者

radial-hks (radialjiajie@gmail.com)

## 贡献

欢迎提交 Issue 和 Pull Request！
