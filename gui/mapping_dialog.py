from typing import Dict, Tuple, List, Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.converter import UnmappedBlockInfo


class MappingDialog(QDialog):
    """
    动态拦截与手动映射弹窗
    当转换引擎遇到未定义的方块时弹出
    """
    
    mappings_ready = pyqtSignal(dict)
    cancelled = pyqtSignal()
    
    def __init__(self, unmapped_blocks: List[UnmappedBlockInfo], parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._unmapped_blocks = unmapped_blocks
        self._result: Optional[Dict[str, Tuple[str, int]]] = None
        
        self.setWindowTitle("发现未映射的方块")
        self.setMinimumWidth(700)
        self.setMinimumHeight(400)
        self.setModal(True)
        
        self._setup_ui()
        self._populate_table()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        info_label = QLabel(
            "以下方块无法完成映射。\n"
            "请为每个方块填写目标低版本名称和元数据值 (Metadata)。\n"
            "提示：如果 CSV 中缺少该方块的数字 ID，需要先在游戏中添加该方块后再导出新的 blocks.csv。"
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        self._table = QTableWidget()
        self._table.setColumnCount(4)
        self._table.setHorizontalHeaderLabels(["高版本方块名称", "原因", "目标低版本名称", "Metadata"])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(1, 180)
        self._table.setColumnWidth(3, 80)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked | QAbstractItemView.EditTrigger.EditKeyPressed)
        
        layout.addWidget(self._table)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self._save_btn = QPushButton("保存并继续")
        self._save_btn.clicked.connect(self._on_save)
        self._save_btn.setDefault(True)
        
        self._ignore_btn = QPushButton("替换为空气")
        self._ignore_btn.clicked.connect(self._on_ignore)
        
        self._cancel_btn = QPushButton("终止转换")
        self._cancel_btn.clicked.connect(self._on_cancel)
        
        btn_layout.addWidget(self._save_btn)
        btn_layout.addWidget(self._ignore_btn)
        btn_layout.addWidget(self._cancel_btn)
        
        layout.addLayout(btn_layout)
    
    def _populate_table(self):
        self._table.setRowCount(len(self._unmapped_blocks))
        
        for i, block_info in enumerate(self._unmapped_blocks):
            name_item = QTableWidgetItem(block_info.high_version_name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            name_item.setToolTip(block_info.high_version_name)
            self._table.setItem(i, 0, name_item)
            
            reason_item = QTableWidgetItem(block_info.reason)
            reason_item.setFlags(reason_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            reason_item.setToolTip(block_info.reason)
            self._table.setItem(i, 1, reason_item)
            
            low_name_item = QTableWidgetItem(block_info.suggested_low_name)
            low_name_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self._table.setItem(i, 2, low_name_item)
            
            meta_item = QTableWidgetItem("0")
            meta_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(i, 3, meta_item)
    
    def _get_mappings_from_table(self) -> Dict[str, Tuple[str, int]]:
        mappings = {}
        
        for i in range(self._table.rowCount()):
            high_name = self._table.item(i, 0).text()
            low_name = self._table.item(i, 2).text().strip()
            
            if not low_name:
                low_name = "minecraft:air"
            
            try:
                metadata = int(self._table.item(i, 3).text())
            except ValueError:
                metadata = 0
            
            mappings[high_name] = (low_name, metadata)
        
        return mappings
    
    def _on_save(self):
        mappings = self._get_mappings_from_table()
        self._result = mappings
        self.mappings_ready.emit(mappings)
        self.accept()
    
    def _on_ignore(self):
        selected_rows = self._table.selectionModel().selectedRows()
        
        if not selected_rows:
            return
        
        for index in sorted([idx.row() for idx in selected_rows]):
            self._table.item(index, 2).setText("minecraft:air")
            self._table.item(index, 3).setText("0")
            self._table.item(index, 0).setBackground(QColor(60, 60, 60))
            self._table.item(index, 1).setBackground(QColor(60, 60, 60))
            self._table.item(index, 2).setBackground(QColor(60, 60, 60))
            self._table.item(index, 3).setBackground(QColor(60, 60, 60))
    
    def _on_cancel(self):
        self._result = None
        self.cancelled.emit()
        self.reject()
    
    def get_result(self) -> Optional[Dict[str, Tuple[str, int]]]:
        return self._result
