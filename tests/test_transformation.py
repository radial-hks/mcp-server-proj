import pytest
import json
import asyncio
from copy import deepcopy

from pyproj import ProjError
from src.mcp_server_proj.core.transformation import CoordinateTransformer
from src.mcp_server_proj.server import handle_call_tool
import mcp.types as types

# --- Fixtures ---

@pytest.fixture
def transformer_4326_to_3857():
    """Returns an initialized CoordinateTransformer from EPSG:4326 to EPSG:3857."""
    transformer = CoordinateTransformer()
    transformer.set_source_crs("EPSG:4326")
    transformer.set_target_crs("EPSG:3857")
    transformer.initialize_transformer()
    return transformer

@pytest.fixture
def transformer_uninitialized():
    """Returns an uninitialized CoordinateTransformer."""
    return CoordinateTransformer()

# --- Tests for CoordinateTransformer.transform_geojson_feature_geometry ---

# Basic valid geometry tests
def test_transform_point(transformer_4326_to_3857):
    geom = {"type": "Point", "coordinates": [0, 0]}
    transformed_geom = transformer_4326_to_3857.transform_geojson_feature_geometry(geom)
    assert transformed_geom["type"] == "Point"
    # ESPG:4326 (0,0) -> EPSG:3857 (0,0)
    assert transformed_geom["coordinates"][0] == pytest.approx(0)
    assert transformed_geom["coordinates"][1] == pytest.approx(0)

    geom_lon_lat = {"type": "Point", "coordinates": [10, 20]}
    transformed_geom_lon_lat = transformer_4326_to_3857.transform_geojson_feature_geometry(geom_lon_lat)
    # Check that coordinates are different after transformation for non-zero values
    assert transformed_geom_lon_lat["coordinates"][0] != geom_lon_lat["coordinates"][0]
    assert transformed_geom_lon_lat["coordinates"][1] != geom_lon_lat["coordinates"][1]
    # Approximate expected values for EPSG:4326 (10,20) -> EPSG:3857
    # Calculated using pyproj directly: Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True).transform(10,20)
    assert transformed_geom_lon_lat["coordinates"][0] == pytest.approx(1113194.9079327358)
    assert transformed_geom_lon_lat["coordinates"][1] == pytest.approx(2273030.926987689)


def test_transform_linestring(transformer_4326_to_3857):
    geom = {"type": "LineString", "coordinates": [[0, 0], [10, 20]]}
    transformed_geom = transformer_4326_to_3857.transform_geojson_feature_geometry(geom)
    assert transformed_geom["type"] == "LineString"
    assert len(transformed_geom["coordinates"]) == 2
    assert transformed_geom["coordinates"][0][0] == pytest.approx(0)
    assert transformed_geom["coordinates"][0][1] == pytest.approx(0)
    assert transformed_geom["coordinates"][1][0] == pytest.approx(1113194.9079327358)
    assert transformed_geom["coordinates"][1][1] == pytest.approx(2273030.926987689)

def test_transform_polygon(transformer_4326_to_3857):
    geom = {
        "type": "Polygon",
        "coordinates": [
            [[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]] # Exterior ring
        ]
    }
    transformed_geom = transformer_4326_to_3857.transform_geojson_feature_geometry(geom)
    assert transformed_geom["type"] == "Polygon"
    assert len(transformed_geom["coordinates"]) == 1
    assert len(transformed_geom["coordinates"][0]) == 5
    # Check a few points
    assert transformed_geom["coordinates"][0][0][0] == pytest.approx(0)
    assert transformed_geom["coordinates"][0][0][1] == pytest.approx(0)
    assert transformed_geom["coordinates"][0][1][0] == pytest.approx(1113194.9079327358) # 10,0
    assert transformed_geom["coordinates"][0][1][1] == pytest.approx(0)

def test_transform_polygon_with_hole(transformer_4326_to_3857):
    geom = {
        "type": "Polygon",
        "coordinates": [
            [[0, 0], [100, 0], [100, 100], [0, 100], [0, 0]],  # Exterior
            [[10, 10], [10, 20], [20, 20], [20, 10], [10, 10]]  # Interior (hole)
        ]
    }
    transformed_geom = transformer_4326_to_3857.transform_geojson_feature_geometry(geom)
    assert transformed_geom["type"] == "Polygon"
    assert len(transformed_geom["coordinates"]) == 2
    assert len(transformed_geom["coordinates"][0]) == 5 # Exterior ring
    assert len(transformed_geom["coordinates"][1]) == 5 # Interior ring
    # Check a point from the hole
    assert transformed_geom["coordinates"][1][0][0] == pytest.approx(1113194.9079327358) # 10,10
    assert transformed_geom["coordinates"][1][0][1] == pytest.approx(1118889.974353909)


