from pyproj import CRS, Transformer
from typing import Optional

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
            return self.transformer.transform(geometry)
        except Exception as e:
            raise ValueError(f"几何对象转换失败: {str(e)}")
