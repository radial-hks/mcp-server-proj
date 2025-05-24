import pytest
import json
import asyncio
from copy import deepcopy
import geojson # Added
from geojson.geometry import Point, LineString, Polygon, MultiPoint, MultiLineString, MultiPolygon, GeometryCollection # Added

from pyproj import ProjError
from src.mcp_server_proj.core.transformation import CoordinateTransformer
from src.mcp_server_proj.server import handle_call_tool # handle_call_tool will be tested
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
    geom = Point((0, 0))
    transformed_geom = transformer_4326_to_3857.transform_geojson_feature_geometry(geom)
    assert isinstance(transformed_geom, Point)
    # ESPG:4326 (0,0) -> EPSG:3857 (0,0)
    assert transformed_geom.coordinates[0] == pytest.approx(0)
    assert transformed_geom.coordinates[1] == pytest.approx(0)

    geom_lon_lat = Point((10, 20))
    transformed_geom_lon_lat = transformer_4326_to_3857.transform_geojson_feature_geometry(geom_lon_lat)
    assert isinstance(transformed_geom_lon_lat, Point)
    # Check that coordinates are different after transformation for non-zero values
    assert transformed_geom_lon_lat.coordinates[0] != geom_lon_lat.coordinates[0]
    assert transformed_geom_lon_lat.coordinates[1] != geom_lon_lat.coordinates[1]
    # Approximate expected values for EPSG:4326 (10,20) -> EPSG:3857
    assert transformed_geom_lon_lat.coordinates[0] == pytest.approx(1113194.9079327358)
    assert transformed_geom_lon_lat.coordinates[1] == pytest.approx(2273030.926987689)


def test_transform_linestring(transformer_4326_to_3857):
    geom = LineString([(0, 0), (10, 20)])
    transformed_geom = transformer_4326_to_3857.transform_geojson_feature_geometry(geom)
    assert isinstance(transformed_geom, LineString)
    assert len(transformed_geom.coordinates) == 2
    assert transformed_geom.coordinates[0][0] == pytest.approx(0)
    assert transformed_geom.coordinates[0][1] == pytest.approx(0)
    assert transformed_geom.coordinates[1][0] == pytest.approx(1113194.9079327358)
    assert transformed_geom.coordinates[1][1] == pytest.approx(2273030.926987689)

def test_transform_polygon(transformer_4326_to_3857):
    coords = [[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]]
    geom = Polygon(coords)
    transformed_geom = transformer_4326_to_3857.transform_geojson_feature_geometry(geom)
    assert isinstance(transformed_geom, Polygon)
    assert len(transformed_geom.coordinates) == 1
    assert len(transformed_geom.coordinates[0]) == 5
    # Check a few points
    assert transformed_geom.coordinates[0][0][0] == pytest.approx(0)
    assert transformed_geom.coordinates[0][0][1] == pytest.approx(0)
    assert transformed_geom.coordinates[0][1][0] == pytest.approx(1113194.9079327358) # 10,0
    assert transformed_geom.coordinates[0][1][1] == pytest.approx(0)

def test_transform_polygon_with_hole(transformer_4326_to_3857):
    coords = [
        [[0, 0], [100, 0], [100, 100], [0, 100], [0, 0]],  # Exterior
        [[10, 10], [10, 20], [20, 20], [20, 10], [10, 10]]  # Interior (hole)
    ]
    geom = Polygon(coords)
    transformed_geom = transformer_4326_to_3857.transform_geojson_feature_geometry(geom)
    assert isinstance(transformed_geom, Polygon)
    assert len(transformed_geom.coordinates) == 2
    assert len(transformed_geom.coordinates[0]) == 5 # Exterior ring
    assert len(transformed_geom.coordinates[1]) == 5 # Interior ring
    # Check a point from the hole
    assert transformed_geom.coordinates[1][0][0] == pytest.approx(1113194.9079327358) # 10,10
    assert transformed_geom.coordinates[1][0][1] == pytest.approx(1118889.974353909)


