import os
import csv
from typing import Dict, Tuple, Optional
from pathlib import Path


DEFAULT_MAPPINGS = {
    "minecraft:air": ("minecraft:air", 0),
    "minecraft:stone": ("minecraft:stone", 0),
    "minecraft:granite": ("minecraft:stone", 1),
    "minecraft:polished_granite": ("minecraft:stone", 2),
    "minecraft:diorite": ("minecraft:stone", 3),
    "minecraft:polished_diorite": ("minecraft:stone", 4),
    "minecraft:andesite": ("minecraft:stone", 5),
    "minecraft:polished_andesite": ("minecraft:stone", 6),
    "minecraft:grass_block": ("minecraft:grass", 0),
    "minecraft:dirt": ("minecraft:dirt", 0),
    "minecraft:coarse_dirt": ("minecraft:dirt", 1),
    "minecraft:podzol": ("minecraft:dirt", 2),
    "minecraft:cobblestone": ("minecraft:cobblestone", 0),
    "minecraft:oak_planks": ("minecraft:planks", 0),
    "minecraft:spruce_planks": ("minecraft:planks", 1),
    "minecraft:birch_planks": ("minecraft:planks", 2),
    "minecraft:jungle_planks": ("minecraft:planks", 3),
    "minecraft:acacia_planks": ("minecraft:planks", 4),
    "minecraft:dark_oak_planks": ("minecraft:planks", 5),
    "minecraft:oak_sapling": ("minecraft:sapling", 0),
    "minecraft:bedrock": ("minecraft:bedrock", 0),
    "minecraft:water": ("minecraft:water", 0),
    "minecraft:lava": ("minecraft:lava", 0),
    "minecraft:sand": ("minecraft:sand", 0),
    "minecraft:red_sand": ("minecraft:sand", 1),
    "minecraft:gravel": ("minecraft:gravel", 0),
    "minecraft:gold_ore": ("minecraft:gold_ore", 0),
    "minecraft:iron_ore": ("minecraft:iron_ore", 0),
    "minecraft:coal_ore": ("minecraft:coal_ore", 0),
    "minecraft:oak_log[axis=y]": ("minecraft:log", 0),
    "minecraft:spruce_log[axis=y]": ("minecraft:log", 1),
    "minecraft:birch_log[axis=y]": ("minecraft:log", 2),
    "minecraft:jungle_log[axis=y]": ("minecraft:log", 3),
    "minecraft:oak_leaves[distance=7,persistent=true]": ("minecraft:leaves", 0),
    "minecraft:sponge": ("minecraft:sponge", 0),
    "minecraft:glass": ("minecraft:glass", 0),
    "minecraft:lapis_ore": ("minecraft:lapis_ore", 0),
    "minecraft:sandstone": ("minecraft:sandstone", 0),
    "minecraft:white_wool": ("minecraft:wool", 0),
    "minecraft:orange_wool": ("minecraft:wool", 1),
    "minecraft:magenta_wool": ("minecraft:wool", 2),
    "minecraft:light_blue_wool": ("minecraft:wool", 3),
    "minecraft:yellow_wool": ("minecraft:wool", 4),
    "minecraft:lime_wool": ("minecraft:wool", 5),
    "minecraft:pink_wool": ("minecraft:wool", 6),
    "minecraft:gray_wool": ("minecraft:wool", 7),
    "minecraft:light_gray_wool": ("minecraft:wool", 8),
    "minecraft:cyan_wool": ("minecraft:wool", 9),
    "minecraft:purple_wool": ("minecraft:wool", 10),
    "minecraft:blue_wool": ("minecraft:wool", 11),
    "minecraft:brown_wool": ("minecraft:wool", 12),
    "minecraft:green_wool": ("minecraft:wool", 13),
    "minecraft:red_wool": ("minecraft:wool", 14),
    "minecraft:black_wool": ("minecraft:wool", 15),
    "minecraft:gold_block": ("minecraft:gold_block", 0),
    "minecraft:iron_block": ("minecraft:iron_block", 0),
    "minecraft:bricks": ("minecraft:brick_block", 0),
    "minecraft:bookshelf": ("minecraft:bookshelf", 0),
    "minecraft:mossy_cobblestone": ("minecraft:mossy_cobblestone", 0),
    "minecraft:obsidian": ("minecraft:obsidian", 0),
    "minecraft:torch": ("minecraft:torch", 0),
    "minecraft:chest": ("minecraft:chest", 0),
    "minecraft:diamond_ore": ("minecraft:diamond_ore", 0),
    "minecraft:diamond_block": ("minecraft:diamond_block", 0),
    "minecraft:crafting_table": ("minecraft:crafting_table", 0),
    "minecraft:farmland": ("minecraft:farmland", 0),
    "minecraft:furnace": ("minecraft:furnace", 0),
    "minecraft:ladder": ("minecraft:ladder", 0),
    "minecraft:redstone_ore": ("minecraft:redstone_ore", 0),
    "minecraft:snow": ("minecraft:snow_layer", 0),
    "minecraft:ice": ("minecraft:ice", 0),
    "minecraft:snow_block": ("minecraft:snow", 0),
    "minecraft:clay": ("minecraft:clay", 0),
    "minecraft:netherrack": ("minecraft:netherrack", 0),
    "minecraft:soul_sand": ("minecraft:soul_sand", 0),
    "minecraft:glowstone": ("minecraft:glowstone", 0),
    "minecraft:stone_bricks": ("minecraft:stonebrick", 0),
    "minecraft:glass_pane": ("minecraft:glass_pane", 0),
    "minecraft:prismarine": ("etfuturum:prismarine", 0),
    "minecraft:prismarine_bricks": ("etfuturum:prismarine", 1),
    "minecraft:dark_prismarine": ("etfuturum:prismarine", 2),
    "minecraft:sea_lantern": ("etfuturum:sea_lantern", 0),
    "minecraft:magma_block": ("etfuturum:magma", 0),
    "minecraft:bone_block": ("etfuturum:bone_block", 0),
    "minecraft:copper_block": ("etfuturum:copper_block", 0),
    "minecraft:tuff": ("etfuturum:tuff", 0),
    "minecraft:calcite": ("etfuturum:calcite", 0),
    "minecraft:deepslate": ("etfuturum:deepslate", 0),
    "minecraft:netherite_block": ("etfuturum:netherite_block", 0),
    "minecraft:ancient_debris": ("etfuturum:ancient_debris", 0),
    "minecraft:blackstone": ("etfuturum:blackstone", 0),
    "minecraft:stripped_oak_log": ("etfuturum:stripped_log", 0),
    "minecraft:stripped_spruce_log": ("etfuturum:stripped_log", 1),
}


