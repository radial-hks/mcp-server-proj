import asyncio
import json # Will be used for initial load, then geojson library
import geojson # Added for GeoJSON object manipulation
from typing import List, Dict, Any # Dict, Any might be less needed after geojson lib usage
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
            # First, parse the string as a Python dictionary
            geojson_data_dict: Dict[str, Any] = json.loads(geojson_content_str)
            # Then, convert the dictionary to a geojson object
            # Using default=None to explicitly handle cases where it's not a known GeoJSON type
            # or use specific constructors if you expect certain types.
            # geojson.GeoJSON.to_instance is a good general approach.
            geojson_obj = geojson.GeoJSON.to_instance(geojson_data_dict)

        except json.JSONDecodeError as e:
            raise ValueError(f"无效的GeoJSON内容: JSON格式错误 - {str(e)} (Invalid GeoJSON content: JSON format error - {str(e)})")
        except (TypeError, ValueError, KeyError, geojson.errors.GeoJSONError) as e: # Catch errors from geojson.GeoJSON.to_instance
            raise ValueError(f"无效的GeoJSON内容: 结构或内容不符合GeoJSON规范 - {str(e)} (Invalid GeoJSON content: Structure or content does not conform to GeoJSON specification - {str(e)})")


        transformer = CoordinateTransformer()
        try:
            transformer.set_source_crs(source_crs)
            transformer.set_target_crs(target_crs)
            transformer.initialize_transformer()

            if not hasattr(geojson_obj, 'type'):
                raise ValueError("无效的GeoJSON对象: 缺少 'type' 属性 (Invalid GeoJSON object: missing 'type' attribute)")

            geojson_type = geojson_obj.type

            if geojson_type == "FeatureCollection":
                if not isinstance(geojson_obj, geojson.FeatureCollection):
                     raise ValueError("类型声称是FeatureCollection但对象结构不匹配 (Type claim is FeatureCollection but object structure mismatch)")
                for i, feature in enumerate(geojson_obj.features):
                    if not isinstance(feature, geojson.Feature):
                         raise ValueError(f"FeatureCollection中的第 {i+1} 个要素无效: 不是有效的GeoJSON Feature对象 (Invalid feature at index {i} in FeatureCollection: not a valid GeoJSON Feature object)")
                    if feature.geometry:  # Check if geometry is not None
                        try:
                            # feature.geometry is already a geojson geometry object
                            transformed_geometry = transformer.transform_geojson_feature_geometry(feature.geometry)
                            feature.geometry = transformed_geometry
                        except Exception as e:
                            raise ValueError(f"转换FeatureCollection中第 {i+1} 个要素的几何对象时出错: {str(e)} (Error transforming geometry for feature at index {i}: {str(e)})")
            
            elif geojson_type == "Feature":
                if not isinstance(geojson_obj, geojson.Feature):
                    raise ValueError("类型声称是Feature但对象结构不匹配 (Type claim is Feature but object structure mismatch)")
                if geojson_obj.geometry: # Check if geometry is not None
                    try:
                        transformed_geometry = transformer.transform_geojson_feature_geometry(geojson_obj.geometry)
                        geojson_obj.geometry = transformed_geometry
                    except Exception as e:
                        raise ValueError(f"转换Feature的几何对象时出错: {str(e)} (Error transforming geometry for Feature: {str(e)})")

            elif isinstance(geojson_obj, geojson.geometry.Geometry):
                # This handles Point, LineString, Polygon, MultiPoint, MultiLineString, MultiPolygon, and GeometryCollection
                # if transform_geojson_feature_geometry supports them.
                # The refactored transform_geojson_feature_geometry itself will raise TypeError for unsupported types passed to it.
                try:
                    geojson_obj = transformer.transform_geojson_feature_geometry(geojson_obj)
                except TypeError as e: # Catch TypeError from the transformation method if type is not directly transformable by map_tuples
                    raise ValueError(f"转换几何对象 '{geojson_type}' 时出错: {str(e)} (Error transforming geometry type '{geojson_type}': {str(e)})")
                except Exception as e:
                    raise ValueError(f"转换几何对象 '{geojson_type}' 时出错: {str(e)} (Error transforming geometry type '{geojson_type}': {str(e)})")
            else:
                # This case should ideally be caught by geojson.GeoJSON.to_instance or the isinstance checks above
                supported_types = ["FeatureCollection", "Feature", "Point", "LineString", "Polygon", "MultiPoint", "MultiLineString", "MultiPolygon", "GeometryCollection"]
                raise ValueError(f"不支持或无效的顶层GeoJSON对象类型: '{geojson_type}'. 支持的类型为: {', '.join(supported_types)} (Unsupported or invalid top-level GeoJSON object type: '{geojson_type}'. Supported types are: {', '.join(supported_types)})")

            # Serialize the transformed geojson object back to a string
            transformed_geojson_str = geojson.dumps(geojson_obj, indent=2)

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