# Multi-geometries
def test_transform_multipoint(transformer_4326_to_3857):
    geom = MultiPoint([(0, 0), (10, 20)])
    transformed_geom = transformer_4326_to_3857.transform_geojson_feature_geometry(geom)
    assert isinstance(transformed_geom, MultiPoint)
    assert len(transformed_geom.coordinates) == 2
    assert transformed_geom.coordinates[0][0] == pytest.approx(0)
    assert transformed_geom.coordinates[1][0] == pytest.approx(1113194.9079327358)

def test_transform_multilinestring(transformer_4326_to_3857):
    geom = MultiLineString([[(0,0),(1,1)], [(10,20),(21,22)]])
    transformed_geom = transformer_4326_to_3857.transform_geojson_feature_geometry(geom)
    assert isinstance(transformed_geom, MultiLineString)
    assert len(transformed_geom.coordinates) == 2
    assert len(transformed_geom.coordinates[0]) == 2
    assert transformed_geom.coordinates[1][0][0] == pytest.approx(1113194.9079327358) # 10,20

def test_transform_multipolygon(transformer_4326_to_3857):
    coords = [
        [[[0,0],[1,0],[1,1],[0,1],[0,0]]], # Polygon 1
        [[[10,10],[11,10],[11,11],[10,11],[10,10]]] # Polygon 2
    ]
    geom = MultiPolygon(coords)
    transformed_geom = transformer_4326_to_3857.transform_geojson_feature_geometry(geom)
    assert isinstance(transformed_geom, MultiPolygon)
    assert len(transformed_geom.coordinates) == 2
    assert len(transformed_geom.coordinates[0][0]) == 5
    assert transformed_geom.coordinates[1][0][0][0] == pytest.approx(1113194.9079327358)

# Z-values
def test_transform_point_with_z(transformer_4326_to_3857):
    geom = Point((0, 0, 100))
    transformed_geom = transformer_4326_to_3857.transform_geojson_feature_geometry(geom)
    assert isinstance(transformed_geom, Point)
    assert transformed_geom.coordinates[0] == pytest.approx(0)
    assert transformed_geom.coordinates[1] == pytest.approx(0)
    assert transformed_geom.coordinates[2] == 100 # Z value preserved by map_tuples

def test_transform_linestring_with_z(transformer_4326_to_3857):
    geom = LineString([(0, 0, 100), (10, 20, 200)])
    transformed_geom = transformer_4326_to_3857.transform_geojson_feature_geometry(geom)
    assert isinstance(transformed_geom, LineString)
    assert transformed_geom.coordinates[0][2] == 100
    assert transformed_geom.coordinates[1][2] == 200

def test_transform_geometry_collection(transformer_4326_to_3857):
    # map_tuples handles GeometryCollection
    geom = GeometryCollection([Point((0,0)), LineString([(1,1),(2,2,20)])])
    transformed_geom = transformer_4326_to_3857.transform_geojson_feature_geometry(geom)
    assert isinstance(transformed_geom, GeometryCollection)
    assert len(transformed_geom.geometries) == 2
    assert isinstance(transformed_geom.geometries[0], Point)
    assert transformed_geom.geometries[0].coordinates[0] == pytest.approx(0)
    assert isinstance(transformed_geom.geometries[1], LineString)
    assert transformed_geom.geometries[1].coordinates[0][0] == pytest.approx(111319.49079327358) # 1,1
    assert transformed_geom.geometries[1].coordinates[1][2] == 20 # Z value


# Error handling and invalid inputs
def test_transform_uninitialized(transformer_uninitialized):
    geom = Point((0,0))
    with pytest.raises(ValueError, match="转换器未初始化"):
        transformer_uninitialized.transform_geojson_feature_geometry(geom)

def test_transform_invalid_geometry_object_type(transformer_4326_to_3857):
    # Test with something that is not a geojson.base.GeoJSON object
    with pytest.raises(TypeError, match="输入的几何对象必须是geojson库的几何类型"):
        transformer_4326_to_3857.transform_geojson_feature_geometry({"type": "Point", "coordinates": [0,0]}) # type: ignore

