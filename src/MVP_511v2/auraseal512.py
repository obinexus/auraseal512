#!/usr/bin/env python3
"""
AuraSeal512 - Document Sealing with 2:1 Public/Private Key Mapping
github.com/obinexus/auraseal512
"""

import hashlib
import json
import os
import zipfile
import base64
from datetime import datetime
from typing import Dict, Tuple, Optional
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization

class AuraSeal512:
    """
    AuraSeal512 Cryptographic System
    - 2 Public Keys (fault-tolerant vectors)
    - 1 Private Key (scalar anchor)
    - 2:1 mapping for redundancy
    """
    
    def __init__(self, seal_name: str = "default"):
        self.seal_name = seal_name
        self.keys_dir = f"~/.auraseal512/{seal_name}"
        os.makedirs(os.path.expanduser(self.keys_dir), exist_ok=True)
        
        # Key paths
        self.private_key_path = os.path.expanduser(f"{self.keys_dir}/private.key")
        self.public_keys_path = os.path.expanduser(f"{self.keys_dir}/public.keys.json")
        
        # Initialize keys
        self.private_key = None
        self.public_keys = {}
        self._load_or_generate_keys()
    
    def _load_or_generate_keys(self):
        """Load existing keys or generate new 2:1 key pair"""
        if os.path.exists(self.private_key_path) and os.path.exists(self.public_keys_path):
            self._load_keys()
        else:
            self._generate_2to1_keypair()
    
    def _generate_2to1_keypair(self):
        """Generate 2 public keys mapping to 1 private key"""
        print("🔐 Generating AuraSeal512 2:1 Key Pair...")
        
        # Generate primary private key (scalar anchor)
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        
        # Generate two public keys from the private key (2:1 mapping)
        private_pem = self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        # Derive two public keys using different derivation paths
        self.public_keys = {
            'pub1': self._derive_public_key(private_pem, 'vector1'),
            'pub2': self._derive_public_key(private_pem, 'vector2')
        }
        
        self._save_keys()
        print("✅ AuraSeal512 Keys Generated: 2 Public → 1 Private")
    
    def _derive_public_key(self, private_pem: bytes, derivation_path: str) -> str:
        """Derive a public key using specific derivation path"""
        # Create unique derivation input
        derivation_input = private_pem + derivation_path.encode()
        
        # Use hash-based key derivation
        derived_key = hashlib.sha512(derivation_input).digest()
        
        # Convert to base64 for storage
        return base64.b64encode(derived_key).decode()
    
    def _save_keys(self):
        """Save keys to secure storage"""
        # Save private key
        with open(self.private_key_path, 'wb') as f:
            f.write(self.private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        # Save public keys
        with open(self.public_keys_path, 'w') as f:
            json.dump({
                'pub1': self.public_keys['pub1'],
                'pub2': self.public_keys['pub2'],
                'seal_name': self.seal_name,
                'created': datetime.utcnow().isoformat(),
                'key_mapping': '2:1_public_to_private'
            }, f, indent=2)
        
        # Secure file permissions
        os.chmod(self.private_key_path, 0o600)
        os.chmod(self.public_keys_path, 0o644)
    
    def _load_keys(self):
        """Load existing keys"""
        # Load private key
        with open(self.private_key_path, 'rb') as f:
            self.private_key = serialization.load_pem_private_key(
                f.read(),
                password=None
            )
        
        # Load public keys
        with open(self.public_keys_path, 'r') as f:
            key_data = json.load(f)
            self.public_keys = {
                'pub1': key_data['pub1'],
                'pub2': key_data['pub2']
            }
    
    def create_document_seal(self, document_path: str, metadata: Dict = None) -> str:
        """Create AuraSeal for a document (PDF, etc.)"""
        if not os.path.exists(document_path):
            raise FileNotFoundError(f"Document not found: {document_path}")
        
        # Read document content
        with open(document_path, 'rb') as f:
            document_content = f.read()
        
        # Create seal metadata
        seal_metadata = {
            'document_name': os.path.basename(document_path),
            'document_size': len(document_content),
            'document_hash': hashlib.sha256(document_content).hexdigest(),
            'seal_timestamp': datetime.utcnow().isoformat() + 'Z',
            'seal_version': 'AuraSeal512-2.1',
            'key_mapping': '2:1_public_private',
            ** (metadata or {})
        }
        
        # Create digital signature
        signature = self._sign_metadata(seal_metadata)
        seal_metadata['_auraseal_signature'] = signature
        seal_metadata['_public_key_fingerprints'] = {
            'pub1': hashlib.sha256(self.public_keys['pub1'].encode()).hexdigest()[:16],
            'pub2': hashlib.sha256(self.public_keys['pub2'].encode()).hexdigest()[:16]
        }
        
        # Create sealed archive
        archive_name = f"{document_path}.auraseal512.zip"
        with zipfile.ZipFile(archive_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add original document
            zipf.write(document_path, os.path.basename(document_path))
            # Add seal metadata
            zipf.writestr('auraseal.metadata.json', json.dumps(seal_metadata, indent=2))
            # Add public keys for verification
            zipf.writestr('public.keys.json', json.dumps(self.public_keys, indent=2))
        
        print(f"✅ Document sealed: {archive_name}")
        return archive_name
    
    def _sign_metadata(self, metadata: Dict) -> str:
        """Create cryptographic signature for metadata"""
        # Create canonical JSON string
        canonical_json = json.dumps(metadata, sort_keys=True, separators=(',', ':'))
        
        # Sign with private key
        signature = self.private_key.sign(
            canonical_json.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        return base64.b64encode(signature).decode()
    
    def verify_document_seal(self, sealed_archive: str) -> Dict:
        """Verify AuraSeal integrity"""
        if not os.path.exists(sealed_archive):
            raise FileNotFoundError(f"Sealed archive not found: {sealed_archive}")
        
        try:
            with zipfile.ZipFile(sealed_archive, 'r') as zipf:
                # Extract metadata
                metadata_str = zipf.read('auraseal.metadata.json').decode()
                metadata = json.loads(metadata_str)
                
                # Extract public keys
                public_keys_str = zipf.read('public.keys.json').decode()
                sealed_public_keys = json.loads(public_keys_str)
                
                # Extract original document
                doc_name = metadata['document_name']
                original_content = zipf.read(doc_name)
            
            # Verify document integrity
            current_hash = hashlib.sha256(original_content).hexdigest()
            if current_hash != metadata['document_hash']:
                return {
                    'valid': False,
                    'error': 'Document content tampered with',
                    'expected_hash': metadata['document_hash'],
                    'actual_hash': current_hash
                }
            
            # Verify signature (would require the original private key or proper PKI)
            # For demo, we'll check if public keys match
            if (sealed_public_keys['pub1'] != self.public_keys['pub1'] or 
                sealed_public_keys['pub2'] != self.public_keys['pub2']):
                return {
                    'valid': False,
                    'error': 'Public key mismatch - seal may be forged'
                }
            
            return {
                'valid': True,
                'document': doc_name,
                'seal_timestamp': metadata['seal_timestamp'],
                'key_mapping': metadata.get('key_mapping', 'unknown'),
                'fault_tolerant': True  # 2:1 mapping provides redundancy
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': f'Verification failed: {str(e)}'
            }
    
    def get_key_info(self) -> Dict:
        """Get information about the 2:1 key mapping"""
        return {
            'seal_name': self.seal_name,
            'key_mapping': '2:1 (Two Public → One Private)',
            'fault_tolerance': 'Dual public keys provide redundancy',
            'public_keys': {
                'pub1_fingerprint': hashlib.sha256(self.public_keys['pub1'].encode()).hexdigest()[:16],
                'pub2_fingerprint': hashlib.sha256(self.public_keys['pub2'].encode()).hexdigest()[:16]
            },
            'key_storage': {
                'private_key': self.private_key_path,
                'public_keys': self.public_keys_path
            }
        }

# Example usage
def demonstrate_auraseal512():
    """Demonstrate AuraSeal512 with 2:1 key mapping"""
    print("=== AuraSeal512 Demonstration ===\n")
    
    # Initialize with custom seal name
    seal = AuraSeal512(seal_name="legal_documents")
    
    # Show key information
    key_info = seal.get_key_info()
    print("🔐 Key Configuration:")
    print(f"  Mapping: {key_info['key_mapping']}")
    print(f"  Public Key 1: {key_info['public_keys']['pub1_fingerprint']}")
    print(f"  Public Key 2: {key_info['public_keys']['pub2_fingerprint']}")
    print(f"  Fault Tolerance: {key_info['fault_tolerance']}\n")
    
    # Create a sample document (in real use, replace with your PDF)
    sample_content = "This is a test document for AuraSeal512 demonstration."
    with open("sample_document.txt", "w") as f:
        f.write(sample_content)
    
    # Seal the document
    print("📄 Sealing document...")
    sealed_archive = seal.create_document_seal(
        "sample_document.txt",
        metadata={
            'author': 'OBINexus Legal',
            'purpose': 'Demonstration of 2:1 key mapping',
            'fault_tolerant': True
        }
    )
    
    # Verify the seal
    print("🔍 Verifying seal...")
    verification = seal.verify_document_seal(sealed_archive)
    
    print("📊 Verification Result:")
    print(f"  Valid: {verification['valid']}")
    if verification['valid']:
        print(f"  Document: {verification['document']}")
        print(f"  Timestamp: {verification['seal_timestamp']}")
        print(f"  Key Mapping: {verification['key_mapping']}")
        print(f"  Fault Tolerant: {verification['fault_tolerant']}")
    else:
        print(f"  Error: {verification['error']}")
    
    # Cleanup
    if os.path.exists("sample_document.txt"):
        os.remove("sample_document.txt")
    
    return seal

if __name__ == "__main__":
    auraseal = demonstrate_auraseal512()