class MappingManager:
    """
    两级映射管理器
    
    阶段一：高版本名称 -> 低版本名称 (静态映射)
    阶段二：低版本名称 -> 动态数字ID (通过 NEI blocks.csv)
    """
    
    def __init__(self):
        self._static_mappings: Dict[str, Tuple[str, int]] = {}
        self._dynamic_id_map: Dict[str, int] = {}
        self._custom_mappings_file: str = "custom_mappings.txt"
        self._csv_loaded = False
        
        self._load_default_mappings()
        self._load_custom_mappings()
    
    def _load_default_mappings(self):
        for high_name, (low_name, meta) in DEFAULT_MAPPINGS.items():
            self._static_mappings[high_name] = (low_name, meta)
    
    def _load_custom_mappings(self):
        if os.path.exists(self._custom_mappings_file):
            self._load_static_mappings_from_file(self._custom_mappings_file)
    
    def _load_static_mappings_from_file(self, filepath: str) -> int:
        count = 0
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    parts = line.split('\t')
                    if len(parts) >= 3:
                        high_name = parts[0]
                        low_name = parts[1]
                        try:
                            meta = int(parts[2])
                            self._static_mappings[high_name] = (low_name, meta)
                            count += 1
                        except ValueError:
                            continue
        except Exception:
            pass
        return count
    
    def load_static_mappings(self, filepath: str) -> int:
        count = self._load_static_mappings_from_file(filepath)
        return count
    
    def load_nei_csv(self, filepath: str) -> int:
        """
        加载 NEI 导出的 blocks.csv
        格式：名称,数字ID,...
        """
        count = 0
        self._dynamic_id_map.clear()
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 2:
                        block_name = row[0].strip()
                        try:
                            block_id = int(row[1].strip())
                            self._dynamic_id_map[block_name] = block_id
                            count += 1
                        except ValueError:
                            continue
            self._csv_loaded = True
        except Exception as e:
            self._csv_loaded = False
            raise e
        
        return count
    
    def is_csv_loaded(self) -> bool:
        return self._csv_loaded
    
    def get_static_mapping(self, high_version_id: str) -> Optional[Tuple[str, int]]:
        """
        阶段一：获取静态映射
        返回 (低版本名称, Metadata) 或 None
        """
        if high_version_id in self._static_mappings:
            return self._static_mappings[high_version_id]
        
        base_name = high_version_id.split('[')[0]
        if base_name in self._static_mappings:
            return self._static_mappings[base_name]
        
        return None
    
    def get_dynamic_id(self, low_version_name: str) -> Optional[int]:
        """
        阶段二：获取动态数字ID
        """
        if low_version_name in self._dynamic_id_map:
            return self._dynamic_id_map[low_version_name]
        
        base_name = low_version_name.split('[')[0]
        if base_name in self._dynamic_id_map:
            return self._dynamic_id_map[base_name]
        
        return None
    
    def get_full_mapping(self, high_version_id: str) -> Optional[Tuple[int, int]]:
        """
        完整映射：高版本名称 -> 数字ID + Metadata
        返回 (数字ID, Metadata) 或 None
        """
        static_result = self.get_static_mapping(high_version_id)
        if static_result is None:
            return None
        
        low_name, meta = static_result
        dynamic_id = self.get_dynamic_id(low_name)
        
        if dynamic_id is None:
            return None
        
        return (dynamic_id, meta)
    
    def has_static_mapping(self, high_version_id: str) -> bool:
        return self.get_static_mapping(high_version_id) is not None
    
    def has_dynamic_id(self, low_version_name: str) -> bool:
        return self.get_dynamic_id(low_version_name) is not None
    
    def add_static_mapping(self, high_version_id: str, low_version_name: str, meta: int, save_to_file: bool = True):
        self._static_mappings[high_version_id] = (low_version_name, meta)
        
        if save_to_file:
            with open(self._custom_mappings_file, 'a', encoding='utf-8') as f:
                f.write(f"{high_version_id}\t{low_version_name}\t{meta}\n")
    
    def add_static_mappings(self, mappings: Dict[str, Tuple[str, int]], save_to_file: bool = True):
        for high_name, (low_name, meta) in mappings.items():
            self._static_mappings[high_name] = (low_name, meta)
        
        if save_to_file:
            with open(self._custom_mappings_file, 'a', encoding='utf-8') as f:
                for high_name, (low_name, meta) in mappings.items():
                    f.write(f"{high_name}\t{low_name}\t{meta}\n")
    
    def get_static_mapping_count(self) -> int:
        return len(self._static_mappings)
    
    def get_dynamic_id_count(self) -> int:
        return len(self._dynamic_id_map)
    
    def get_default_mapping_count(self) -> int:
        return len(DEFAULT_MAPPINGS)
    
    def get_custom_mapping_count(self) -> int:
        return len(self._static_mappings) - len(DEFAULT_MAPPINGS)
    
    def reload(self):
        self._static_mappings.clear()
        self._dynamic_id_map.clear()
        self._csv_loaded = False
        self._load_default_mappings()
        self._load_custom_mappings()
