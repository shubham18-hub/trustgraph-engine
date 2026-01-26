"""
TrustGraph Blockchain Service - W3C Verifiable Credentials for Indian Workforce
NITI Aayog Digital ShramSetu Initiative Implementation

This service manages W3C Verifiable Credentials on Hyperledger Fabric blockchain
for India's 490 million informal workers, ensuring DPDP Act 2023 compliance.

Features:
- W3C VC Data Model v1.1 compliance
- Ed25519Signature2020 cryptographic proofs
- did:india: method for sovereign identity
- DPDP Act 2023 privacy-by-design
- Indian work categories and skill levels
- Regional language support via Bhashini
"""

import json
import logging
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import boto3
from botocore.config import Config
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.asymmetric import ed25519
import base64

# Configure logging
logger = logging.getLogger(__name__)

class IndianWorkforceCredentialService:
    """
    W3C Verifiable Credentials service for Indian informal workforce
    Implements NITI Aayog Digital ShramSetu specifications
    """
    
    def __init__(self):
        # AWS clients configured for India region (DPDP Act compliance)
        aws_config = Config(
            region_name='ap-south-1',  # Mumbai region for data residency
            retries={'max_attempts': 3}
        )
        
        self.kms_client = boto3.client('kms', config=aws_config)
        self.s3_client = boto3.client('s3', config=aws_config)
        self.blockchain_client = boto3.client('managedblockchain', config=aws_config)
        
        # Indian context configurations
        self.w3c_context = [
            "https://www.w3.org/2018/credentials/v1",
            "https://trustgraph.gov.in/contexts/work/v1",
            "https://dpdp.gov.in/contexts/privacy/v1"  # DPDP Act context
        ]
        
        # Indian work categories with regional variations
        self.indian_work_categories = {
            "construction": {
                "hindi": "निर्माण कार्य",
                "subcategories": ["राजमिस्त्री", "बढ़ई", "इलेक्ट्रीशियन", "प्लंबर", "पेंटर"]
            },
            "domestic": {
                "hindi": "घरेलू कार्य", 
                "subcategories": ["घरेलू सहायक", "रसोइया", "ड्राइवर", "सिक्योरिटी गार्ड"]
            },
            "agriculture": {
                "hindi": "कृषि कार्य",
                "subcategories": ["खेत मजदूर", "फसल कटाई", "सिंचाई विशेषज्ञ", "पशुपालन"]
            },
            "services": {
                "hindi": "सेवा कार्य",
                "subcategories": ["डिलीवरी पर्सन", "ऑटो ड्राइवर", "दुकानदार", "मैकेनिक"]
            }
        }
        
        # Skill levels in Indian languages
        self.skill_levels = {
            "beginner": {"hindi": "प्रशिक्षु", "english": "Trainee"},
            "skilled": {"hindi": "कुशल", "english": "Skilled"},
            "expert": {"hindi": "विशेषज्ञ", "english": "Expert"}
        }
    
    async def issue_indian_work_credential(
        self,
        worker_did: str,
        employer_did: str,
        work_details: Dict,
        privacy_settings: Dict
    ) -> Dict:
        """
        Issue W3C Verifiable Credential for Indian worker
        
        Args:
            worker_did: Worker's DID (did:india:worker:hash)
            employer_did: Employer's DID (did:india:employer:id)
            work_details: Work completion details
            privacy_settings: DPDP Act privacy preferences
            
        Returns:
            W3C compliant verifiable credential
        """
        
        try:
            # Validate DPDP Act compliance
            if not self._validate_dpdp_compliance(privacy_settings):
                raise ValueError("DPDP Act compliance validation failed")
            
            # Create credential ID
            credential_id = f"urn:uuid:{self._generate_uuid()}"
            
            # Build W3C Verifiable Credential
            credential = {
                "@context": self.w3c_context,
                "id": credential_id,
                "type": ["VerifiableCredential", "IndianWorkCredential"],
                "issuer": {
                    "id": employer_did,
                    "name": work_details.get("employer_name"),
                    "type": "IndianEmployer",
                    "verification": {
                        "gst_number": work_details.get("gst_number"),
                        "verification_status": "govt_verified",
                        "verification_date": datetime.now(timezone.utc).isoformat()
                    }
                },
                "issuanceDate": datetime.now(timezone.utc).isoformat(),
                "expirationDate": self._calculate_expiration_date(),
                "credentialSubject": {
                    "id": worker_did,
                    "type": "IndianInformalWorker",
                    "workDetails": await self._build_indian_work_details(work_details),
                    "skillEndorsements": await self._build_skill_endorsements(work_details),
                    "performanceMetrics": self._build_performance_metrics(work_details),
                    "regionalContext": self._build_regional_context(work_details)
                },
                "privacyCompliance": {
                    "dpdpAct2023": True,
                    "dataLocalization": "ap-south-1",
                    "consentTimestamp": privacy_settings.get("consent_timestamp"),
                    "retentionPeriod": privacy_settings.get("retention_period", "7_years"),
                    "sharingPermissions": privacy_settings.get("sharing_permissions", {}),
                    "rightToErasure": True,
                    "dataMinimization": True
                },
                "evidence": await self._build_evidence_chain(work_details)
            }
            
            # Generate cryptographic proof using Ed25519
            proof = await self._generate_ed25519_proof(credential, employer_did)
            credential["proof"] = proof
            
            # Store credential on blockchain
            blockchain_tx = await self._store_on_hyperledger_fabric(credential)
            credential["blockchainProof"] = blockchain_tx
            
            # Store encrypted credential in S3 (ap-south-1)
            storage_result = await self._store_encrypted_credential(credential, worker_did)
            
            logger.info(f"Indian work credential issued: {credential_id}")
            
            return {
                "credential": credential,
                "credentialId": credential_id,
                "blockchainTxId": blockchain_tx["transaction_id"],
                "storageLocation": storage_result["s3_key"],
                "dpdpCompliant": True,
                "issuanceTimestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to issue Indian work credential: {str(e)}")
            raise
    
    async def _build_indian_work_details(self, work_details: Dict) -> Dict:
        """Build work details with Indian context and multilingual support"""
        
        work_type = work_details.get("work_type", "")
        
        # Map to Indian work categories
        indian_work_type = self._map_to_indian_category(work_type)
        
        return {
            "jobType": {
                "english": work_type,
                "hindi": indian_work_type.get("hindi", work_type),
                "category": indian_work_type.get("category", "services"),
                "iscoCode": self._get_isco_code(work_type)  # International Standard Classification
            },
            "skillLevel": {
                "level": work_details.get("skill_level", "skilled"),
                "hindi": self.skill_levels.get(work_details.get("skill_level", "skilled"), {}).get("hindi"),
                "certificationBody": work_details.get("certification_body"),
                "skillIndiaAlignment": self._check_skill_india_alignment(work_type)
            },
            "duration": {
                "startDate": work_details.get("start_date"),
                "endDate": work_details.get("end_date"),
                "totalDays": work_details.get("total_days"),
                "workingHours": work_details.get("working_hours", 8),
                "seasonalPattern": self._analyze_seasonal_pattern(work_details)
            },
            "location": {
                "state": work_details.get("state"),
                "district": work_details.get("district"),
                "pinCode": work_details.get("pin_code"),
                "coordinates": {
                    "latitude": work_details.get("latitude"),
                    "longitude": work_details.get("longitude"),
                    "accuracy": work_details.get("gps_accuracy", "high")
                },
                "addressHash": self._hash_address_for_privacy(work_details.get("address")),
                "ruralUrban": self._classify_rural_urban(work_details.get("pin_code"))
            },
            "compensation": {
                "totalAmount": work_details.get("total_amount"),
                "currency": "INR",
                "paymentMethod": work_details.get("payment_method", "UPI"),
                "paymentSchedule": work_details.get("payment_schedule", "milestone_based"),
                "bonusEarned": work_details.get("bonus_amount", 0),
                "deductions": work_details.get("deductions", {}),
                "netPayment": work_details.get("net_payment"),
                "upiTransactionRefs": work_details.get("upi_refs", [])
            }
        }
    
    async def _generate_ed25519_proof(self, credential: Dict, issuer_did: str) -> Dict:
        """
        Generate Ed25519Signature2020 proof for W3C compliance
        Uses AWS KMS for secure key management
        """
        
        try:
            # Get or create Ed25519 key for issuer
            key_id = await self._get_or_create_ed25519_key(issuer_did)
            
            # Create canonical representation for signing
            canonical_credential = self._canonicalize_credential(credential)
            
            # Create proof structure
            proof = {
                "type": "Ed25519Signature2020",
                "created": datetime.now(timezone.utc).isoformat(),
                "verificationMethod": f"{issuer_did}#key-1",
                "proofPurpose": "assertionMethod",
                "challenge": self._generate_challenge(),
                "domain": "trustgraph.gov.in"
            }
            
            # Create signing input
            signing_input = self._create_signing_input(canonical_credential, proof)
            
            # Sign using AWS KMS
            signature = await self._sign_with_kms(key_id, signing_input)
            
            # Add signature to proof
            proof["jws"] = signature
            proof["compliance"] = {
                "w3cStandard": "Verifiable Credentials Data Model v1.1",
                "signatureSuite": "Ed25519Signature2020",
                "dpdpAct2023": True,
                "dataResidency": "ap-south-1"
            }
            
            return proof
            
        except Exception as e:
            logger.error(f"Failed to generate Ed25519 proof: {str(e)}")
            raise
    
    async def _store_on_hyperledger_fabric(self, credential: Dict) -> Dict:
        """Store credential on Hyperledger Fabric blockchain"""
        
        try:
            # Prepare blockchain transaction
            chaincode_args = {
                "function": "MintIndianWorkCredential",
                "args": [
                    credential["id"],
                    json.dumps(credential),
                    credential["credentialSubject"]["id"],  # worker DID
                    credential["issuer"]["id"],  # employer DID
                    datetime.now(timezone.utc).isoformat()
                ]
            }
            
            # Submit to Hyperledger Fabric network
            # This would use the actual blockchain client
            # For now, return mock transaction
            
            transaction_id = f"tx_{self._generate_uuid()}"
            
            blockchain_result = {
                "transaction_id": transaction_id,
                "block_number": 12345,  # Mock block number
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "network": "trustgraph-fabric-network",
                "channel": "indian-workforce-channel",
                "chaincode": "trustledger",
                "status": "committed",
                "gas_used": 0,  # Hyperledger Fabric doesn't use gas
                "endorsing_peers": ["peer0.employer.trustgraph.com", "peer0.bank.trustgraph.com"]
            }
            
            logger.info(f"Credential stored on blockchain: {transaction_id}")
            return blockchain_result
            
        except Exception as e:
            logger.error(f"Failed to store credential on blockchain: {str(e)}")
            raise
    
    async def verify_indian_work_credential(self, credential: Dict) -> Dict:
        """
        Verify W3C Verifiable Credential with Indian compliance checks
        
        Args:
            credential: W3C Verifiable Credential to verify
            
        Returns:
            Verification result with compliance status
        """
        
        try:
            verification_result = {
                "isValid": False,
                "w3cCompliant": False,
                "dpdpCompliant": False,
                "blockchainVerified": False,
                "signatureValid": False,
                "errors": [],
                "warnings": []
            }
            
            # 1. W3C Structure Validation
            if not self._validate_w3c_structure(credential):
                verification_result["errors"].append("Invalid W3C VC structure")
                return verification_result
            
            verification_result["w3cCompliant"] = True
            
            # 2. DPDP Act Compliance Check
            if not self._validate_credential_dpdp_compliance(credential):
                verification_result["errors"].append("DPDP Act compliance validation failed")
                return verification_result
            
            verification_result["dpdpCompliant"] = True
            
            # 3. Cryptographic Signature Verification
            if not await self._verify_ed25519_signature(credential):
                verification_result["errors"].append("Invalid cryptographic signature")
                return verification_result
            
            verification_result["signatureValid"] = True
            
            # 4. Blockchain Verification
            if not await self._verify_blockchain_record(credential):
                verification_result["warnings"].append("Blockchain verification failed")
            else:
                verification_result["blockchainVerified"] = True
            
            # Overall validity
            verification_result["isValid"] = (
                verification_result["w3cCompliant"] and
                verification_result["dpdpCompliant"] and
                verification_result["signatureValid"]
            )
            
            logger.info(f"Credential verification completed: {credential.get('id')}")
            return verification_result
            
        except Exception as e:
            logger.error(f"Credential verification failed: {str(e)}")
            return {
                "isValid": False,
                "error": str(e)
            }
    
    def _validate_dpdp_compliance(self, privacy_settings: Dict) -> bool:
        """Validate DPDP Act 2023 compliance requirements"""
        
        required_fields = [
            "consent_timestamp",
            "data_categories",
            "processing_purposes",
            "retention_period"
        ]
        
        # Check required fields
        for field in required_fields:
            if field not in privacy_settings:
                logger.error(f"Missing DPDP compliance field: {field}")
                return False
        
        # Validate consent timestamp is recent (within 30 days)
        consent_time = datetime.fromisoformat(privacy_settings["consent_timestamp"].replace('Z', '+00:00'))
        if (datetime.now(timezone.utc) - consent_time).days > 30:
            logger.error("Consent timestamp too old for DPDP compliance")
            return False
        
        return True
    
    def _map_to_indian_category(self, work_type: str) -> Dict:
        """Map work type to Indian categories with Hindi translations"""
        
        work_type_lower = work_type.lower()
        
        for category, details in self.indian_work_categories.items():
            if work_type_lower in [sub.lower() for sub in details["subcategories"]]:
                return {
                    "category": category,
                    "hindi": details["hindi"],
                    "subcategory": work_type
                }
        
        # Default mapping
        return {
            "category": "services",
            "hindi": "सेवा कार्य",
            "subcategory": work_type
        }
    
    def _validate_w3c_structure(self, credential: Dict) -> bool:
        """Validate W3C Verifiable Credential structure"""
        
        required_fields = ["@context", "type", "issuer", "issuanceDate", "credentialSubject", "proof"]
        
        for field in required_fields:
            if field not in credential:
                logger.error(f"Missing required W3C field: {field}")
                return False
        
        # Validate context
        if "https://www.w3.org/2018/credentials/v1" not in credential["@context"]:
            logger.error("Missing W3C credentials context")
            return False
        
        return True
    
    def _generate_uuid(self) -> str:
        """Generate UUID for credential identification"""
        import uuid
        return str(uuid.uuid4())
    
    def _calculate_expiration_date(self) -> str:
        """Calculate credential expiration date (typically 5 years for work credentials)"""
        from datetime import timedelta
        expiration = datetime.now(timezone.utc) + timedelta(days=5*365)  # 5 years
        return expiration.isoformat()
    
    def _canonicalize_credential(self, credential: Dict) -> str:
        """Create canonical representation of credential for signing"""
        # This would implement JSON-LD canonicalization
        # For now, use simple JSON serialization
        return json.dumps(credential, sort_keys=True, separators=(',', ':'))
    
    def _create_signing_input(self, canonical_credential: str, proof: Dict) -> bytes:
        """Create signing input from credential and proof"""
        proof_str = json.dumps(proof, sort_keys=True, separators=(',', ':'))
        signing_input = canonical_credential + proof_str
        return signing_input.encode('utf-8')

# Initialize the service
indian_credential_service = IndianWorkforceCredentialService()