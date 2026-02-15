from nbtlib import Compound, List, ByteArray, String, Short, File
from nbtlib import load as nbt_load
from typing import Dict, Tuple, List as TypingList, Optional


class SchematicWriter:
    """
    MCEdit .schematic 文件写入器
    支持 1.12.2 格式，可处理超过 4096 的方块 ID
    
    NBT 结构:
    - Width, Height, Length: Short
    - Materials: String ("Alpha" or "Classic")
    - Blocks: ByteArray (低 8 位方块 ID)
    - Data: ByteArray (方块元数据)
    - AddBlocks: ByteArray (可选，高 4 位附加 ID)
    - Entities: List[Compound]
    - TileEntities: List[Compound]
    """
    
    def __init__(self, width: int, height: int, length: int):
        self.width = width
        self.height = height
        self.length = length
        self.materials = "Alpha"
        self._blocks: TypingList[int] = [0] * (width * height * length)
        self._data: TypingList[int] = [0] * (width * height * length)
        self._add_blocks: TypingList[int] = []
        self._entities: TypingList[Compound] = []
        self._tile_entities: TypingList[Compound] = []
        self._has_add_blocks = False
    
    def set_block(self, x: int, y: int, z: int, block_id: int, metadata: int):
        """
        设置指定位置的方块
        
        对于 ID >= 256 的方块:
        - Blocks 数组存储低 8 位 (block_id & 0xFF)
        - AddBlocks 数组存储高 4 位 ((block_id >> 8) & 0xF)
        
        注意: AddBlocks 采用紧凑存储，每字节存储两个方块的高 4 位
        """
        index = self._get_index(x, y, z)
        
        if block_id > 255:
            self._has_add_blocks = True
            self._blocks[index] = block_id & 0xFF
            self._set_add_block(index, (block_id >> 8) & 0xF)
        else:
            self._blocks[index] = block_id
        
        self._data[index] = metadata & 0xF
    
    def _get_index(self, x: int, y: int, z: int) -> int:
        return (y * self.length + z) * self.width + x
    
    def _set_add_block(self, index: int, add_value: int):
        """
        设置 AddBlocks 数组
        AddBlocks 采用紧凑存储: 每个字节存储两个方块的高 4 位
        - 偶数索引: 低 4 位
        - 奇数索引: 高 4 位
        """
        add_index = index // 2
        while len(self._add_blocks) <= add_index:
            self._add_blocks.append(0)
        
        if index % 2 == 0:
            self._add_blocks[add_index] = (self._add_blocks[add_index] & 0xF0) | (add_value & 0x0F)
        else:
            self._add_blocks[add_index] = (self._add_blocks[add_index] & 0x0F) | ((add_value & 0x0F) << 4)
    
    def add_entity(self, entity: Compound):
        self._entities.append(entity)
    
    def add_tile_entity(self, tile_entity: Compound):
        self._tile_entities.append(tile_entity)
    
    def build_nbt(self) -> Compound:
        nbt_data = Compound({
            'Width': Short(self.width),
            'Height': Short(self.height),
            'Length': Short(self.length),
            'Materials': String(self.materials),
            'Blocks': ByteArray(self._blocks),
            'Data': ByteArray(self._data),
            'Entities': List[Compound](self._entities),
            'TileEntities': List[Compound](self._tile_entities),
        })
        
        if self._has_add_blocks:
            nbt_data['AddBlocks'] = ByteArray(self._add_blocks)
        
        return nbt_data
    
    def save(self, filepath: str):
        nbt_data = self.build_nbt()
        nbt_file = File({'Schematic': nbt_data})
        nbt_file.save(filepath)


class SchemReader:
    """
    Sponge .schem 文件读取器
    解析 1.13+ 版本的 Sponge Schematic 格式
    
    NBT 结构:
    - Width, Height, Length: Short
    - Version: Int
    - Palette: Compound (方块名称 -> 索引)
    - BlockData: ByteArray (VarInt 索引数组)
    - BlockEntities: List[Compound]
    - Entities: List[Compound]
    """
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self._nbt: Optional[Compound] = None
        self.width: int = 0
        self.height: int = 0
        self.length: int = 0
        self.palette: Dict[str, int] = {}
        self._palette_max: int = 0
        self._block_data: bytes = b''
        self._block_entities: TypingList[Compound] = []
        self._entities: TypingList[Compound] = []
    
    def read(self):
        self._nbt = nbt_load(self.filepath)
        
        self.width = int(self._nbt.get('Width', Short(0)))
        self.height = int(self._nbt.get('Height', Short(0)))
        self.length = int(self._nbt.get('Length', Short(0)))
        
        palette_data = self._nbt.get('Palette', Compound({}))
        for name, index in palette_data.items():
            self.palette[name] = int(index)
        
        if self.palette:
            self._palette_max = max(self.palette.values()) + 1
        
        self._block_data = bytes(self._nbt.get('BlockData', ByteArray([])))
        
        self._block_entities = list(self._nbt.get('BlockEntities', List[Compound]([])))
        self._entities = list(self._nbt.get('Entities', List[Compound]([])))
        
        return self
    
    def get_block_indices(self) -> TypingList[int]:
        """
        解析 BlockData 中的 VarInt 数组
        返回每个方块位置的 Palette 索引列表
        """
        indices = []
        data = self._block_data
        offset = 0
        
        while offset < len(data):
            value, offset = self._read_varint(data, offset)
            indices.append(value)
        
        return indices
    
    def _read_varint(self, data: bytes, offset: int) -> Tuple[int, int]:
        """
        读取一个 VarInt 值
        返回 (值, 新偏移量)
        """
        value = 0
        shift = 0
        
        while True:
            if offset >= len(data):
                break
            
            byte = data[offset]
            offset += 1
            
            value |= (byte & 0x7F) << shift
            shift += 7
            
            if not (byte & 0x80):
                break
        
        return value, offset
    
    def get_block_name_by_index(self, palette_index: int) -> Optional[str]:
        """
        根据 Palette 索引获取方块名称
        """
        for name, idx in self.palette.items():
            if idx == palette_index:
                return name
        return None
    
    def get_block_entities(self) -> TypingList[Compound]:
        return self._block_entities
    
    def get_entities(self) -> TypingList[Compound]:
        return self._entities
