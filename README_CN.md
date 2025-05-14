# MCP Server PROJ

基于 MCP（Model Context Protocol）协议的坐标系统转换服务器，提供专业的地图投影与坐标转换功能。

## 功能特点

- 支持多种坐标系统格式：
  - EPSG 代码（全球通用的坐标系统标识符）
  - WKT（Well-Known Text，标准的坐标系统描述格式）
  - Proj 字符串格式（简洁的投影参数表达式）
- 支持批量坐标转换
- 提供简洁直观的 API 接口
- 双模式运行：可作为独立服务器或嵌入式库使用

## 安装方法

```bash
pip install mcp-server-proj
```

## 使用说明

### 服务器模式

```bash
mcp-server-proj
```

### 库模式

```python
from mcp_server_proj import CoordinateTransformer

# 创建坐标转换器实例
transformer = CoordinateTransformer()

# 设置源坐标系和目标坐标系
transformer.set_source_crs("EPSG:4326")  # WGS84 经纬度
transformer.set_target_crs("EPSG:3857")  # Web墨卡托投影

# 初始化转换器
transformer.initialize_transformer()

# 执行坐标转换（示例：北京坐标）
x, y = transformer.transform_point(116.3, 39.9)
print(f"转换后的坐标: ({x:.2f}, {y:.2f})")
```

## API 文档

### CoordinateTransformer 类

核心的坐标转换类，提供以下方法：

- `set_source_crs(crs: str)`: 设置源坐标系统
- `set_target_crs(crs: str)`: 设置目标坐标系统
- `initialize_transformer()`: 初始化转换器
- `transform_point(x: float, y: float) -> tuple[float, float]`: 转换单个点的坐标

### 服务器工具

MCP 协议服务器提供两个主要工具：

- `transform-coordinates`: 坐标转换工具
  ```json
  {
    "source_crs": "EPSG:4326",
    "target_crs": "EPSG:3857",
    "coordinates": [
      {"x": 116.3, "y": 39.9}
    ]
  }
  ```

- `list-supported-crs`: 列出所有支持的坐标系统

## 支持的坐标系统

### 1. EPSG 代码
标准的坐标参考系统标识符：
- EPSG:4326 - WGS84 地理坐标系（GPS 使用的经纬度）
- EPSG:3857 - Web 墨卡托投影（网络地图常用）
- 以及更多其他坐标系统...

### 2. WKT 格式
地理坐标系统示例：
```
GEOGCS["WGS 84",
  DATUM["WGS_1984",
    SPHEROID["WGS 84",6378137,298.257223563]],
  PRIMEM["Greenwich",0],
  UNIT["degree",0.0174532925199433]]
```

### 3. Proj 格式
WGS84 示例：
```
+proj=longlat +datum=WGS84 +no_defs +type=crs
```

## 开发指南

### 调试方法
推荐使用 [MCP Inspector](https://github.com/modelcontextprotocol/inspector) 进行调试：

```bash
npx @modelcontextprotocol/inspector mcp-server-proj
```

## 环境要求

- Python >= 3.12
- mcp >= 1.3.0
- pyproj >= 3.0.0

## 许可证

MIT 开源许可

## 作者

radial-hks (radialjiajie@gmail.com)

## 参与贡献

欢迎提交 Issue 和 Pull Request！如果您发现了 bug 或有新功能建议，请随时与我们联系。