def test_transform_unsupported_geojson_lib_type(transformer_4326_to_3857):
    # Test with a valid geojson lib object, but not a geometry (e.g. Feature)
    # The method expects geojson.geometry.Geometry, not geojson.Feature
    feature = geojson.Feature(geometry=Point((0,0)))
    with pytest.raises(TypeError, match="不支持的GeoJSON对象类型进行坐标转换: 'Feature'"):
        transformer_4326_to_3857.transform_geojson_feature_geometry(feature) # type: ignore

# Tests for invalid coordinate structures are now largely handled by the geojson library's own validation
# upon object creation. If map_tuples or the transform_coords callback has specific input expectations
# not covered by geojson object validity, those could be tested here.
# For instance, if transform_coords expected only 2D points but received 3D.
# However, the current transform_coords handles this by passing *coords_tuple.

def test_proj_error_on_transform(mocker, transformer_4326_to_3857):
    geom = Point((0,0))
    # Mock the internal transformer's transform method to raise ProjError
    mocker.patch.object(transformer_4326_to_3857.transformer, 'transform', side_effect=ProjError("Mock Proj Error"))
    with pytest.raises(ValueError, match="坐标转换失败: Mock Proj Error"):
        transformer_4326_to_3857.transform_geojson_feature_geometry(geom)

# Removed old dictionary-based error tests like test_transform_missing_type_key,
# test_transform_missing_coordinates_key, test_transform_unsupported_type (dict-based),
# test_transform_geometry_collection_direct (dict-based), and test_transform_invalid_coordinate_structures
# as these are now handled by geojson library object validation or different error types.

# --- Tests for the transform-geojson-file tool via handle_call_tool ---

# Base GeoJSON structures as dictionaries for server input
BASE_GEOJSON_POINT_DICT = {"type": "Point", "coordinates": [10, 20]}
BASE_GEOJSON_LINESTRING_DICT = {"type": "LineString", "coordinates": [[10, 20], [30, 40]]}
BASE_GEOJSON_POLYGON_DICT = {"type": "Polygon", "coordinates": [[[0,0], [10,0], [10,10], [0,10], [0,0]]]}

