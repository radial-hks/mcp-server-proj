from pyproj import CRS, Transformer, ProjError
from typing import Optional # Dict, Any, and copy will be removed or replaced by geojson types
import geojson # Added
import geojson.utils # Added

class CoordinateTransformer:
    def __init__(self):
        self.source_crs: Optional[CRS] = None
        self.target_crs: Optional[CRS] = None
        self.transformer: Optional[Transformer] = None
    
    def set_source_crs(self, crs: str) -> None:
        """设置源坐标系"""
        try:
            print("设置源坐标系:",crs)
            self.source_crs = CRS.from_string(crs)
        except Exception as e:
            raise ValueError(f"无效的源坐标系: {str(e)}")
    
    def set_target_crs(self, crs: str) -> None:
        """设置目标坐标系"""
        try:
            print("设置目标坐标系:",crs)
            self.target_crs = CRS.from_string(crs)
        except Exception as e:
            raise ValueError(f"无效的目标坐标系: {str(e)}")
    
    def initialize_transformer(self) -> bool:
        """初始化转换器"""
        if self.source_crs is None or self.target_crs is None:
            raise ValueError("源坐标系和目标坐标系必须都设置")
        
        try:
            self.transformer = Transformer.from_crs(
                self.source_crs, 
                self.target_crs,
                always_xy=True
            )
            return True
        except Exception as e:
            raise ValueError(f"无法初始化转换器: {str(e)}")
    
    def transform_point(self, x: float, y: float) -> tuple:
        """转换单个坐标点"""
        if self.transformer is None:
            raise ValueError("转换器未初始化")
        
        try:
            return self.transformer.transform(x, y)
        except Exception as e:
            raise ValueError(f"坐标转换失败: {str(e)}")
    
    def transform_geometry(self, geometry) -> bool:
        """转换几何对象"""
        if self.transformer is None:
            raise ValueError("转换器未初始化")
        
        try:
            # 使用pyproj的transform方法转换几何对象
            # This method's signature and return type seem mismatched with typical GeoJSON handling.
            # It's kept as is from original code, but transform_geojson_feature_geometry is added for clarity.
            return self.transformer.transform(geometry) # Assuming 'geometry' here is not a GeoJSON dict based on transform signature
        except Exception as e:
            raise ValueError(f"几何对象转换失败: {str(e)}")

    def transform_geojson_feature_geometry(self, geom: geojson.geometry.Geometry) -> geojson.geometry.Geometry:
        """
        Transforms a GeoJSON geometry object using the initialized transformer.
        This method now uses the 'geojson' library.

        :param geom: A geojson.geometry.Geometry object.
        :return: A new geojson.geometry.Geometry object with transformed coordinates.
        :raises ValueError: If the transformer is not initialized or if a ProjError occurs during transformation.
        :raises TypeError: If the input `geom` is not a valid geojson geometry type handled by geojson.utils.map_tuples.
        """
        if self.transformer is None:
            raise ValueError("转换器未初始化 (Transformer not initialized)")

        if not isinstance(geom, geojson.base.GeoJSON):
             # Check if it's a base GeoJSON type, which includes Geometry types
            raise TypeError(f"输入的几何对象必须是geojson库的几何类型 (Input geometry must be a geojson library geometry type, got {type(geom)})")
        
        # Ensure it's a geometry type that map_tuples can handle (not Feature, FeatureCollection here)
        # geojson.utils.map_tuples works on Geometry types (Point, LineString, Polygon, etc.)
        # and also on GeometryCollection.
        if not hasattr(geom, 'type') or geom.type not in [
            "Point", "LineString", "Polygon", 
            "MultiPoint", "MultiLineString", "MultiPolygon", 
            "GeometryCollection"
        ]:
            raise TypeError(f"不支持的GeoJSON对象类型进行坐标转换: '{geom.type if hasattr(geom, 'type') else 'Unknown'}' (Unsupported GeoJSON object type for coordinate transformation: '{geom.type if hasattr(geom, 'type') else 'Unknown'}')")


        def transform_coords(coords_tuple):
            """Transforms a single coordinate tuple (x, y) or (x, y, z)."""
            try:
                # self.transformer.transform can take *args, so unpacking the tuple works
                return self.transformer.transform(*coords_tuple)
            except ProjError as e:
                # Re-raise ProjError as ValueError for consistent error handling by the caller
                raise ValueError(f"坐标转换失败: {str(e)} (Coordinate transformation failed: {str(e)})")
            except Exception as e: # Catch other potential errors from transform itself
                raise ValueError(f"坐标转换时发生意外错误: {str(e)} (Unexpected error during coordinate transformation: {str(e)})")

        try:
            # geojson.utils.map_tuples iterates over coordinates and applies transform_coords.
            # It returns a new geometry object of the same type as the input.
            transformed_geom = geojson.utils.map_tuples(transform_coords, geom)
            return transformed_geom
        except ValueError: # Catch ValueError raised by transform_coords
            raise
        except Exception as e:
            # Catch any other unexpected errors during map_tuples or other geojson lib operations
            raise ValueError(f"GeoJSON几何对象转换过程中发生意外错误: {str(e)} (An unexpected error occurred during GeoJSON geometry transformation: {str(e)})")
