# MCP Server PROJ 坐标投影与转换服务器

MCP Server PROJ 是一个用于地图投影和坐标转换的服务器。

![](image/mcp_server_proj_transform.png)

### 工具

服务器实现了两个坐标转换工具：

1. transform-coordinates（坐标转换）
   - 在不同坐标系统之间转换坐标
   - 支持以下坐标系统格式：
     - EPSG代码（例如：EPSG:4326表示WGS84）
     - WKT格式
     - Proj格式
   - 所需输入参数：
     - source_crs：源坐标系统
     - target_crs：目标坐标系统
     - coordinates：包含x、y值的点数组
   
   示例：从WGS84（EPSG:4326）转换到正射投影
   ```
   输入：
   - source_crs: EPSG:4326
   - target_crs: +proj=ortho +lon_0=112.364017384874 +lat_0=34.9227297291321 +a=6371010 +units=m +no_defs
   - coordinates: [112.364017384874, 34.9227297291321]
   
   输出：
   - 转换后的坐标: [0.00000000, 0.00000000]
   ```

2. list-supported-crs（列出支持的坐标系统）
   - 列出所有支持的坐标系统格式及示例
   - 提供以下格式的详细示例：
     - EPSG代码格式
     - 地理和投影坐标系统的WKT格式
     - Proj格式

## 配置

### Claude Desktop

在MacOS系统：`~/Library/Application\ Support/Claude/claude_desktop_config.json`
在Windows系统：`%APPDATA%/Claude/claude_desktop_config.json`

<details>
  <summary>开发/未发布服务器配置</summary>

```json
{
  "mcpServers": {
    "mcp-server-proj": {
      "command": "uv",
      "args": [
        "--directory",
        "E:\\Code\\PythonDir\\MCP\\mcp-server-proj",
        "run",
        "mcp-server-proj"
      ]
    }
  }
}
```
</details>

<details>
  <summary>已发布服务器配置</summary>

```json
{
  "mcpServers": {
    "mcp-server-proj": {
      "command": "uvx",
      "args": [
        "mcp-server-proj"
      ]
    }
  }
}
```
</details>

### 调试

由于MCP服务器通过标准输入输出运行，调试可能会比较困难。为了获得最佳的调试体验，我们强烈推荐使用[MCP Inspector](https://github.com/modelcontextprotocol/inspector)。

你可以通过[`npm`](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm)使用以下命令启动MCP Inspector：

```bash
npx @modelcontextprotocol/inspector uv --directory E:\Code\PythonDir\MCP\mcp-server-proj run mcp-server-proj
```

启动后，Inspector将显示一个URL，你可以在浏览器中访问该URL开始调试。

## 坐标系统信息
### 1. EPSG（坐标系统唯一代码）
EPSG代码是地理和投影坐标系统的唯一标识符，在GIS软件和编程库中广泛使用。以下是一些常用的EPSG代码及其对应的坐标系统：
- EPSG:4326：WGS84地理坐标系统（GPS标准）
- EPSG:3857：Web墨卡托投影（被谷歌地图、高德地图等使用）

### 2. WKT（Well-Known Text格式）
WKT（Well-Known Text）是一种人类可读的坐标系统描述格式，在GIS软件和数据库中广泛使用。以下是典型的WKT结构：
- 地理坐标系统（GEOGCS）
```
GEOGCS["WGS 84",
  DATUM["WGS_1984",
    SPHEROID["WGS 84",6378137,298.257223563]],
  PRIMEM["Greenwich",0],
  UNIT["degree",0.0174532925199433]]
```
- 投影坐标系统（PROJCS）
```
PROJCS["WGS 84 / UTM zone 50N",
  GEOGCS["WGS 84",...],
  PROJECTION["Transverse_Mercator"],
  PARAMETER["latitude_of_origin",0],
  PARAMETER["central_meridian",117],
  UNIT["metre",1]]
```
### 3. Proj（简洁的投影参数表达式）
Proj是一种简洁的投影参数表达式格式，在proj4库和命令行工具中常用。以下是典型的Proj语法示例：

WGS84：
```proj
+proj=longlat +datum=WGS84 +no_defs +type=crs
```

Web墨卡托投影：
```proj
+proj=merc +a=6378137 +b=6378137 +lat_ts=0 +lon_0=0 +x_0=0 +y_0=0 +k=1 +units=m +no_defs
```

## 参考资料
更多关于坐标系统的信息，请访问：https://epsg.io/
如果你对坐标转换的JavaScript实现感兴趣，可以查看：https://github.com/proj4js/proj4js