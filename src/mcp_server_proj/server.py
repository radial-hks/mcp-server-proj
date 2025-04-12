import asyncio
from typing import List
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio
from .core.transformation import CoordinateTransformer

# 创建服务器实例
server = Server("mcp-coordinate-transform")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """列出可用的坐标转换工具"""
    return [
        types.Tool(
            name="transform-coordinates",
            description="在不同坐标系统之间转换坐标，支持EPSG、WKT和Proj格式的坐标系统",
            inputSchema={
                "type": "object",
                "properties": {
                    "source_crs": {
                        "type": "string",
                        "description": "源坐标系统，支持以下格式：\n1. EPSG代码 (如：EPSG:4326)\n2. WKT格式 (如：GEOGCS[\"WGS 84\",DATUM[...]])\n3. Proj格式 (如：+proj=longlat +datum=WGS84)",
                    },
                    "target_crs": {
                        "type": "string",
                        "description": "目标坐标系统，支持以下格式：\n1. EPSG代码 (如：EPSG:4326)\n2. WKT格式 (如：GEOGCS[\"WGS 84\",DATUM[...]])\n3. Proj格式 (如：+proj=longlat +datum=WGS84)",
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
        
        source_crs = arguments.get("source_crs")
        target_crs = arguments.get("target_crs")
        coordinates = arguments.get("coordinates")

        if not all([source_crs, target_crs, coordinates]):
            raise ValueError("缺少必要的参数")

        # 使用 CoordinateTransformer 进行转换
        transformer = CoordinateTransformer()
        try:
            # 直接使用输入的坐标系统字符串
            transformer.set_source_crs(source_crs)
            transformer.set_target_crs(target_crs)
            transformer.initialize_transformer()

            # 转换所有坐标
            results = []
            for coord in coordinates:
                x, y = coord["x"], coord["y"]
                try:
                    trans_x, trans_y = transformer.transform_point(x, y)
                    results.append({
                        "original": {"x": x, "y": y},
                        "transformed": {"x": trans_x, "y": trans_y}
                    })
                except ValueError as e:
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
        except ValueError as e:
            raise ValueError(f"坐标转换失败: {str(e)}")

    elif name == "list-supported-crs":
        return [
            types.TextContent(
                type="text",
                text="支持的坐标系统格式:\n\n" +
                    "1. EPSG代码格式:\n" +
                    "   - 示例: EPSG:4326 (WGS84)\n" +
                    "   - 示例: EPSG:3857 (Web墨卡托投影)\n\n" +
                    "2. WKT格式:\n" +
                    "   - 地理坐标系示例:\n" +
                    "     GEOGCS[\"WGS 84\",DATUM[\"WGS_1984\",SPHEROID[\"WGS 84\",6378137,298.257223563]],PRIMEM[\"Greenwich\",0],UNIT[\"degree\",0.0174532925199433]]\n\n" +
                    "   - 投影坐标系示例:\n" +
                    "     PROJCS[\"WGS 84 / UTM zone 50N\",GEOGCS[\"WGS 84\",...],PROJECTION[\"Transverse_Mercator\"],PARAMETER[\"latitude_of_origin\",0],PARAMETER[\"central_meridian\",117],UNIT[\"metre\",1]]\n\n" +
                    "3. Proj格式:\n" +
                    "   - WGS84示例:\n" +
                    "     +proj=longlat +datum=WGS84 +no_defs +type=crs\n\n" +
                    "   - Web墨卡托投影示例:\n" +
                    "     +proj=merc +a=6378137 +b=6378137 +lat_ts=0 +lon_0=0 +x_0=0 +y_0=0 +k=1 +units=m +no_defs"
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