@pytest.mark.asyncio
async def test_handle_call_tool_feature_collection():
    feature_collection = {
        "type": "FeatureCollection",
        "features": [
            {"type": "Feature", "geometry": deepcopy(BASE_GEOJSON_POINT_DICT), "properties": {"name": "point1"}},
            {"type": "Feature", "geometry": deepcopy(BASE_GEOJSON_LINESTRING_DICT), "properties": {"name": "line1"}},
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
    feature = {"type": "Feature", "geometry": deepcopy(BASE_GEOJSON_POLYGON_DICT), "properties": {"id": 123}}
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
        "geojson_content": json.dumps(deepcopy(BASE_GEOJSON_POINT_DICT))
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
        "geojson_content": json.dumps(BASE_GEOJSON_POINT_DICT)
    }
    with pytest.raises(ValueError, match="无效的源坐标系"): # This matches the error from CoordinateTransformer
        await handle_call_tool(name="transform-geojson-file", arguments=arguments)

@pytest.mark.asyncio
async def test_handle_call_tool_toplevel_geometry_collection():
    # With geojson library, GeometryCollection can be transformed by map_tuples
    geom_collection_dict = {"type": "GeometryCollection", "geometries": [deepcopy(BASE_GEOJSON_POINT_DICT)]}
    arguments = {
        "source_crs": "EPSG:4326",
        "target_crs": "EPSG:3857",
        "geojson_content": json.dumps(geom_collection_dict)
    }
    result = await handle_call_tool(name="transform-geojson-file", arguments=arguments)
    transformed_data = json.loads(result[0].text.split("GeoJSON转换成功 (从 EPSG:4326 到 EPSG:3857):\n")[1]) # type: ignore
    assert transformed_data["type"] == "GeometryCollection"
    assert len(transformed_data["geometries"]) == 1
    assert transformed_data["geometries"][0]["type"] == "Point"
    assert transformed_data["geometries"][0]["coordinates"][0] == pytest.approx(1113194.9079327358)


@pytest.mark.asyncio
async def test_handle_call_tool_feature_collection_with_transform_error_on_one_feature(mocker):
    # Mock transform_geojson_feature_geometry to raise error for a specific geometry
    # The mocked method now expects a geojson object and should return one or raise error
    
    def mock_transform_with_error(self_transformer_instance, geom_obj): # Renamed self to self_transformer_instance
        # geom_obj is now a geojson.geometry.Geometry object
        if geom_obj.type == "LineString": # Let's say LineString fails
            raise ValueError("Mocked transformation error for LineString from transform_geojson_feature_geometry") # map_tuples re-raises ProjError as ValueError
        # For other types, perform a "passthrough" transformation for simplicity in mock
        return geom_obj 

    mocker.patch(
        'src.mcp_server_proj.core.transformation.CoordinateTransformer.transform_geojson_feature_geometry',
        side_effect=mock_transform_with_error,
        autospec=True # Keep autospec if it helps with signature matching
    )
    
    feature_collection = {
        "type": "FeatureCollection",
        "features": [
            {"type": "Feature", "geometry": deepcopy(BASE_GEOJSON_POINT_DICT), "properties": {"name": "point1"}},
            {"type": "Feature", "geometry": deepcopy(BASE_GEOJSON_LINESTRING_DICT), "properties": {"name": "line1_fails"}},
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
    # mocker.stopall() # mocker.patch is function-scoped by default, no need to stopall usually


@pytest.mark.asyncio
async def test_handle_call_tool_null_arguments():
    with pytest.raises(ValueError, match="缺少参数"):
        await handle_call_tool(name="transform-geojson-file", arguments=None)

@pytest.mark.asyncio
async def test_handle_call_tool_feature_collection_invalid_feature_structure():
    # This test needs to be adapted because geojson.GeoJSON.to_instance will likely fail first
    # if the structure is fundamentally not GeoJSON compliant.
    feature_collection_str = '{"type": "FeatureCollection", "features": [{"type": "Feature", "geometry": null}, "not a feature dict"]}'
    arguments = {
        "source_crs": "EPSG:4326",
        "target_crs": "EPSG:3857",
        "geojson_content": feature_collection_str
    }
    # Expecting error from geojson.GeoJSON.to_instance or subsequent validation in server.py
    with pytest.raises(ValueError, match="无效的GeoJSON内容: 结构或内容不符合GeoJSON规范|FeatureCollection中的第 2 个要素无效"):
        await handle_call_tool(name="transform-geojson-file", arguments=arguments)


@pytest.mark.asyncio
async def test_handle_call_tool_feature_collection_missing_features_key():
    # geojson library will raise error if 'features' is missing for FeatureCollection
    feature_collection_str = '{"type": "FeatureCollection", "geoms": [] }' # 'geoms' instead of 'features'
    arguments = {
        "source_crs": "EPSG:4326",
        "target_crs": "EPSG:3857",
        "geojson_content": feature_collection_str
    }
    with pytest.raises(ValueError, match="无效的GeoJSON内容: 结构或内容不符合GeoJSON规范"):
        await handle_call_tool(name="transform-geojson-file", arguments=arguments)

@pytest.mark.asyncio
async def test_handle_call_tool_feature_missing_geometry_key():
    # geojson library will raise error if 'geometry' is missing for Feature
    feature_str = '{"type": "Feature", "props": {}}' # 'props' instead of 'geometry'
    arguments = {
        "source_crs": "EPSG:4326",
        "target_crs": "EPSG:3857",
        "geojson_content": feature_str
    }
    with pytest.raises(ValueError, match="无效的GeoJSON内容: 结构或内容不符合GeoJSON规范"):
        await handle_call_tool(name="transform-geojson-file", arguments=arguments)


@pytest.mark.asyncio
async def test_handle_call_tool_unsupported_geojson_type_in_server():
    # geojson.GeoJSON.to_instance will fail if "SomeCustomType" is not a valid GeoJSON type string
    geojson_data_str = '{"type": "SomeCustomType", "coordinates": [1,2,3]}'
    arguments = {
        "source_crs": "EPSG:4326",
        "target_crs": "EPSG:3857",
        "geojson_content": geojson_data_str
    }
    with pytest.raises(ValueError, match="无效的GeoJSON内容: 结构或内容不符合GeoJSON规范"): # Error from to_instance
        await handle_call_tool(name="transform-geojson-file", arguments=arguments)
