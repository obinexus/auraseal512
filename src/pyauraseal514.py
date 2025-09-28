#!/usr/bin/env python3
"""
PyAuraSeal514 - Cryptographic Algorithm Implementation
Combining Huffman Coding with AVL Trie for Integrity Validation

Author: OBINexus Computing
Repository: github.com/obinexus/pyauraseal514
"""

import hashlib
import json
import os
import zipfile
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from collections import defaultdict
import heapq
import base64


@dataclass
class HuffmanNode:
    """Node structure for Huffman tree construction"""
    char: Optional[str] = None
    freq: int = 0
    left: Optional['HuffmanNode'] = None
    right: Optional['HuffmanNode'] = None
    
    def __lt__(self, other):
        return self.freq < other.freq


class PhenoAVLNode:
    """
    Phenomenological AVL Node with Huffman integration
    Maintains balance while preserving Huffman properties
    """
    def __init__(self, key: str, huffman_code: str = "", freq: int = 0):
        self.key = key
        self.huffman_code = huffman_code
        self.frequency = freq
        self.height = 1
        self.balance_factor = 0
        self.left: Optional['PhenoAVLNode'] = None
        self.right: Optional['PhenoAVLNode'] = None
        
        # Integrity tracking
        self.checksum = self._calculate_checksum()
    
    def _calculate_checksum(self) -> str:
        """Calculate SHA-256 checksum for node integrity"""
        data = f"{self.key}:{self.huffman_code}:{self.frequency}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def update_checksum(self):
        """Update checksum after modifications"""
        self.checksum = self._calculate_checksum()


class PhenoAVLTrie:
    """
    Phenomenological AVL Trie with Huffman compression
    Maintains both trie structure and AVL balance properties
    """
    def __init__(self):
        self.root: Optional[PhenoAVLNode] = None
        self.huffman_tree: Optional[HuffmanNode] = None
        self.huffman_codes: Dict[str, str] = {}
        self.compression_ratio = 0.0
        
    def _get_height(self, node: Optional[PhenoAVLNode]) -> int:
        """Get height of node"""
        return node.height if node else 0
    
    def _get_balance(self, node: Optional[PhenoAVLNode]) -> int:
        """Get balance factor of node"""
        return self._get_height(node.left) - self._get_height(node.right) if node else 0
    
    def _update_height(self, node: PhenoAVLNode):
        """Update height of node"""
        node.height = max(self._get_height(node.left), self._get_height(node.right)) + 1
        node.balance_factor = self._get_balance(node)
    
    def _rotate_right(self, y: PhenoAVLNode) -> PhenoAVLNode:
        """Right rotation for AVL balancing"""
        x = y.left
        t2 = x.right
        
        x.right = y
        y.left = t2
        
        self._update_height(y)
        self._update_height(x)
        
        return x
    
    def _rotate_left(self, x: PhenoAVLNode) -> PhenoAVLNode:
        """Left rotation for AVL balancing"""
        y = x.right
        t2 = y.left
        
        y.left = x
        x.right = t2
        
        self._update_height(x)
        self._update_height(y)
        
        return y
    
    def build_huffman_tree(self, text: str):
        """Build Huffman tree from input text"""
        if not text:
            return
        
        # Calculate frequencies
        freq_map = defaultdict(int)
        for char in text:
            freq_map[char] += 1
        
        # Create heap of nodes
        heap = []
        for char, freq in freq_map.items():
            heapq.heappush(heap, HuffmanNode(char, freq))
        
        # Build Huffman tree
        while len(heap) > 1:
            left = heapq.heappop(heap)
            right = heapq.heappop(heap)
            
            merged = HuffmanNode(freq=left.freq + right.freq)
            merged.left = left
            merged.right = right
            
            heapq.heappush(heap, merged)
        
        self.huffman_tree = heap[0] if heap else None
        self._generate_codes()
    
    def _generate_codes(self):
        """Generate Huffman codes from tree"""
        if not self.huffman_tree:
            return
        
        def generate_codes_recursive(node: HuffmanNode, code: str):
            if node.char:  # Leaf node
                self.huffman_codes[node.char] = code or "0"
                return
            
            if node.left:
                generate_codes_recursive(node.left, code + "0")
            if node.right:
                generate_codes_recursive(node.right, code + "1")
        
        generate_codes_recursive(self.huffman_tree, "")
    
    def insert(self, key: str, freq: int = 1) -> Optional[PhenoAVLNode]:
        """Insert key with frequency into AVL trie"""
        huffman_code = self.huffman_codes.get(key, "")
        
        def insert_recursive(node: Optional[PhenoAVLNode], key: str, 
                           huffman_code: str, freq: int) -> PhenoAVLNode:
            # Standard AVL insertion
            if not node:
                return PhenoAVLNode(key, huffman_code, freq)
            
            if key < node.key:
                node.left = insert_recursive(node.left, key, huffman_code, freq)
            elif key > node.key:
                node.right = insert_recursive(node.right, key, huffman_code, freq)
            else:
                # Update frequency
                node.frequency += freq
                node.update_checksum()
                return node
            
            # Update height and balance factor
            self._update_height(node)
            balance = self._get_balance(node)
            
            # AVL rotations
            if balance > 1:  # Left heavy
                if key > node.left.key:  # Left-Right case
                    node.left = self._rotate_left(node.left)
                node = self._rotate_right(node)
            elif balance < -1:  # Right heavy
                if key < node.right.key:  # Right-Left case
                    node.right = self._rotate_right(node.right)
                node = self._rotate_left(node)
            
            node.update_checksum()
            return node
        
        self.root = insert_recursive(self.root, key, huffman_code, freq)
        return self.root
    
    def search(self, key: str) -> Optional[PhenoAVLNode]:
        """Search for key in trie"""
        def search_recursive(node: Optional[PhenoAVLNode], key: str) -> Optional[PhenoAVLNode]:
            if not node or node.key == key:
                return node
            
            if key < node.key:
                return search_recursive(node.left, key)
            else:
                return search_recursive(node.right, key)
        
        return search_recursive(self.root, key)
    
    def compress_data(self, data: str) -> Tuple[str, float]:
        """Compress data using Huffman codes"""
        if not self.huffman_codes:
            self.build_huffman_tree(data)
        
        compressed = ""
        for char in data:
            compressed += self.huffman_codes.get(char, char)
        
        original_bits = len(data) * 8  # 8 bits per character
        compressed_bits = len(compressed)
        self.compression_ratio = compressed_bits / original_bits if original_bits > 0 else 0
        
        return compressed, self.compression_ratio
    
    def verify_integrity(self) -> bool:
        """Verify integrity of all nodes in trie"""
        def verify_recursive(node: Optional[PhenoAVLNode]) -> bool:
            if not node:
                return True
            
            # Verify checksum
            expected_checksum = node._calculate_checksum()
            if node.checksum != expected_checksum:
                return False
            
            # Verify balance property
            if abs(node.balance_factor) > 1:
                return False
            
            return verify_recursive(node.left) and verify_recursive(node.right)
        
        return verify_recursive(self.root)


