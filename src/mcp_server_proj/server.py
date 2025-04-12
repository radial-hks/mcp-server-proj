import asyncio
from typing import List
from pyproj import CRS, Transformer
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio

# 存储常用的坐标系统信息
COMMON_CRS = {
    "WGS84": "EPSG:4326",           # GPS全球定位系统
    "WebMercator": "EPSG:3857",     # Web墨卡托投影
    "CGCS2000": "EPSG:4490",        # 中国2000国家大地坐标系
    "Beijing54": "EPSG:4214",       # 北京54坐标系
    "Xian80": "EPSG:4610",          # 西安80坐标系
}

# 创建服务器实例
server = Server("mcp-coordinate-transform")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """列出可用的坐标转换工具"""
    return [
        types.Tool(
            name="transform-coordinates",
            description="在不同坐标系统之间转换坐标",
            inputSchema={
                "type": "object",
                "properties": {
                    "source_crs": {
                        "type": "string",
                        "description": "源坐标系统（EPSG代码或常用坐标系名称）",
                        "enum": list(COMMON_CRS.keys()) + list(COMMON_CRS.values()),
                    },
                    "target_crs": {
                        "type": "string",
                        "description": "目标坐标系统（EPSG代码或常用坐标系名称）",
                        "enum": list(COMMON_CRS.keys()) + list(COMMON_CRS.values()),
                    },
                    "coordinates": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "x": {"type": "number"},
                                "y": {"type": "number"},
                            },
                            "required": ["x", "y"]
                        },
                        "minItems": 1,
                    }
                },
                "required": ["source_crs", "target_crs", "coordinates"],
            },
        ),
        types.Tool(
            name="list-supported-crs",
            description="列出所有支持的坐标系统",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        )
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """处理工具调用请求"""
    if name == "transform-coordinates":
        if not arguments:
            raise ValueError("缺少参数")
        # 解析参数 目标坐标系 源坐标系 坐标列表
        source_crs = arguments.get("source_crs")
        target_crs = arguments.get("target_crs")
        coordinates = arguments.get("coordinates")

        if not all([source_crs, target_crs, coordinates]):
            raise ValueError("缺少必要的参数")

        # 解析坐标系统
        source_epsg = COMMON_CRS.get(source_crs, source_crs)
        target_epsg = COMMON_CRS.get(target_crs, target_crs)

        try:
            # 创建坐标转换器
            transformer = Transformer.from_crs(
                source_epsg,
                target_epsg,
                always_xy=True  # 确保输入输出顺序为 (x,y)
            )

            # 转换所有坐标
            results = []
            for coord in coordinates:
                x, y = coord["x"], coord["y"]
                try:
                    trans_x, trans_y = transformer.transform(x, y)
                    results.append({
                        "original": {"x": x, "y": y},
                        "transformed": {"x": trans_x, "y": trans_y}
                    })
                except Exception as e:
                    results.append({
                        "original": {"x": x, "y": y},
                        "error": str(e)
                    })

            return [
                types.TextContent(
                    type="text",
                    text=f"坐标转换结果 (从 {source_crs} 到 {target_crs}):\n" +
                        "\n".join(
                            f"输入: ({r['original']['x']}, {r['original']['y']})\n" +
                            (f"输出: ({r['transformed']['x']:.8f}, {r['transformed']['y']:.8f})"
                            if 'transformed' in r else f"错误: {r['error']}")
                            for r in results
                        )
                )
            ]
        except Exception as e:
            raise ValueError(f"坐标转换失败: {str(e)}")

    elif name == "list-supported-crs":
        crs_info = []
        for name, epsg in COMMON_CRS.items():
            try:
                crs = CRS.from_string(epsg)
                crs_info.append(f"{name} ({epsg}):\n  {crs.name}")
            except Exception:
                crs_info.append(f"{name} ({epsg}): 无法获取详细信息")

        return [
            types.TextContent(
                type="text",
                text="支持的坐标系统:\n" + "\n".join(crs_info)
            )
        ]

    else:
        raise ValueError(f"未知的工具: {name}")

async def main():
    """运行服务器"""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="mcp-coordinate-transform",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())