# Multi-geometries
def test_transform_multipoint(transformer_4326_to_3857):
    geom = {"type": "MultiPoint", "coordinates": [[0, 0], [10, 20]]}
    transformed_geom = transformer_4326_to_3857.transform_geojson_feature_geometry(geom)
    assert transformed_geom["type"] == "MultiPoint"
    assert len(transformed_geom["coordinates"]) == 2
    assert transformed_geom["coordinates"][0][0] == pytest.approx(0)
    assert transformed_geom["coordinates"][1][0] == pytest.approx(1113194.9079327358)

def test_transform_multilinestring(transformer_4326_to_3857):
    geom = {"type": "MultiLineString", "coordinates": [[[0,0],[1,1]], [[10,20],[21,22]]]}
    transformed_geom = transformer_4326_to_3857.transform_geojson_feature_geometry(geom)
    assert transformed_geom["type"] == "MultiLineString"
    assert len(transformed_geom["coordinates"]) == 2
    assert len(transformed_geom["coordinates"][0]) == 2
    assert transformed_geom["coordinates"][1][0][0] == pytest.approx(1113194.9079327358) # 10,20

def test_transform_multipolygon(transformer_4326_to_3857):
    geom = {
        "type": "MultiPolygon",
        "coordinates": [
            [[[0,0],[1,0],[1,1],[0,1],[0,0]]], # Polygon 1
            [[[10,10],[11,10],[11,11],[10,11],[10,10]]] # Polygon 2
        ]
    }
    transformed_geom = transformer_4326_to_3857.transform_geojson_feature_geometry(geom)
    assert transformed_geom["type"] == "MultiPolygon"
    assert len(transformed_geom["coordinates"]) == 2
    assert len(transformed_geom["coordinates"][0][0]) == 5
    assert transformed_geom["coordinates"][1][0][0][0] == pytest.approx(1113194.9079327358) # 10,10 (first point of first ring of second polygon)

# Z-values
def test_transform_point_with_z(transformer_4326_to_3857):
    geom = {"type": "Point", "coordinates": [0, 0, 100]}
    transformed_geom = transformer_4326_to_3857.transform_geojson_feature_geometry(geom)
    assert transformed_geom["type"] == "Point"
    assert transformed_geom["coordinates"][0] == pytest.approx(0)
    assert transformed_geom["coordinates"][1] == pytest.approx(0)
    assert transformed_geom["coordinates"][2] == 100 # Z value preserved

def test_transform_linestring_with_z(transformer_4326_to_3857):
    geom = {"type": "LineString", "coordinates": [[0, 0, 100], [10, 20, 200]]}
    transformed_geom = transformer_4326_to_3857.transform_geojson_feature_geometry(geom)
    assert transformed_geom["type"] == "LineString"
    assert transformed_geom["coordinates"][0][2] == 100
    assert transformed_geom["coordinates"][1][2] == 200

# Error handling and invalid inputs
def test_transform_uninitialized(transformer_uninitialized):
    geom = {"type": "Point", "coordinates": [0, 0]}
    with pytest.raises(ValueError, match="转换器未初始化"):
        transformer_uninitialized.transform_geojson_feature_geometry(geom)

def test_transform_invalid_geometry_type(transformer_4326_to_3857):
    with pytest.raises(TypeError, match="输入的几何对象必须是字典类型"):
        transformer_4326_to_3857.transform_geojson_feature_geometry("not a dict") # type: ignore

def test_transform_missing_type_key(transformer_4326_to_3857):
    geom = {"coordinates": [0, 0]}
    with pytest.raises(ValueError, match="输入的GeoJSON几何对象无效: 缺少 'type' 键"): # Updated match
        transformer_4326_to_3857.transform_geojson_feature_geometry(geom) # type: ignore

def test_transform_missing_coordinates_key(transformer_4326_to_3857):
    geom = {"type": "Point"}
    with pytest.raises(ValueError, match="输入的GeoJSON几何对象无效: 类型 'Point' 缺少 'coordinates' 键"): # Updated match
        transformer_4326_to_3857.transform_geojson_feature_geometry(geom) # type: ignore

