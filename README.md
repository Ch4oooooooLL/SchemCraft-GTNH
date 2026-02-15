# SchemaCrafter GUI (GTNH 专版)

跨版本 Minecraft 蓝图降级转换器，专为《格雷科技：新视野 (GTNH)》等大型模组整合包设计。

## 功能特性

- 将 1.13+ 蓝图 (`.schem`) 转换为 1.7.10/1.12.2 蓝图 (`.schematic`)
- **两级映射引擎**：
  - 阶段一：高版本名称 → 低版本名称 (静态映射)
  - 阶段二：低版本名称 → 动态数字ID (NEI CSV)
- 支持 GTNH 等突破 4096 ID 限制的特供版 WorldEdit
- Windows 11 Fluent Design 风格界面
- 动态拦截未映射方块，支持手动映射

## 安装

```bash
pip install -r requirements.txt
```

## 使用方法

### 1. 运行程序

```bash
python main.py
```

### 2. 导入数据源

1. **导入静态字典 (可选)**：加载额外的方块映射规则文件
2. **导入 NEI blocks.csv (必选)**：从游戏内 NEI 导出的 CSV 文件

### 3. 选择文件并转换

1. 选择要转换的 `.schem` 蓝图文件
2. 选择输出目录
3. 点击"开始转换"

## NEI blocks.csv 导出方法

1. 进入游戏，打开 NEI 物品面板
2. 按下导出快捷键导出方块列表
3. 将生成的 `blocks.csv` 文件导入程序

## 映射文件格式

静态映射文件 (`.txt`) 格式：
```
高版本方块名称	低版本方块名称	Metadata
minecraft:copper_block	etfuturum:copper_block	0
```

## 打包为 EXE

```bash
.\build.bat
```

## 技术栈

- Python 3.9+
- PyQt6
- nbtlib
- PyInstaller

## 许可证

MIT License
