import sys
import os
from typing import Dict, Tuple, List, Optional
from PyQt6.QtCore import QThread, pyqtSignal, QObject, QCoreApplication

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.converter import ConversionEngine, ConversionResult, UnmappedBlockInfo
from core.mapping_manager import MappingManager


class ConversionWorker(QThread):
    """
    转换工作线程
    在独立线程中执行 NBT 解析和文件转换
    """
    
    progress = pyqtSignal(int, int, str)
    log = pyqtSignal(str)
    finished = pyqtSignal(bool, str, str)
    unmapped_blocks_found = pyqtSignal(list)
    
    def __init__(self, input_files: List[str], output_dir: str, mapping_manager: MappingManager):
        super().__init__()
        self.input_files = input_files
        self.output_dir = output_dir
        self.mapping_manager = mapping_manager
        self._engine: Optional[ConversionEngine] = None
        self._pending_mappings: Optional[Dict[str, Tuple[str, int]]] = None
        self._waiting_for_mapping = False
        self._cancelled = False
    
    def run(self):
        self._engine = ConversionEngine(self.mapping_manager)
        self._engine.set_progress_callback(self._on_progress)
        self._engine.set_unmapped_callback(self._on_unmapped_blocks)
        
        total_files = len(self.input_files)
        
        for i, input_file in enumerate(self.input_files):
            if self._cancelled:
                self.log.emit("转换已取消")
                self.finished.emit(False, "转换已取消", "")
                return
            
            self.log.emit(f"正在处理文件 ({i+1}/{total_files}): {os.path.basename(input_file)}")
            
            result = self._engine.convert(input_file, self.output_dir)
            
            if result.success:
                self.log.emit(f"✓ {result.message}")
            else:
                self.log.emit(f"✗ {result.message}")
                self.finished.emit(False, result.message, "")
                return
        
        self.log.emit(f"所有文件转换完成! 共处理 {total_files} 个文件")
        self.finished.emit(True, f"成功转换 {total_files} 个文件", self.output_dir)
    
    def _on_progress(self, current: int, total: int, message: str):
        self.progress.emit(current, total, message)
    
    def _on_unmapped_blocks(self, unmapped: List[UnmappedBlockInfo]) -> Optional[Dict[str, Tuple[str, int]]]:
        self._waiting_for_mapping = True
        self._pending_mappings = None
        
        self.unmapped_blocks_found.emit(unmapped)
        
        while self._waiting_for_mapping:
            QCoreApplication.processEvents()
            self.msleep(50)
            
            if self._cancelled:
                return None
        
        return self._pending_mappings
    
    def provide_mappings(self, mappings: Dict[str, Tuple[str, int]]):
        self._pending_mappings = mappings
        self._waiting_for_mapping = False
    
    def cancel_mapping(self):
        self._pending_mappings = None
        self._waiting_for_mapping = False
        self._cancelled = True
    
    def cancel(self):
        self._cancelled = True
        if self._engine:
            self._engine.cancel()
        self._waiting_for_mapping = False