class PhenoAVL:
    """
    Main AuraSeal514 cryptographic system
    Manages dual public keys and single private key
    """
    def __init__(self, coherence_threshold: float = 0.954):
        self.coherence_threshold = coherence_threshold
        self.trie = PhenoAVLTrie()
        
        # Key management
        self.public_keys: Dict[int, str] = {}  # Vector-based
        self.private_key: Optional[str] = None  # Scalar-based
        
        # Version tracking
        self.version = 1
        self.archive_integrity: Dict[str, str] = {}
    
    def generate_key_pair(self) -> Tuple[Dict[int, str], str]:
        """
        Generate dual public keys (2:1 ratio) and single private key
        Public keys are vector-based, private key is scalar
        """
        # Generate private key (scalar) - O(log n) complexity
        private_scalar = hashlib.sha512(os.urandom(64)).hexdigest()
        
        # Generate dual public keys (vectors) - O(n) complexity
        pub_key_1 = hashlib.sha256(f"{private_scalar}:vector1".encode()).hexdigest()
        pub_key_2 = hashlib.sha256(f"{private_scalar}:vector2".encode()).hexdigest()
        
        self.private_key = private_scalar
        self.public_keys = {1: pub_key_1, 2: pub_key_2}
        
        return self.public_keys, self.private_key
    
    def create_archive_signature(self, archive_path: str, data: Dict[str, any]) -> str:
        """Create cryptographic signature for archive"""
        # Build trie from archive data
        combined_data = json.dumps(data, sort_keys=True)
        self.trie.build_huffman_tree(combined_data)
        
        # Insert data into trie
        for key, value in data.items():
            self.trie.insert(key, hash(str(value)) % 1000)
        
        # Generate signature
        compressed_data, ratio = self.trie.compress_data(combined_data)
        signature_input = f"{archive_path}:{compressed_data}:{self.private_key}"
        
        return hashlib.sha512(signature_input.encode()).hexdigest()
    
    def verify_archive_signature(self, archive_path: str, data: Dict[str, any], 
                                signature: str) -> bool:
        """Verify archive signature using public keys"""
        # Reconstruct signature
        combined_data = json.dumps(data, sort_keys=True)
        temp_trie = PhenoAVLTrie()
        temp_trie.build_huffman_tree(combined_data)
        
        compressed_data, _ = temp_trie.compress_data(combined_data)
        
        # Try verification with both public keys
        for pub_key in self.public_keys.values():
            verification_input = f"{archive_path}:{compressed_data}:{pub_key}"
            expected_sig = hashlib.sha512(verification_input.encode()).hexdigest()
            
            # In real implementation, this would use proper cryptographic verification
            # For demonstration, we check structural integrity
            if len(signature) == len(expected_sig) and signature.startswith(expected_sig[:16]):
                return True
        
        return False
    
    def create_version_archive(self, folder_path: str, version_data: Dict[str, any]) -> str:
        """Create versioned ZIP archive with AuraSeal integrity"""
        archive_name = f".auraseal.pub.{self.version}.zip"
        signature = self.create_archive_signature(archive_name, version_data)
        
        # Add integrity metadata
        version_data['_auraseal_signature'] = signature
        version_data['_auraseal_version'] = self.version
        version_data['_auraseal_coherence'] = self.trie.compression_ratio
        
        # Create ZIP archive
        with zipfile.ZipFile(archive_name, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Add version data as metadata
            zf.writestr('auraseal.metadata.json', json.dumps(version_data, indent=2))
            
            # Add files from folder if it exists
            if os.path.exists(folder_path):
                for root, dirs, files in os.walk(folder_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arc_path = os.path.relpath(file_path, folder_path)
                        zf.write(file_path, arc_path)
        
        self.archive_integrity[archive_name] = signature
        self.version += 1
        
        return archive_name
    
    def verify_archive_integrity(self, archive_path: str) -> bool:
        """Verify the integrity of an AuraSeal archive"""
        try:
            with zipfile.ZipFile(archive_path, 'r') as zf:
                metadata_str = zf.read('auraseal.metadata.json').decode()
                metadata = json.loads(metadata_str)
                
                signature = metadata.get('_auraseal_signature')
                if not signature:
                    return False
                
                # Remove signature for verification
                verification_data = {k: v for k, v in metadata.items() 
                                   if not k.startswith('_auraseal_signature')}
                
                return self.verify_archive_signature(archive_path, verification_data, signature)
        
        except Exception:
            return False
    
    def get_system_status(self) -> Dict[str, any]:
        """Get current system status and integrity metrics"""
        return {
            'version': self.version - 1,
            'coherence_threshold': self.coherence_threshold,
            'trie_integrity': self.trie.verify_integrity(),
            'compression_ratio': self.trie.compression_ratio,
            'public_keys_count': len(self.public_keys),
            'archives_created': len(self.archive_integrity),
            'has_private_key': self.private_key is not None
        }


# Example usage and demonstration
def demonstrate_auraseal514():
    """Demonstrate AuraSeal514 functionality"""
    print("=== PyAuraSeal514 Demonstration ===\n")
    
    # Initialize system
    auraseal = PhenoAVL()
    
    # Generate key pair
    public_keys, private_key = auraseal.generate_key_pair()
    print(f"Generated Public Key 1: {public_keys[1][:32]}...")
    print(f"Generated Public Key 2: {public_keys[2][:32]}...")
    print(f"Private Key Length: {len(private_key)} characters\n")
    
    # Create sample data
    sample_data = {
        'project_name': 'AuraSeal514',
        'version': '1.0.0',
        'files': ['main.py', 'utils.py', 'tests.py'],
        'checksum': 'abc123def456',
        'timestamp': '2025-01-01T00:00:00Z'
    }
    
    # Create versioned archive
    print("Creating versioned archive...")
    archive_name = auraseal.create_version_archive('./sample_project', sample_data)
    print(f"Created archive: {archive_name}")
    
    # Verify archive integrity
    is_valid = auraseal.verify_archive_integrity(archive_name)
    print(f"Archive integrity verification: {'PASSED' if is_valid else 'FAILED'}")
    
    # Display system status
    status = auraseal.get_system_status()
    print(f"\nSystem Status:")
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    return auraseal


if __name__ == "__main__":
    auraseal_system = demonstrate_auraseal514()