def test_transform_unsupported_type(transformer_4326_to_3857):
    geom = {"type": "PseudoGeometry", "coordinates": [0, 0]}
    with pytest.raises(NotImplementedError, match="几何类型 'PseudoGeometry' 暂不支持转换"):
        transformer_4326_to_3857.transform_geojson_feature_geometry(geom)

def test_transform_geometry_collection_direct(transformer_4326_to_3857):
    # As per implementation, direct GeometryCollection is not supported by this method.
    geom = {"type": "GeometryCollection", "geometries": [{"type": "Point", "coordinates": [0,0]}]}
    with pytest.raises(NotImplementedError, match="几何类型 'GeometryCollection' 暂不支持转换"):
        transformer_4326_to_3857.transform_geojson_feature_geometry(geom)


# Invalid coordinates structure tests
@pytest.mark.parametrize("geom_type, invalid_coords, error_msg_match", [
    ("Point", "not a list", "点的坐标格式无效"),
    ("Point", [0], "点的坐标格式无效"),
    ("Point", ["a", "b"], "点的坐标格式无效"),
    ("LineString", "not a list", "线字符串的坐标格式无效"),
    ("LineString", [[0,0], "not a point"], "线字符串的坐标格式无效"),
    ("LineString", [[0,0], [1]], "线字符串的坐标格式无效"),
    ("Polygon", "not a list", "多边形的坐标格式无效"),
    ("Polygon", [["not a ring"]], "多边形环的坐标格式无效"), # type: ignore
    ("Polygon", [[[0,0], [1]]], "多边形环的坐标格式无效"),
    ("MultiPoint", "not a list", "MultiPoint 的坐标格式无效"),
    ("MultiPoint", ["not a point"], "MultiPoint 的坐标格式无效"),
    ("MultiLineString", "not a list", "MultiLineString 的坐标格式无效"),
    ("MultiLineString", [["not a linestring"]], "MultiLineString 中线字符串的坐标格式无效"), # type: ignore
    ("MultiPolygon", "not a list", "MultiPolygon 的坐标格式无效"),
    ("MultiPolygon", [[["not a ring"]]], "MultiPolygon 中多边形环的坐标格式无效"), # type: ignore
])
def test_transform_invalid_coordinate_structures(transformer_4326_to_3857, geom_type, invalid_coords, error_msg_match):
    geom = {"type": geom_type, "coordinates": invalid_coords}
    with pytest.raises(ValueError, match=error_msg_match):
        transformer_4326_to_3857.transform_geojson_feature_geometry(geom)


def test_proj_error_on_transform(mocker, transformer_4326_to_3857):
    geom = {"type": "Point", "coordinates": [0, 0]}
    # Mock the internal transformer's transform method to raise ProjError
    mocker.patch.object(transformer_4326_to_3857.transformer, 'transform', side_effect=ProjError("Mock Proj Error"))
    with pytest.raises(ValueError, match="坐标转换失败: Mock Proj Error"):
        transformer_4326_to_3857.transform_geojson_feature_geometry(geom)

# --- Tests for the transform-geojson-file tool via handle_call_tool ---

BASE_GEOJSON_POINT = {"type": "Point", "coordinates": [10, 20]}
BASE_GEOJSON_LINESTRING = {"type": "LineString", "coordinates": [[10, 20], [30, 40]]}
BASE_GEOJSON_POLYGON = {"type": "Polygon", "coordinates": [[[0,0], [10,0], [10,10], [0,10], [0,0]]]}

@pytest.mark.asyncio
async def test_handle_call_tool_feature_collection():
    feature_collection = {
        "type": "FeatureCollection",
        "features": [
            {"type": "Feature", "geometry": deepcopy(BASE_GEOJSON_POINT), "properties": {"name": "point1"}},
            {"type": "Feature", "geometry": deepcopy(BASE_GEOJSON_LINESTRING), "properties": {"name": "line1"}},
            {"type": "Feature", "geometry": None, "properties": {"name": "null_geom_feature"}}
        ]
    }
    arguments = {
        "source_crs": "EPSG:4326",
        "target_crs": "EPSG:3857",
        "geojson_content": json.dumps(feature_collection)
    }
    result = await handle_call_tool(name="transform-geojson-file", arguments=arguments)
    assert len(result) == 1
    assert isinstance(result[0], types.TextContent)
    
    transformed_data = json.loads(result[0].text.split("GeoJSON转换成功 (从 EPSG:4326 到 EPSG:3857):\n")[1]) # type: ignore
    
    assert transformed_data["type"] == "FeatureCollection"
    assert len(transformed_data["features"]) == 3
    assert transformed_data["features"][0]["geometry"]["type"] == "Point"
    assert transformed_data["features"][0]["geometry"]["coordinates"][0] == pytest.approx(1113194.9079327358)
    assert transformed_data["features"][0]["properties"]["name"] == "point1"
    assert transformed_data["features"][1]["geometry"]["type"] == "LineString"
    assert transformed_data["features"][1]["geometry"]["coordinates"][0][0] == pytest.approx(1113194.9079327358)
    assert transformed_data["features"][2]["geometry"] is None
    assert transformed_data["features"][2]["properties"]["name"] == "null_geom_feature"

