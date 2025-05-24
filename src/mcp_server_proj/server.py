import asyncio
import json # Added for GeoJSON parsing
from typing import List, Dict, Any # Added Dict and Any
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
        ),
        types.Tool(
            name="transform-geojson-file",
            description="转换GeoJSON文件中的几何对象坐标系。输入源CRS、目标CRS和GeoJSON内容的字符串。",
            inputSchema={
                "type": "object",
                "properties": {
                    "source_crs": {
                        "type": "string",
                        "description": "源坐标系统 (例如 EPSG:4326)",
                    },
                    "target_crs": {
                        "type": "string",
                        "description": "目标坐标系统 (例如 EPSG:3857)",
                    },
                    "geojson_content": {
                        "type": "string",
                        "description": "包含GeoJSON数据的字符串内容。",
                    },
                },
                "required": ["source_crs", "target_crs", "geojson_content"],
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

    elif name == "transform-geojson-file":
        if not arguments:
            raise ValueError("缺少参数 (Missing arguments)")

        source_crs = arguments.get("source_crs")
        target_crs = arguments.get("target_crs")
        geojson_content_str = arguments.get("geojson_content")

        if not all([source_crs, target_crs, geojson_content_str]):
            raise ValueError("缺少必要的参数: source_crs, target_crs, 或 geojson_content (Missing required arguments: source_crs, target_crs, or geojson_content)")

        try:
            geojson_data: Dict[str, Any] = json.loads(geojson_content_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"无效的GeoJSON内容: {str(e)} (Invalid GeoJSON content: {str(e)})")

        transformer = CoordinateTransformer()
        try:
            transformer.set_source_crs(source_crs)
            transformer.set_target_crs(target_crs)
            transformer.initialize_transformer()

            geojson_type = geojson_data.get("type")

            if geojson_type == "FeatureCollection":
                if "features" not in geojson_data or not isinstance(geojson_data["features"], list):
                    raise ValueError("无效的FeatureCollection: 缺少或无效的 'features' 列表 (Invalid FeatureCollection: missing or invalid 'features' list)")
                
                for i, feature in enumerate(geojson_data["features"]):
                    if not isinstance(feature, dict) or "geometry" not in feature:
                        raise ValueError(f"FeatureCollection中的第 {i+1} 个要素无效: 不是字典或缺少 'geometry' (Invalid feature at index {i} in FeatureCollection: not a dict or missing 'geometry')")
                    if feature["geometry"] is not None: # Allow null geometries
                         try:
                            feature["geometry"] = transformer.transform_geojson_feature_geometry(feature["geometry"])
                         except Exception as e:
                            # Add information about which feature failed
                            raise ValueError(f"转换FeatureCollection中第 {i+1} 个要素的几何对象时出错: {str(e)} (Error transforming geometry for feature at index {i}: {str(e)})")

            elif geojson_type == "Feature":
                if "geometry" not in geojson_data:
                    raise ValueError("无效的Feature: 缺少 'geometry' (Invalid Feature: missing 'geometry')")
                if geojson_data["geometry"] is not None: # Allow null geometries
                    try:
                        geojson_data["geometry"] = transformer.transform_geojson_feature_geometry(geojson_data["geometry"])
                    except Exception as e:
                        raise ValueError(f"转换Feature的几何对象时出错: {str(e)} (Error transforming geometry for Feature: {str(e)})")
            
            elif geojson_type in ["Point", "LineString", "Polygon", "MultiPoint", "MultiLineString", "MultiPolygon"]: # Removed "GeometryCollection" as it's not directly transformed by the previous method's main cases
                # For individual geometry types, transform the whole geojson_data object
                # as it is the geometry itself.
                try:
                    geojson_data = transformer.transform_geojson_feature_geometry(geojson_data)
                except Exception as e:
                    raise ValueError(f"转换几何对象 '{geojson_type}' 时出错: {str(e)} (Error transforming geometry type '{geojson_type}': {str(e)})")
            elif geojson_data.get("type") == "GeometryCollection":
                 raise ValueError(f"不支持直接转换 'GeometryCollection' 类型的顶层GeoJSON对象。请在Feature或FeatureCollection中使用。 (Direct transformation of top-level 'GeometryCollection' is not supported. Please use it within a Feature or FeatureCollection.)")
            else:
                supported_types = ["FeatureCollection", "Feature", "Point", "LineString", "Polygon", "MultiPoint", "MultiLineString", "MultiPolygon"]
                raise ValueError(f"不支持的GeoJSON类型: '{geojson_type}'。支持的类型为: {', '.join(supported_types)} (Unsupported GeoJSON type: '{geojson_type}'. Supported types are: {', '.join(supported_types)})")

            transformed_geojson_str = json.dumps(geojson_data, indent=2) # indent for readability

            return [
                types.TextContent(
                    type="text",
                    text=f"GeoJSON转换成功 (从 {source_crs} 到 {target_crs}):\n{transformed_geojson_str}"
                )
            ]
        
        except ValueError as e: # Catch errors from transformer setup or transformation logic
            raise ValueError(f"GeoJSON转换失败: {str(e)} (GeoJSON transformation failed: {str(e)})")
        except Exception as e: # Catch any other unexpected errors
            # Log the full error for debugging if possible, then raise a generic one
            # print(f"Unexpected error during GeoJSON transformation: {traceback.format_exc()}")
            raise ValueError(f"GeoJSON转换过程中发生意外错误: {str(e)} (An unexpected error occurred during GeoJSON transformation: {str(e)})")

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