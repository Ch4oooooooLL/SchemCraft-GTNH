import sys
import os
from typing import Dict, Tuple, List, Optional
from pathlib import Path

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTextEdit, QFileDialog, QListWidget, QListWidgetItem,
    QProgressBar, QMessageBox, QSplitter, QFrame, QGroupBox
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QColor

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.mapping_manager import MappingManager
from core.converter import UnmappedBlockInfo
from gui.worker import ConversionWorker
from gui.mapping_dialog import MappingDialog


class MainWindow(QMainWindow):
    """
    主窗口 - Windows 11 风格
    """
    
    def __init__(self):
        super().__init__()
        
        self._mapping_manager: Optional[MappingManager] = None
        self._worker: Optional[ConversionWorker] = None
        self._input_files: List[str] = []
        self._output_dir: str = ""
        self._pending_dialog: Optional[MappingDialog] = None
        
        self._setup_window()
        self._setup_ui()
        self._init_mapping_manager()
    
    def _setup_window(self):
        self.setWindowTitle("SchemaCrafter GUI - GTNH 专版")
        self.setMinimumSize(900, 700)
        self.resize(1000, 750)
        
        self.setStyleSheet("""
            QMainWindow {
                background-color: #202020;
            }
            QWidget {
                background-color: #202020;
                color: #ffffff;
                font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
            }
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1084d8;
            }
            QPushButton:pressed {
                background-color: #006cbd;
            }
            QPushButton:disabled {
                background-color: #4a4a4a;
                color: #888888;
            }
            QPushButton#secondaryBtn {
                background-color: #3d3d3d;
            }
            QPushButton#secondaryBtn:hover {
                background-color: #4d4d4d;
            }
            QPushButton#convertBtn {
                background-color: #107c10;
                font-size: 16px;
                padding: 12px 32px;
            }
            QPushButton#convertBtn:hover {
                background-color: #0e6e0e;
            }
            QPushButton#convertBtn:disabled {
                background-color: #2d4a2d;
            }
            QPushButton#cancelBtn {
                background-color: #d13438;
            }
            QPushButton#cancelBtn:hover {
                background-color: #c12a2e;
            }
            QListWidget {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 4px;
            }
            QListWidget::item {
                padding: 4px;
                border-radius: 2px;
            }
            QListWidget::item:selected {
                background-color: #0078d4;
            }
            QTextEdit {
                background-color: #1e1e1e;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 8px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 13px;
            }
            QProgressBar {
                background-color: #2d2d2d;
                border: none;
                border-radius: 4px;
                text-align: center;
                height: 24px;
            }
            QProgressBar::chunk {
                background-color: #0078d4;
                border-radius: 4px;
            }
            QLabel {
                font-size: 14px;
            }
            QLabel#titleLabel {
                font-size: 24px;
                font-weight: bold;
            }
            QLabel#sectionLabel {
                font-size: 16px;
                font-weight: 600;
                color: #cccccc;
            }
            QLabel#statusLabel {
                color: #888888;
                padding: 6px 12px;
                background-color: #2d2d2d;
                border-radius: 4px;
            }
            QLabel#statusOk {
                color: #4fc3f7;
            }
            QLabel#statusWarn {
                color: #ffb74d;
            }
        """)
    
    def _setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(12)
        
        title_label = QLabel("SchemaCrafter GUI")
        title_label.setObjectName("titleLabel")
        main_layout.addWidget(title_label)
        
        subtitle_label = QLabel("GTNH 专版 - 将 1.13+ 蓝图 (.schem) 转换为 1.7.10/1.12.2 蓝图 (.schematic)")
        subtitle_label.setStyleSheet("color: #888888; font-size: 14px;")
        main_layout.addWidget(subtitle_label)
        
        main_layout.addSpacing(12)
        
        data_section = QLabel("数据源配置")
        data_section.setObjectName("sectionLabel")
        main_layout.addWidget(data_section)
        
        data_layout = QHBoxLayout()
        
        static_layout = QVBoxLayout()
        static_header = QHBoxLayout()
        self._load_static_btn = QPushButton("导入静态字典 (可选)")
        self._load_static_btn.setObjectName("secondaryBtn")
        self._load_static_btn.clicked.connect(self._on_load_static_mappings)
        static_header.addWidget(self._load_static_btn)
        static_header.addStretch()
        static_layout.addLayout(static_header)
        
        self._static_status_label = QLabel("已加载 0 条自定义映射")
        self._static_status_label.setObjectName("statusLabel")
        static_layout.addWidget(self._static_status_label)
        
        data_layout.addLayout(static_layout)
        
        csv_layout = QVBoxLayout()
        csv_header = QHBoxLayout()
        self._load_csv_btn = QPushButton("导入 NEI blocks.csv (必选)")
        self._load_csv_btn.setObjectName("secondaryBtn")
        self._load_csv_btn.clicked.connect(self._on_load_nei_csv)
        csv_header.addWidget(self._load_csv_btn)
        csv_header.addStretch()
        csv_layout.addLayout(csv_header)
        
        self._csv_status_label = QLabel("未加载 CSV 文件")
        self._csv_status_label.setObjectName("statusLabel")
        csv_layout.addWidget(self._csv_status_label)
        
        data_layout.addLayout(csv_layout)
        
        main_layout.addLayout(data_layout)
        
        main_layout.addSpacing(8)
        
        file_section = QLabel("文件操作")
        file_section.setObjectName("sectionLabel")
        main_layout.addWidget(file_section)
        
        input_layout = QHBoxLayout()
        
        self._file_list = QListWidget()
        self._file_list.setMinimumHeight(80)
        self._file_list.setMaximumHeight(120)
        input_layout.addWidget(self._file_list, 1)
        
        input_btn_layout = QVBoxLayout()
        
        self._select_files_btn = QPushButton("选择蓝图文件")
        self._select_files_btn.setObjectName("secondaryBtn")
        self._select_files_btn.clicked.connect(self._on_select_files)
        input_btn_layout.addWidget(self._select_files_btn)
        
        self._clear_files_btn = QPushButton("清空列表")
        self._clear_files_btn.setObjectName("secondaryBtn")
        self._clear_files_btn.clicked.connect(self._on_clear_files)
        input_btn_layout.addWidget(self._clear_files_btn)
        
        input_btn_layout.addStretch()
        input_layout.addLayout(input_btn_layout)
        
        main_layout.addLayout(input_layout)
        
        output_layout = QHBoxLayout()
        self._output_path_label = QLabel("未选择输出目录")
        self._output_path_label.setObjectName("statusLabel")
        output_layout.addWidget(self._output_path_label, 1)
        
        self._select_output_btn = QPushButton("选择输出目录")
        self._select_output_btn.setObjectName("secondaryBtn")
        self._select_output_btn.clicked.connect(self._on_select_output)
        output_layout.addWidget(self._select_output_btn)
        
        main_layout.addLayout(output_layout)
        
        main_layout.addSpacing(12)
        
        self._progress_bar = QProgressBar()
        self._progress_bar.setValue(0)
        self._progress_bar.setFormat("%p% - %v/%m")
        self._progress_bar.setVisible(False)
        main_layout.addWidget(self._progress_bar)
        
        convert_layout = QHBoxLayout()
        convert_layout.addStretch()
        
        self._convert_btn = QPushButton("开始转换")
        self._convert_btn.setObjectName("convertBtn")
        self._convert_btn.clicked.connect(self._on_start_conversion)
        self._convert_btn.setEnabled(False)
        convert_layout.addWidget(self._convert_btn)
        
        self._cancel_btn = QPushButton("取消")
        self._cancel_btn.setObjectName("cancelBtn")
        self._cancel_btn.setVisible(False)
        self._cancel_btn.clicked.connect(self._on_cancel)
        convert_layout.addWidget(self._cancel_btn)
        
        convert_layout.addStretch()
        main_layout.addLayout(convert_layout)
        
        main_layout.addSpacing(8)
        
        log_section = QLabel("转换日志")
        log_section.setObjectName("sectionLabel")
        main_layout.addWidget(log_section)
        
        self._log_text = QTextEdit()
        self._log_text.setReadOnly(True)
        main_layout.addWidget(self._log_text, 1)
        
        self._log("程序已启动")
    
    def _init_mapping_manager(self):
        try:
            self._mapping_manager = MappingManager()
            self._update_status_labels()
            self._log(f"已加载内置映射 {self._mapping_manager.get_default_mapping_count()} 条")
        except Exception as e:
            self._log(f"错误: 无法初始化映射管理器 - {e}")
    
    def _update_status_labels(self):
        if self._mapping_manager:
            custom_count = self._mapping_manager.get_custom_mapping_count()
            self._static_status_label.setText(f"已加载 {custom_count} 条自定义映射")
            
            if self._mapping_manager.is_csv_loaded():
                csv_count = self._mapping_manager.get_dynamic_id_count()
                self._csv_status_label.setText(f"已加载 {csv_count} 个游戏内 ID")
                self._csv_status_label.setStyleSheet("color: #4fc3f7; padding: 6px 12px; background-color: #2d2d2d; border-radius: 4px;")
            else:
                self._csv_status_label.setText("未加载 CSV 文件")
                self._csv_status_label.setStyleSheet("color: #ffb74d; padding: 6px 12px; background-color: #2d2d2d; border-radius: 4px;")
            
            self._convert_btn.setEnabled(self._mapping_manager.is_csv_loaded())
    
    def _log(self, message: str):
        self._log_text.append(f"[{self._get_timestamp()}] {message}")
        scrollbar = self._log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def _get_timestamp(self) -> str:
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")
    
    def _on_load_static_mappings(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择静态映射文件",
            "",
            "Text Files (*.txt);;JSON Files (*.json);;All Files (*)"
        )
        
        if file_path and self._mapping_manager:
            try:
                count = self._mapping_manager.load_static_mappings(file_path)
                self._update_status_labels()
                self._log(f"从 {os.path.basename(file_path)} 加载了 {count} 条静态映射")
            except Exception as e:
                self._log(f"加载静态映射失败: {e}")
    
    def _on_load_nei_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择 NEI blocks.csv 文件",
            "",
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if file_path and self._mapping_manager:
            try:
                count = self._mapping_manager.load_nei_csv(file_path)
                self._update_status_labels()
                self._log(f"从 {os.path.basename(file_path)} 加载了 {count} 个游戏内 ID")
            except Exception as e:
                self._log(f"加载 CSV 失败: {e}")
                QMessageBox.warning(self, "错误", f"加载 CSV 文件失败:\n{e}")
    
    def _on_select_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "选择蓝图文件",
            "",
            "Sponge Schematic Files (*.schem);;All Files (*)"
        )
        
        if files:
            for file in files:
                if file not in self._input_files:
                    self._input_files.append(file)
                    item = QListWidgetItem(os.path.basename(file))
                    item.setData(Qt.ItemDataRole.UserRole, file)
                    item.setToolTip(file)
                    self._file_list.addItem(item)
            
            self._log(f"已添加 {len(files)} 个文件")
    
    def _on_clear_files(self):
        self._input_files.clear()
        self._file_list.clear()
        self._log("已清空文件列表")
    
    def _on_select_output(self):
        directory = QFileDialog.getExistingDirectory(
            self,
            "选择输出目录",
            ""
        )
        
        if directory:
            self._output_dir = directory
            self._output_path_label.setText(directory)
            self._output_path_label.setStyleSheet("color: #ffffff; padding: 6px 12px; background-color: #2d2d2d; border-radius: 4px;")
            self._log(f"输出目录: {directory}")
    
    def _on_start_conversion(self):
        if not self._input_files:
            QMessageBox.warning(self, "警告", "请先选择要转换的蓝图文件")
            return
        
        if not self._output_dir:
            QMessageBox.warning(self, "警告", "请先选择输出目录")
            return
        
        if not self._mapping_manager or not self._mapping_manager.is_csv_loaded():
            QMessageBox.warning(self, "警告", "请先导入 NEI blocks.csv 文件")
            return
        
        self._set_ui_busy(True)
        self._progress_bar.setVisible(True)
        self._progress_bar.setValue(0)
        
        self._worker = ConversionWorker(self._input_files, self._output_dir, self._mapping_manager)
        self._worker.progress.connect(self._on_progress)
        self._worker.log.connect(self._log)
        self._worker.finished.connect(self._on_finished)
        self._worker.unmapped_blocks_found.connect(self._on_unmapped_blocks)
        
        self._worker.start()
    
    def _on_cancel(self):
        if self._worker:
            self._worker.cancel()
            self._log("正在取消转换...")
    
    def _on_progress(self, current: int, total: int, message: str):
        self._progress_bar.setMaximum(total)
        self._progress_bar.setValue(current)
    
    def _on_finished(self, success: bool, message: str, output_path: str):
        self._set_ui_busy(False)
        
        if success:
            self._progress_bar.setValue(self._progress_bar.maximum())
            QMessageBox.information(self, "完成", message)
        else:
            QMessageBox.warning(self, "失败", message)
    
    def _on_unmapped_blocks(self, unmapped: List[UnmappedBlockInfo]):
        self._pending_dialog = MappingDialog(unmapped, self)
        self._pending_dialog.mappings_ready.connect(self._on_mappings_ready)
        self._pending_dialog.cancelled.connect(self._on_mapping_cancelled)
        self._pending_dialog.exec()
    
    def _on_mappings_ready(self, mappings: Dict[str, Tuple[str, int]]):
        if self._worker:
            self._worker.provide_mappings(mappings)
            
            if self._mapping_manager:
                self._mapping_manager.add_static_mappings(mappings)
                self._update_status_labels()
                self._log(f"已保存 {len(mappings)} 条新映射到 custom_mappings.txt")
    
    def _on_mapping_cancelled(self):
        if self._worker:
            self._worker.cancel_mapping()
            self._log("用户取消了映射，转换已终止")
    
    def _set_ui_busy(self, busy: bool):
        self._select_files_btn.setEnabled(not busy)
        self._clear_files_btn.setEnabled(not busy)
        self._select_output_btn.setEnabled(not busy)
        self._load_static_btn.setEnabled(not busy)
        self._load_csv_btn.setEnabled(not busy)
        self._convert_btn.setVisible(not busy)
        self._cancel_btn.setVisible(busy)
        
        if not busy:
            self._progress_bar.setVisible(False)
    
    def closeEvent(self, event):
        if self._worker and self._worker.isRunning():
            reply = QMessageBox.question(
                self,
                "确认退出",
                "转换正在进行中，确定要退出吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return
            
            self._worker.cancel()
            self._worker.wait(2000)
        
        event.accept()
