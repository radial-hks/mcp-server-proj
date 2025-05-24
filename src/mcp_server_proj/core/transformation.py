from pyproj import CRS, Transformer, ProjError
from typing import Optional, Dict, Any
import copy

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

    def transform_geojson_feature_geometry(self, geometry_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transforms a GeoJSON geometry object using the initialized transformer.

        :param geometry_dict: A GeoJSON geometry object (as a Python dictionary).
        :return: The transformed GeoJSON geometry object (as a Python dictionary).
        :raises ValueError: If the transformer is not initialized, the input is not a valid
                            GeoJSON geometry, a ProjError occurs, or any other transformation error.
        :raises TypeError: If the input geometry_dict is not a dictionary.
        :raises NotImplementedError: If the geometry type is not supported.
        """
        if self.transformer is None:
            raise ValueError("转换器未初始化 (Transformer not initialized)")

        if not isinstance(geometry_dict, dict):
            raise TypeError("输入的几何对象必须是字典类型 (Input geometry must be a dictionary)")

        if 'type' not in geometry_dict:
            raise ValueError("输入的GeoJSON几何对象无效: 缺少 'type' 键 (Invalid GeoJSON geometry: missing 'type' key)")

        # Create a deep copy to avoid modifying the original dictionary
        # Do this after initial type checks to ensure 'type' key exists.
        transformed_geometry_dict = copy.deepcopy(geometry_dict)
        geom_type = transformed_geometry_dict['type'] # Already checked for 'type' key

        if geom_type == 'GeometryCollection':
            if 'geometries' not in transformed_geometry_dict: # Check geometries for GeometryCollection
                raise ValueError(f"输入的GeoJSON几何对象无效: 类型 '{geom_type}' 缺少 'geometries' 键 (Invalid GeoJSON geometry: type '{geom_type}' missing 'geometries' key)")
            # This method does not process GeometryCollection further, will be caught by NotImplementedError later
        elif 'coordinates' not in transformed_geometry_dict: # For other types, 'coordinates' is expected
            raise ValueError(f"输入的GeoJSON几何对象无效: 类型 '{geom_type}' 缺少 'coordinates' 键 (Invalid GeoJSON geometry: type '{geom_type}' missing 'coordinates' key)")
        
        original_coordinates = transformed_geometry_dict.get('coordinates') # Use .get() as it might be GeometryCollection

        try:
            if geom_type == 'Point':
                if not (isinstance(original_coordinates, list) and len(original_coordinates) >= 2 and 
                        all(isinstance(c, (int, float)) for c in original_coordinates[:2])):
                    raise ValueError("点的坐标格式无效 (Invalid coordinates for Point)")
                x, y = original_coordinates[0], original_coordinates[1]
                new_x, new_y = self.transformer.transform(x, y)
                # Preserve potential Z coordinate if present
                new_coords = [new_x, new_y]
                if len(original_coordinates) > 2:
                    new_coords.extend(original_coordinates[2:])
                transformed_geometry_dict['coordinates'] = new_coords
            
            elif geom_type == 'LineString':
                if not isinstance(original_coordinates, list) or not all(isinstance(p, list) and len(p) >= 2 for p in original_coordinates):
                    raise ValueError("线字符串的坐标格式无效 (Invalid coordinates for LineString)")
                new_coords_list = []
                for point_coords in original_coordinates:
                    x, y = point_coords[0], point_coords[1]
                    new_x, new_y = self.transformer.transform(x, y)
                    new_point = [new_x, new_y]
                    if len(point_coords) > 2:
                        new_point.extend(point_coords[2:])
                    new_coords_list.append(new_point)
                transformed_geometry_dict['coordinates'] = new_coords_list

            elif geom_type == 'Polygon':
                if not isinstance(original_coordinates, list) or not all(isinstance(r, list) for r in original_coordinates):
                    raise ValueError("多边形的坐标格式无效 (Invalid coordinates for Polygon)")
                new_polygon_rings = []
                for ring in original_coordinates:
                    if not all(isinstance(p, list) and len(p) >= 2 for p in ring):
                         raise ValueError("多边形环的坐标格式无效 (Invalid coordinates for Polygon ring)")
                    new_ring_coords = []
                    for point_coords in ring:
                        x, y = point_coords[0], point_coords[1]
                        new_x, new_y = self.transformer.transform(x, y)
                        new_point = [new_x, new_y]
                        if len(point_coords) > 2:
                            new_point.extend(point_coords[2:])
                        new_ring_coords.append(new_point)
                    new_polygon_rings.append(new_ring_coords)
                transformed_geometry_dict['coordinates'] = new_polygon_rings
            
            elif geom_type in ['MultiPoint', 'MultiLineString', 'MultiPolygon']: # Removed 'GeometryCollection' from this direct processing block
                # For MultiPoint (similar logic for MultiLineString, MultiPolygon):
                if geom_type == 'MultiPoint':
                    if not isinstance(original_coordinates, list) or not all(isinstance(p, list) and len(p) >= 2 for p in original_coordinates): # original_coordinates will be non-None here
                        raise ValueError(f"{geom_type} 的坐标格式无效 (Invalid coordinates for {geom_type})")
                    new_multi_coords = []
                    for point_coords in original_coordinates: # original_coordinates is not None
                        x, y = point_coords[0], point_coords[1]
                        new_x, new_y = self.transformer.transform(x, y)
                        new_point = [new_x, new_y]
                        if len(point_coords) > 2:
                            new_point.extend(point_coords[2:])
                        new_multi_coords.append(new_point)
                    transformed_geometry_dict['coordinates'] = new_multi_coords
                elif geom_type == 'MultiLineString':
                    if not isinstance(original_coordinates, list) or not all(isinstance(ls, list) for ls in original_coordinates): # original_coordinates is not None
                         raise ValueError(f"{geom_type} 的坐标格式无效 (Invalid coordinates for {geom_type})")
                    new_multi_line_coords = []
                    for linestring_coords in original_coordinates: # original_coordinates is not None
                        if not all(isinstance(p, list) and len(p) >= 2 for p in linestring_coords):
                            raise ValueError(f"{geom_type} 中线字符串的坐标格式无效 (Invalid LineString coordinates in {geom_type})")
                        current_line = []
                        for point_coords in linestring_coords:
                            x, y = point_coords[0], point_coords[1]
                            new_x, new_y = self.transformer.transform(x, y)
                            new_point = [new_x, new_y]
                            if len(point_coords) > 2:
                                new_point.extend(point_coords[2:])
                            current_line.append(new_point)
                        new_multi_line_coords.append(current_line)
                    transformed_geometry_dict['coordinates'] = new_multi_line_coords
                elif geom_type == 'MultiPolygon':
                    if not isinstance(original_coordinates, list) or not all(isinstance(poly, list) for poly in original_coordinates): # original_coordinates is not None
                        raise ValueError(f"{geom_type} 的坐标格式无效 (Invalid coordinates for {geom_type})")
                    new_multi_poly_coords = []
                    for polygon_rings in original_coordinates: # original_coordinates is not None
                        if not all(isinstance(r, list) for r in polygon_rings):
                            raise ValueError(f"{geom_type} 中多边形的坐标格式无效 (Invalid Polygon coordinates in {geom_type})")
                        current_poly = []
                        for ring in polygon_rings:
                            if not all(isinstance(p, list) and len(p) >= 2 for p in ring):
                                raise ValueError(f"{geom_type} 中多边形环的坐标格式无效 (Invalid Polygon ring coordinates in {geom_type})")
                            current_ring = []
                            for point_coords in ring:
                                x, y = point_coords[0], point_coords[1]
                                new_x, new_y = self.transformer.transform(x, y)
                                new_point = [new_x, new_y]
                                if len(point_coords) > 2:
                                    new_point.extend(point_coords[2:])
                                current_ring.append(new_point)
                            current_poly.append(current_ring)
                        new_multi_poly_coords.append(current_poly)
                    transformed_geometry_dict['coordinates'] = new_multi_poly_coords
            # GeometryCollection will fall through to the final else
            else: # Handles GeometryCollection and any other unknown types
                raise NotImplementedError(f"几何类型 '{geom_type}' 暂不支持转换 (Geometry type '{geom_type}' is not yet supported for transformation)")

        except ProjError as e:
            raise ValueError(f"坐标转换失败: {str(e)} (Coordinate transformation failed due to ProjError: {str(e)})")
        except (TypeError, IndexError, KeyError) as e:
            # More specific error for bad structure if not caught by initial checks
            raise ValueError(f"GeoJSON几何对象结构无效或坐标处理错误: {str(e)} (Invalid GeoJSON geometry structure or coordinate processing error: {str(e)})")
        except NotImplementedError: # Re-raise not implemented error
            raise
        except Exception as e:
            # Catch any other unexpected errors during transformation logic
            raise ValueError(f"几何对象转换过程中发生意外错误: {str(e)} (An unexpected error occurred during geometry transformation: {str(e)})")
            
        return transformed_geometry_dict