@pytest.mark.asyncio
async def test_handle_call_tool_single_feature():
    feature = {"type": "Feature", "geometry": deepcopy(BASE_GEOJSON_POLYGON), "properties": {"id": 123}}
    arguments = {
        "source_crs": "EPSG:4326",
        "target_crs": "EPSG:3857",
        "geojson_content": json.dumps(feature)
    }
    result = await handle_call_tool(name="transform-geojson-file", arguments=arguments)
    transformed_data = json.loads(result[0].text.split("GeoJSON转换成功 (从 EPSG:4326 到 EPSG:3857):\n")[1]) # type: ignore
    
    assert transformed_data["type"] == "Feature"
    assert transformed_data["geometry"]["type"] == "Polygon"
    assert transformed_data["geometry"]["coordinates"][0][1][0] == pytest.approx(1113194.9079327358) # 10,0
    assert transformed_data["properties"]["id"] == 123

@pytest.mark.asyncio
async def test_handle_call_tool_direct_geometry():
    arguments = {
        "source_crs": "EPSG:4326",
        "target_crs": "EPSG:3857",
        "geojson_content": json.dumps(deepcopy(BASE_GEOJSON_POINT))
    }
    result = await handle_call_tool(name="transform-geojson-file", arguments=arguments)
    transformed_data = json.loads(result[0].text.split("GeoJSON转换成功 (从 EPSG:4326 到 EPSG:3857):\n")[1]) # type: ignore
    assert transformed_data["type"] == "Point"
    assert transformed_data["coordinates"][0] == pytest.approx(1113194.9079327358)

# Error cases for handle_call_tool
@pytest.mark.asyncio
@pytest.mark.parametrize("missing_arg", ["source_crs", "target_crs", "geojson_content"])
async def test_handle_call_tool_missing_args(missing_arg):
    arguments = {
        "source_crs": "EPSG:4326",
        "target_crs": "EPSG:3857",
        "geojson_content": "{}"
    }
    del arguments[missing_arg]
    with pytest.raises(ValueError, match="缺少必要的参数"):
        await handle_call_tool(name="transform-geojson-file", arguments=arguments)

@pytest.mark.asyncio
async def test_handle_call_tool_invalid_json_content():
    arguments = {
        "source_crs": "EPSG:4326",
        "target_crs": "EPSG:3857",
        "geojson_content": "this is not json"
    }
    with pytest.raises(ValueError, match="无效的GeoJSON内容"):
        await handle_call_tool(name="transform-geojson-file", arguments=arguments)

@pytest.mark.asyncio
async def test_handle_call_tool_invalid_crs():
    arguments = {
        "source_crs": "EPSG:INVALID",
        "target_crs": "EPSG:3857",
        "geojson_content": json.dumps(BASE_GEOJSON_POINT)
    }
    with pytest.raises(ValueError, match="无效的源坐标系"): # This matches the error from CoordinateTransformer
        await handle_call_tool(name="transform-geojson-file", arguments=arguments)

@pytest.mark.asyncio
async def test_handle_call_tool_unsupported_toplevel_geojson_type():
    # GeometryCollection at top level is not supported by the current server endpoint logic.
    # The underlying transform_geojson_feature_geometry raises NotImplementedError for GeometryCollection.
    # The server.py catches this and re-raises as ValueError.
    geom_collection = {"type": "GeometryCollection", "geometries": [deepcopy(BASE_GEOJSON_POINT)]}
    arguments = {
        "source_crs": "EPSG:4326",
        "target_crs": "EPSG:3857",
        "geojson_content": json.dumps(geom_collection)
    }
    # The error message comes from the server.py handler for this case
    with pytest.raises(ValueError, match="不支持直接转换 'GeometryCollection' 类型的顶层GeoJSON对象"):
        await handle_call_tool(name="transform-geojson-file", arguments=arguments)


