import os
from typing import Dict, Tuple, List, Optional, Callable
from pathlib import Path
from dataclasses import dataclass

from .nbt_handler import SchemReader, SchematicWriter
from .mapping_manager import MappingManager


@dataclass
class UnmappedBlockInfo:
    high_version_name: str
    reason: str
    suggested_low_name: str = ""


class ConversionResult:
    def __init__(self, success: bool, message: str, output_path: str = "", unmapped_blocks: List[UnmappedBlockInfo] = None):
        self.success = success
        self.message = message
        self.output_path = output_path
        self.unmapped_blocks = unmapped_blocks or []


class ConversionEngine:
    """
    蓝图转换引擎
    将 .schem 文件转换为 .schematic 文件
    
    使用两级映射：
    1. 高版本名称 -> 低版本名称 (静态映射)
    2. 低版本名称 -> 动态数字ID (NEI CSV)
    """
    
    def __init__(self, mapping_manager: MappingManager):
        self.mapping_manager = mapping_manager
        self._progress_callback: Optional[Callable[[int, int, str], None]] = None
        self._unmapped_callback: Optional[Callable[[List[UnmappedBlockInfo]], Dict[str, Tuple[str, int]]]] = None
        self._cancelled = False
    
    def set_progress_callback(self, callback: Callable[[int, int, str], None]):
        self._progress_callback = callback
    
    def set_unmapped_callback(self, callback: Callable[[List[UnmappedBlockInfo]], Dict[str, Tuple[str, int]]]):
        self._unmapped_callback = callback
    
    def cancel(self):
        self._cancelled = True
    
    def convert(self, input_path: str, output_dir: str) -> ConversionResult:
        """
        执行转换
        """
        self._cancelled = False
        
        if not self.mapping_manager.is_csv_loaded():
            return ConversionResult(False, "请先导入 NEI blocks.csv 文件")
        
        try:
            if self._progress_callback:
                self._progress_callback(0, 100, f"正在读取文件: {os.path.basename(input_path)}")
            
            reader = SchemReader(input_path)
            reader.read()
            
            width, height, length = reader.width, reader.height, reader.length
            total_blocks = width * height * length
            
            if total_blocks == 0:
                return ConversionResult(False, "蓝图文件为空或无效")
            
            writer = SchematicWriter(width, height, length)
            
            block_indices = reader.get_block_indices()
            
            unmapped_blocks: Dict[str, UnmappedBlockInfo] = {}
            temp_mappings: Dict[str, Tuple[str, int]] = {}
            blocks_need_id: Dict[str, Tuple[str, int]] = {}
            
            if self._progress_callback:
                self._progress_callback(10, 100, "正在解析方块数据...")
            
            for i, palette_index in enumerate(block_indices):
                if self._cancelled:
                    return ConversionResult(False, "转换已取消")
                
                x = i % width
                z = (i // width) % length
                y = i // (width * length)
                
                block_name = reader.get_block_name_by_index(palette_index)
                
                if block_name is None:
                    continue
                
                result = self._get_full_mapping_with_temp(block_name, temp_mappings)
                
                if result is None:
                    unmapped_info = self._diagnose_unmapped(block_name, temp_mappings)
                    if block_name not in unmapped_blocks:
                        unmapped_blocks[block_name] = unmapped_info
                    writer.set_block(x, y, z, 0, 0)
                else:
                    block_id, metadata = result
                    writer.set_block(x, y, z, block_id, metadata)
                
                if self._progress_callback and i % 1000 == 0:
                    progress = 10 + int((i / total_blocks) * 70)
                    self._progress_callback(progress, 100, f"正在转换方块... ({i}/{total_blocks})")
            
            if unmapped_blocks:
                if self._unmapped_callback:
                    new_mappings = self._unmapped_callback(list(unmapped_blocks.values()))
                    
                    if new_mappings is None:
                        return ConversionResult(False, "转换已取消")
                    
                    temp_mappings.update(new_mappings)
                    
                    for block_name, (low_name, meta) in new_mappings.items():
                        dynamic_id = self.mapping_manager.get_dynamic_id(low_name)
                        if dynamic_id is not None:
                            for i, palette_index in enumerate(block_indices):
                                high_name = reader.get_block_name_by_index(palette_index)
                                if high_name == block_name:
                                    x = i % width
                                    z = (i // width) % length
                                    y = i // (width * length)
                                    writer.set_block(x, y, z, dynamic_id, meta)
                        else:
                            self._log_missing_dynamic_id(low_name)
                else:
                    return ConversionResult(
                        False, 
                        f"发现未映射的方块: {', '.join([b.high_version_name for b in unmapped_blocks.values()])}",
                        unmapped_blocks=list(unmapped_blocks.values())
                    )
            
            if self._progress_callback:
                self._progress_callback(85, 100, "正在写入输出文件...")
            
            input_name = Path(input_path).stem
            output_path = os.path.join(output_dir, f"{input_name}.schematic")
            
            writer.save(output_path)
            
            if self._progress_callback:
                self._progress_callback(100, 100, "转换完成!")
            
            return ConversionResult(True, f"转换成功: {output_path}", output_path)
            
        except Exception as e:
            return ConversionResult(False, f"转换失败: {str(e)}")
    
    def _get_full_mapping_with_temp(self, high_version_id: str, temp_mappings: Dict[str, Tuple[str, int]]) -> Optional[Tuple[int, int]]:
        if high_version_id in temp_mappings:
            low_name, meta = temp_mappings[high_version_id]
            dynamic_id = self.mapping_manager.get_dynamic_id(low_name)
            if dynamic_id is not None:
                return (dynamic_id, meta)
            return None
        
        return self.mapping_manager.get_full_mapping(high_version_id)
    
    def _diagnose_unmapped(self, high_version_id: str, temp_mappings: Dict[str, Tuple[str, int]]) -> UnmappedBlockInfo:
        static_result = self.mapping_manager.get_static_mapping(high_version_id)
        
        if static_result is None:
            return UnmappedBlockInfo(
                high_version_name=high_version_id,
                reason="缺少静态映射",
                suggested_low_name=""
            )
        else:
            low_name, meta = static_result
            return UnmappedBlockInfo(
                high_version_name=high_version_id,
                reason=f"CSV中缺少ID: {low_name}",
                suggested_low_name=low_name
            )
    
    def _log_missing_dynamic_id(self, low_name: str):
        pass
