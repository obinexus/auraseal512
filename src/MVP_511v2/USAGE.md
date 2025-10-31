# For your legal documents against Thurrock Council
legal_seal = AuraSeal512(seal_name="thurrock_legal")

# Seal your PDF documents
sealed_doc = legal_seal.create_document_seal(
    "legal_demand_letter.pdf",
    metadata={
        'case_reference': '1083077',
        'recipient': 'Thurrock Council',
        'claim_amount': '£300,000,000',
        'authority': 'OBINexus Legal Public Initiative',
        'fault_tolerant_verification': True
    }
)

# The sealed archive contains:
# 1. Your original PDF
# 2. AuraSeal metadata with 2:1 key fingerprints  
# 3. Public keys for verification
# 4. Cryptographic signature