@pytest.mark.asyncio
async def test_handle_call_tool_feature_collection_with_transform_error_on_one_feature(mocker):
    # Mock transform_geojson_feature_geometry to raise error for a specific geometry
    original_method = CoordinateTransformer.transform_geojson_feature_geometry
    
    def mock_transform_with_error(self, geometry_dict):
        if geometry_dict["type"] == "LineString": # Let's say LineString fails
            raise ProjError("Mocked transformation error for LineString")
        return original_method(self, geometry_dict)

    mocker.patch(
        'src.mcp_server_proj.core.transformation.CoordinateTransformer.transform_geojson_feature_geometry', 
        side_effect=mock_transform_with_error, 
        autospec=True 
    )
    
    feature_collection = {
        "type": "FeatureCollection",
        "features": [
            {"type": "Feature", "geometry": deepcopy(BASE_GEOJSON_POINT), "properties": {"name": "point1"}},
            {"type": "Feature", "geometry": deepcopy(BASE_GEOJSON_LINESTRING), "properties": {"name": "line1_fails"}},
            {"type": "Feature", "geometry": {"type":"Point", "coordinates": [1,1]}, "properties": {"name": "point2"}}
        ]
    }
    arguments = {
        "source_crs": "EPSG:4326",
        "target_crs": "EPSG:3857",
        "geojson_content": json.dumps(feature_collection)
    }

    # The server.py logic wraps the specific error
    with pytest.raises(ValueError, match="转换FeatureCollection中第 2 个要素的几何对象时出错: .*Mocked transformation error for LineString"):
        await handle_call_tool(name="transform-geojson-file", arguments=arguments)
    
    # Restore the original method if other tests in the same session might use it
    mocker.stopall()


@pytest.mark.asyncio
async def test_handle_call_tool_null_arguments():
    with pytest.raises(ValueError, match="缺少参数"):
        await handle_call_tool(name="transform-geojson-file", arguments=None)

@pytest.mark.asyncio
async def test_handle_call_tool_feature_collection_invalid_feature_structure():
    feature_collection = {
        "type": "FeatureCollection",
        "features": [
            {"type": "Feature", "geometry": deepcopy(BASE_GEOJSON_POINT)},
            "not a feature dict" # Invalid feature
        ]
    }
    arguments = {
        "source_crs": "EPSG:4326",
        "target_crs": "EPSG:3857",
        "geojson_content": json.dumps(feature_collection)
    }
    with pytest.raises(ValueError, match="FeatureCollection中的第 2 个要素无效: 不是字典或缺少 'geometry'"):
        await handle_call_tool(name="transform-geojson-file", arguments=arguments)

@pytest.mark.asyncio
async def test_handle_call_tool_feature_collection_missing_features_key():
    feature_collection = {"type": "FeatureCollection", "geoms": [] } # 'geoms' instead of 'features'
    arguments = {
        "source_crs": "EPSG:4326",
        "target_crs": "EPSG:3857",
        "geojson_content": json.dumps(feature_collection)
    }
    with pytest.raises(ValueError, match="无效的FeatureCollection: 缺少或无效的 'features' 列表"):
        await handle_call_tool(name="transform-geojson-file", arguments=arguments)

@pytest.mark.asyncio
async def test_handle_call_tool_feature_missing_geometry_key():
    feature = {"type": "Feature", "props": {}} # 'props' instead of 'geometry'
    arguments = {
        "source_crs": "EPSG:4326",
        "target_crs": "EPSG:3857",
        "geojson_content": json.dumps(feature)
    }
    with pytest.raises(ValueError, match="无效的Feature: 缺少 'geometry'"):
        await handle_call_tool(name="transform-geojson-file", arguments=arguments)

@pytest.mark.asyncio
async def test_handle_call_tool_unsupported_geojson_type_in_server():
    geojson_data = {"type": "SomeCustomType", "coordinates": [1,2,3]}
    arguments = {
        "source_crs": "EPSG:4326",
        "target_crs": "EPSG:3857",
        "geojson_content": json.dumps(geojson_data)
    }
    with pytest.raises(ValueError, match="不支持的GeoJSON类型: 'SomeCustomType'"):
        await handle_call_tool(name="transform-geojson-file", arguments=arguments)
