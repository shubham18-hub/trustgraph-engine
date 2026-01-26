"""
Agentic Execution Handler for TrustGraph Engine
Handles milestone verification, geotagged photo validation, and automatic UPI payment disbursal
Integrates with Amazon Managed Blockchain and UPI payment gateways
"""

import json
import boto3
import base64
import asyncio
import aiohttp
import logging
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime, timedelta
import uuid
import os
from dataclasses import dataclass, asdict
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import io
import hashlib
import hmac
from decimal import Decimal
import math

from src.utils.logger import get_logger, set_correlation_id, log_business_event
from src.utils.response import create_response, create_error_response
from src.services.blockchain_service import BlockchainService
from src.services.upi_service import UPIService

logger = get_logger(__name__)

@dataclass
class GeoLocation:
    """Represents geographical coordinates"""
    latitude: float
    longitude: float
    accuracy: Optional[float] = None
    timestamp: Optional[str] = None
    
    def distance_to(self, other: 'GeoLocation') -> float:
        """Calculate distance in meters using Haversine formula"""
        R = 6371000  # Earth's radius in meters
        
        lat1_rad = math.radians(self.latitude)
        lat2_rad = math.radians(other.latitude)
        delta_lat = math.radians(other.latitude - self.latitude)
        delta_lon = math.radians(other.longitude - self.longitude)
        
        a = (math.sin(delta_lat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * 
             math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c

@dataclass
class PhotoEvidence:
    """Represents uploaded photo evidence"""
    photo_id: str
    s3_url: str
    hash: str
    location: Optional[GeoLocation]
    timestamp: str
    metadata: Dict[str, Any]
    worker_id: str
    milestone_id: str

@dataclass
class SmartContractMilestone:
    """Represents a smart contract milestone"""
    milestone_id: str
    project_id: str
    worker_id: str
    employer_id: str
    description: str
    payment_amount: int
    currency: str
    expected_location: GeoLocation
    location_tolerance: float  # meters
    deadline: str
    status: str
    verification_criteria: Dict[str, Any]
    created_at: str

@dataclass
class PaymentDisbursal:
    """Represents a UPI payment disbursal"""
    payment_id: str
    milestone_id: str
    worker_id: str
    employer_id: str
    amount: int
    currency: str
    upi_id: str
    transaction_ref: str
    status: str
    initiated_at: str
    completed_at: Optional[str] = None
    failure_reason: Optional[str] = None

class AgenticExecutionService:
    """Service for handling agentic milestone execution and payment automation"""
    
    def __init__(self):
        self.s3_client = boto3.client('s3', region_name='ap-south-1')
        self.dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
        self.rekognition = boto3.client('rekognition', region_name='ap-south-1')
        self.eventbridge = boto3.client('events', region_name='ap-south-1')
        
        # DynamoDB tables
        self.milestones_table = self.dynamodb.Table(os.environ.get('MILESTONES_TABLE', 'trustgraph-milestones'))
        self.payments_table = self.dynamodb.Table(os.environ.get('PAYMENTS_TABLE', 'trustgraph-payments'))
        self.evidence_table = self.dynamodb.Table(os.environ.get('EVIDENCE_TABLE', 'trustgraph-evidence'))
        
        # S3 bucket for evidence storage
        self.evidence_bucket = os.environ.get('EVIDENCE_BUCKET', 'trustgraph-evidence')
        
        # Services
        self.blockchain_service = BlockchainService()
        self.upi_service = UPIService()
        
        # Configuration
        self.max_photo_size = 10 * 1024 * 1024  # 10MB
        self.supported_formats = ['JPEG', 'JPG', 'PNG']
        self.location_tolerance_default = 100.0  # 100 meters default
        
    async def process_milestone_evidence(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process uploaded milestone evidence and trigger payment if verified
        
        Args:
            event_data: Event containing photo upload and milestone information
            
        Returns:
            Processing result with verification status and payment details
        """
        try:
            # Extract event parameters
            worker_id = event_data.get('worker_id')
            milestone_id = event_data.get('milestone_id')
            photo_data = event_data.get('photo_data')  # Base64 encoded
            photo_metadata = event_data.get('photo_metadata', {})
            
            if not all([worker_id, milestone_id, photo_data]):
                raise ValueError("Missing required parameters: worker_id, milestone_id, photo_data")
            
            logger.info(f"Processing milestone evidence for worker {worker_id}, milestone {milestone_id}")
            
            # Step 1: Retrieve milestone details
            milestone = await self.get_milestone(milestone_id)
            if not milestone:
                raise ValueError(f"Milestone {milestone_id} not found")
            
            if milestone.worker_id != worker_id:
                raise ValueError(f"Worker {worker_id} not authorized for milestone {milestone_id}")
            
            if milestone.status != 'active':
                raise ValueError(f"Milestone {milestone_id} is not active (status: {milestone.status})")
            
            # Step 2: Process and validate photo evidence
            photo_evidence = await self.process_photo_evidence(
                photo_data, worker_id, milestone_id, photo_metadata
            )
            
            # Step 3: Verify location against milestone requirements
            location_verified = await self.verify_location(photo_evidence.location, milestone)
            
            # Step 4: Perform additional verification checks
            verification_result = await self.perform_verification_checks(
                photo_evidence, milestone
            )
            
            # Step 5: If all verifications pass, trigger payment
            payment_result = None
            if location_verified and verification_result['verified']:
                payment_result = await self.trigger_automatic_payment(milestone, photo_evidence)
                
                # Update milestone status
                await self.update_milestone_status(milestone_id, 'completed', {
                    'verification_timestamp': datetime.utcnow().isoformat(),
                    'evidence_id': photo_evidence.photo_id,
                    'payment_id': payment_result.get('payment_id') if payment_result else None
                })
                
                # Mint W3C Verifiable Credential on blockchain
                credential_result = await self.mint_verifiable_credential(milestone, photo_evidence)
                
                # Log business event
                log_business_event(logger, 'milestone_completed', {
                    'worker_id': worker_id,
                    'milestone_id': milestone_id,
                    'payment_amount': milestone.payment_amount,
                    'verification_method': 'geotagged_photo',
                    'location_verified': location_verified
                })
            
            return {
                'milestone_id': milestone_id,
                'worker_id': worker_id,
                'verification_status': 'verified' if (location_verified and verification_result['verified']) else 'failed',
                'location_verified': location_verified,
                'verification_details': verification_result,
                'photo_evidence': asdict(photo_evidence),
                'payment_result': payment_result,
                'credential_minted': credential_result is not None if payment_result else False,
                'processing_timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing milestone evidence: {str(e)}")
            raise
    
    async def process_photo_evidence(self, photo_data: str, worker_id: str, 
                                   milestone_id: str, metadata: Dict[str, Any]) -> PhotoEvidence:
        """
        Process uploaded photo evidence and extract metadata
        
        Args:
            photo_data: Base64 encoded photo data
            worker_id: Worker identifier
            milestone_id: Milestone identifier
            metadata: Additional metadata
            
        Returns:
            PhotoEvidence object with extracted information
        """
        try:
            # Decode photo data
            photo_bytes = base64.b64decode(photo_data)
            
            # Validate photo size
            if len(photo_bytes) > self.max_photo_size:
                raise ValueError(f"Photo size exceeds maximum limit of {self.max_photo_size} bytes")
            
            # Validate photo format
            try:
                image = Image.open(io.BytesIO(photo_bytes))
                if image.format not in self.supported_formats:
                    raise ValueError(f"Unsupported photo format: {image.format}")
            except Exception as e:
                raise ValueError(f"Invalid photo format: {str(e)}")
            
            # Generate photo ID and hash
            photo_id = f"evidence_{worker_id}_{milestone_id}_{int(datetime.utcnow().timestamp())}"
            photo_hash = hashlib.sha256(photo_bytes).hexdigest()
            
            # Extract EXIF data including GPS coordinates
            exif_data = self.extract_exif_data(image)
            location = self.extract_gps_location(exif_data)
            
            # Upload to S3
            s3_key = f"evidence/{worker_id}/{milestone_id}/{photo_id}.jpg"
            s3_url = await self.upload_to_s3(photo_bytes, s3_key, {
                'worker_id': worker_id,
                'milestone_id': milestone_id,
                'photo_hash': photo_hash,
                'upload_timestamp': datetime.utcnow().isoformat()
            })
            
            # Store evidence metadata in DynamoDB
            evidence_record = {
                'photo_id': photo_id,
                'worker_id': worker_id,
                'milestone_id': milestone_id,
                's3_url': s3_url,
                'photo_hash': photo_hash,
                'location': asdict(location) if location else None,
                'exif_data': exif_data,
                'metadata': metadata,
                'created_at': datetime.utcnow().isoformat(),
                'status': 'uploaded'
            }
            
            self.evidence_table.put_item(Item=evidence_record)
            
            return PhotoEvidence(
                photo_id=photo_id,
                s3_url=s3_url,
                hash=photo_hash,
                location=location,
                timestamp=datetime.utcnow().isoformat(),
                metadata={**exif_data, **metadata},
                worker_id=worker_id,
                milestone_id=milestone_id
            )
            
        except Exception as e:
            logger.error(f"Error processing photo evidence: {str(e)}")
            raise
    
    def extract_exif_data(self, image: Image.Image) -> Dict[str, Any]:
        """Extract EXIF metadata from image"""
        exif_data = {}
        
        try:
            exif = image._getexif()
            if exif:
                for tag_id, value in exif.items():
                    tag = TAGS.get(tag_id, tag_id)
                    exif_data[tag] = value
        except Exception as e:
            logger.warning(f"Failed to extract EXIF data: {str(e)}")
        
        return exif_data
    
    def extract_gps_location(self, exif_data: Dict[str, Any]) -> Optional[GeoLocation]:
        """Extract GPS coordinates from EXIF data"""
        try:
            gps_info = exif_data.get('GPSInfo')
            if not gps_info:
                return None
            
            def convert_to_degrees(value):
                """Convert GPS coordinates to decimal degrees"""
                d, m, s = value
                return d + (m / 60.0) + (s / 3600.0)
            
            # Extract latitude
            lat = gps_info.get(2)  # GPSLatitude
            lat_ref = gps_info.get(1)  # GPSLatitudeRef
            
            # Extract longitude
            lon = gps_info.get(4)  # GPSLongitude
            lon_ref = gps_info.get(3)  # GPSLongitudeRef
            
            if lat and lon and lat_ref and lon_ref:
                latitude = convert_to_degrees(lat)
                if lat_ref != 'N':
                    latitude = -latitude
                
                longitude = convert_to_degrees(lon)
                if lon_ref != 'E':
                    longitude = -longitude
                
                # Extract timestamp if available
                gps_timestamp = None
                gps_date = gps_info.get(29)  # GPSDateStamp
                gps_time = gps_info.get(7)   # GPSTimeStamp
                
                if gps_date and gps_time:
                    try:
                        date_str = gps_date.replace(':', '-')
                        time_str = f"{int(gps_time[0]):02d}:{int(gps_time[1]):02d}:{int(gps_time[2]):02d}"
                        gps_timestamp = f"{date_str}T{time_str}Z"
                    except:
                        pass
                
                return GeoLocation(
                    latitude=latitude,
                    longitude=longitude,
                    timestamp=gps_timestamp
                )
        
        except Exception as e:
            logger.warning(f"Failed to extract GPS location: {str(e)}")
        
        return None
    
    async def upload_to_s3(self, data: bytes, key: str, metadata: Dict[str, str]) -> str:
        """Upload data to S3 and return URL"""
        try:
            self.s3_client.put_object(
                Bucket=self.evidence_bucket,
                Key=key,
                Body=data,
                Metadata=metadata,
                ServerSideEncryption='AES256',
                ContentType='image/jpeg'
            )
            
            return f"s3://{self.evidence_bucket}/{key}"
            
        except Exception as e:
            logger.error(f"Failed to upload to S3: {str(e)}")
            raise
    
    async def get_milestone(self, milestone_id: str) -> Optional[SmartContractMilestone]:
        """Retrieve milestone details from DynamoDB"""
        try:
            response = self.milestones_table.get_item(Key={'milestone_id': milestone_id})
            
            if 'Item' not in response:
                return None
            
            item = response['Item']
            
            # Parse expected location
            expected_location = None
            if 'expected_location' in item:
                loc_data = item['expected_location']
                expected_location = GeoLocation(
                    latitude=float(loc_data['latitude']),
                    longitude=float(loc_data['longitude'])
                )
            
            return SmartContractMilestone(
                milestone_id=item['milestone_id'],
                project_id=item['project_id'],
                worker_id=item['worker_id'],
                employer_id=item['employer_id'],
                description=item['description'],
                payment_amount=int(item['payment_amount']),
                currency=item.get('currency', 'INR'),
                expected_location=expected_location,
                location_tolerance=float(item.get('location_tolerance', self.location_tolerance_default)),
                deadline=item['deadline'],
                status=item['status'],
                verification_criteria=item.get('verification_criteria', {}),
                created_at=item['created_at']
            )
            
        except Exception as e:
            logger.error(f"Error retrieving milestone {milestone_id}: {str(e)}")
            return None
    
    async def verify_location(self, photo_location: Optional[GeoLocation], 
                            milestone: SmartContractMilestone) -> bool:
        """Verify if photo location matches milestone requirements"""
        if not photo_location or not milestone.expected_location:
            logger.warning("Missing location data for verification")
            return False
        
        try:
            distance = photo_location.distance_to(milestone.expected_location)
            tolerance = milestone.location_tolerance
            
            logger.info(f"Location verification: distance={distance:.2f}m, tolerance={tolerance}m")
            
            is_within_tolerance = distance <= tolerance
            
            # Log location verification event
            log_business_event(logger, 'location_verification', {
                'milestone_id': milestone.milestone_id,
                'worker_id': milestone.worker_id,
                'distance_meters': distance,
                'tolerance_meters': tolerance,
                'verified': is_within_tolerance,
                'photo_location': asdict(photo_location),
                'expected_location': asdict(milestone.expected_location)
            })
            
            return is_within_tolerance
            
        except Exception as e:
            logger.error(f"Error verifying location: {str(e)}")
            return False
    
    async def perform_verification_checks(self, photo_evidence: PhotoEvidence, 
                                        milestone: SmartContractMilestone) -> Dict[str, Any]:
        """Perform additional verification checks on the evidence"""
        verification_result = {
            'verified': True,
            'checks': {},
            'confidence_score': 1.0,
            'issues': []
        }
        
        try:
            # Check 1: Photo authenticity (basic checks)
            authenticity_check = await self.verify_photo_authenticity(photo_evidence)
            verification_result['checks']['authenticity'] = authenticity_check
            
            if not authenticity_check['passed']:
                verification_result['verified'] = False
                verification_result['issues'].extend(authenticity_check['issues'])
            
            # Check 2: Timestamp verification
            timestamp_check = await self.verify_timestamp(photo_evidence, milestone)
            verification_result['checks']['timestamp'] = timestamp_check
            
            if not timestamp_check['passed']:
                verification_result['verified'] = False
                verification_result['issues'].extend(timestamp_check['issues'])
            
            # Check 3: Content analysis (if enabled)
            if milestone.verification_criteria.get('content_analysis', False):
                content_check = await self.analyze_photo_content(photo_evidence, milestone)
                verification_result['checks']['content'] = content_check
                
                if not content_check['passed']:
                    verification_result['verified'] = False
                    verification_result['issues'].extend(content_check['issues'])
            
            # Calculate overall confidence score
            passed_checks = sum(1 for check in verification_result['checks'].values() if check['passed'])
            total_checks = len(verification_result['checks'])
            verification_result['confidence_score'] = passed_checks / total_checks if total_checks > 0 else 0.0
            
            return verification_result
            
        except Exception as e:
            logger.error(f"Error performing verification checks: {str(e)}")
            return {
                'verified': False,
                'checks': {},
                'confidence_score': 0.0,
                'issues': [f"Verification error: {str(e)}"]
            }
    
    async def verify_photo_authenticity(self, photo_evidence: PhotoEvidence) -> Dict[str, Any]:
        """Verify photo authenticity using basic checks"""
        try:
            # Check for required EXIF data
            has_exif = bool(photo_evidence.metadata)
            has_timestamp = 'DateTime' in photo_evidence.metadata
            has_camera_info = any(key in photo_evidence.metadata for key in ['Make', 'Model', 'Software'])
            
            # Check for GPS data
            has_gps = photo_evidence.location is not None
            
            issues = []
            if not has_exif:
                issues.append("Missing EXIF metadata")
            if not has_timestamp:
                issues.append("Missing timestamp in EXIF")
            if not has_gps:
                issues.append("Missing GPS coordinates")
            
            passed = len(issues) == 0
            
            return {
                'passed': passed,
                'confidence': 0.8 if passed else 0.3,
                'issues': issues,
                'details': {
                    'has_exif': has_exif,
                    'has_timestamp': has_timestamp,
                    'has_camera_info': has_camera_info,
                    'has_gps': has_gps
                }
            }
            
        except Exception as e:
            return {
                'passed': False,
                'confidence': 0.0,
                'issues': [f"Authenticity check error: {str(e)}"],
                'details': {}
            }
    
    async def verify_timestamp(self, photo_evidence: PhotoEvidence, 
                             milestone: SmartContractMilestone) -> Dict[str, Any]:
        """Verify photo timestamp is within acceptable range"""
        try:
            current_time = datetime.utcnow()
            
            # Check if photo is too old (more than 24 hours)
            photo_time = datetime.fromisoformat(photo_evidence.timestamp.replace('Z', '+00:00'))
            time_diff = current_time - photo_time
            
            # Check if photo is from the future (more than 5 minutes ahead)
            future_diff = photo_time - current_time
            
            issues = []
            if time_diff.total_seconds() > 24 * 3600:  # 24 hours
                issues.append("Photo is too old (more than 24 hours)")
            
            if future_diff.total_seconds() > 300:  # 5 minutes
                issues.append("Photo timestamp is in the future")
            
            # Check against milestone deadline
            deadline = datetime.fromisoformat(milestone.deadline.replace('Z', '+00:00'))
            if photo_time > deadline:
                issues.append("Photo taken after milestone deadline")
            
            passed = len(issues) == 0
            
            return {
                'passed': passed,
                'confidence': 0.9 if passed else 0.1,
                'issues': issues,
                'details': {
                    'photo_timestamp': photo_evidence.timestamp,
                    'current_time': current_time.isoformat(),
                    'time_diff_hours': time_diff.total_seconds() / 3600,
                    'milestone_deadline': milestone.deadline
                }
            }
            
        except Exception as e:
            return {
                'passed': False,
                'confidence': 0.0,
                'issues': [f"Timestamp verification error: {str(e)}"],
                'details': {}
            }
    
    async def analyze_photo_content(self, photo_evidence: PhotoEvidence, 
                                  milestone: SmartContractMilestone) -> Dict[str, Any]:
        """Analyze photo content using AWS Rekognition"""
        try:
            # Get photo from S3
            s3_key = photo_evidence.s3_url.split('/')[-3:]  # Extract key from S3 URL
            s3_key = '/'.join(s3_key)
            
            # Use Rekognition to detect labels
            response = self.rekognition.detect_labels(
                Image={
                    'S3Object': {
                        'Bucket': self.evidence_bucket,
                        'Name': s3_key
                    }
                },
                MaxLabels=20,
                MinConfidence=70
            )
            
            labels = [label['Name'].lower() for label in response['Labels']]
            
            # Check for work-related content based on job type
            job_type = milestone.verification_criteria.get('expected_job_type', '').lower()
            work_related_keywords = {
                'construction': ['building', 'construction', 'concrete', 'brick', 'cement', 'scaffold'],
                'plumbing': ['pipe', 'plumbing', 'water', 'bathroom', 'sink', 'toilet'],
                'electrical': ['wire', 'electrical', 'cable', 'switch', 'outlet', 'panel'],
                'painting': ['paint', 'brush', 'wall', 'color', 'coating'],
                'masonry': ['brick', 'stone', 'mortar', 'wall', 'construction']
            }
            
            expected_keywords = work_related_keywords.get(job_type, [])
            found_keywords = [keyword for keyword in expected_keywords if keyword in labels]
            
            issues = []
            if job_type and not found_keywords:
                issues.append(f"No {job_type}-related content detected in photo")
            
            passed = len(issues) == 0
            
            return {
                'passed': passed,
                'confidence': 0.7 if passed else 0.4,
                'issues': issues,
                'details': {
                    'detected_labels': labels,
                    'expected_job_type': job_type,
                    'found_keywords': found_keywords,
                    'rekognition_response': response
                }
            }
            
        except Exception as e:
            logger.warning(f"Content analysis failed: {str(e)}")
            return {
                'passed': True,  # Don't fail verification if content analysis fails
                'confidence': 0.5,
                'issues': [f"Content analysis unavailable: {str(e)}"],
                'details': {}
            }
    
    async def trigger_automatic_payment(self, milestone: SmartContractMilestone, 
                                      photo_evidence: PhotoEvidence) -> Dict[str, Any]:
        """Trigger automatic UPI payment disbursal"""
        try:
            # Generate payment ID
            payment_id = f"pay_{milestone.milestone_id}_{int(datetime.utcnow().timestamp())}"
            
            # Get worker's UPI ID (this would typically come from user profile)
            worker_upi_id = await self.get_worker_upi_id(milestone.worker_id)
            if not worker_upi_id:
                raise ValueError(f"UPI ID not found for worker {milestone.worker_id}")
            
            # Create payment record
            payment_record = PaymentDisbursal(
                payment_id=payment_id,
                milestone_id=milestone.milestone_id,
                worker_id=milestone.worker_id,
                employer_id=milestone.employer_id,
                amount=milestone.payment_amount,
                currency=milestone.currency,
                upi_id=worker_upi_id,
                transaction_ref="",
                status="initiated",
                initiated_at=datetime.utcnow().isoformat()
            )
            
            # Store payment record
            self.payments_table.put_item(Item=asdict(payment_record))
            
            # Initiate UPI payment
            upi_result = await self.upi_service.initiate_payment({
                'payment_id': payment_id,
                'payee_upi_id': worker_upi_id,
                'amount': milestone.payment_amount,
                'currency': milestone.currency,
                'description': f"TrustGraph milestone payment - {milestone.description}",
                'reference_id': milestone.milestone_id
            })
            
            if upi_result['success']:
                # Update payment record with transaction reference
                payment_record.transaction_ref = upi_result['transaction_ref']
                payment_record.status = "processing"
                
                self.payments_table.update_item(
                    Key={'payment_id': payment_id},
                    UpdateExpression='SET transaction_ref = :ref, #status = :status',
                    ExpressionAttributeNames={'#status': 'status'},
                    ExpressionAttributeValues={
                        ':ref': upi_result['transaction_ref'],
                        ':status': 'processing'
                    }
                )
                
                # Log payment initiation
                log_business_event(logger, 'payment_initiated', {
                    'payment_id': payment_id,
                    'milestone_id': milestone.milestone_id,
                    'worker_id': milestone.worker_id,
                    'amount': milestone.payment_amount,
                    'upi_transaction_ref': upi_result['transaction_ref']
                })
                
                return {
                    'success': True,
                    'payment_id': payment_id,
                    'transaction_ref': upi_result['transaction_ref'],
                    'status': 'processing',
                    'amount': milestone.payment_amount,
                    'currency': milestone.currency
                }
            else:
                # Update payment record with failure
                payment_record.status = "failed"
                payment_record.failure_reason = upi_result.get('error', 'Unknown error')
                
                self.payments_table.update_item(
                    Key={'payment_id': payment_id},
                    UpdateExpression='SET #status = :status, failure_reason = :reason',
                    ExpressionAttributeNames={'#status': 'status'},
                    ExpressionAttributeValues={
                        ':status': 'failed',
                        ':reason': payment_record.failure_reason
                    }
                )
                
                return {
                    'success': False,
                    'payment_id': payment_id,
                    'error': upi_result.get('error', 'Payment initiation failed')
                }
                
        except Exception as e:
            logger.error(f"Error triggering automatic payment: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_worker_upi_id(self, worker_id: str) -> Optional[str]:
        """Get worker's UPI ID from profile (placeholder implementation)"""
        # TODO: Implement actual worker profile lookup
        # This would typically query a user profile service or database
        return f"{worker_id}@paytm"  # Placeholder
    
    async def update_milestone_status(self, milestone_id: str, status: str, 
                                    additional_data: Dict[str, Any]) -> None:
        """Update milestone status in DynamoDB"""
        try:
            update_expression = "SET #status = :status, updated_at = :updated_at"
            expression_values = {
                ':status': status,
                ':updated_at': datetime.utcnow().isoformat()
            }
            expression_names = {'#status': 'status'}
            
            # Add additional data to update
            for key, value in additional_data.items():
                placeholder = f":val_{key}"
                update_expression += f", {key} = {placeholder}"
                expression_values[placeholder] = value
            
            self.milestones_table.update_item(
                Key={'milestone_id': milestone_id},
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expression_names,
                ExpressionAttributeValues=expression_values
            )
            
        except Exception as e:
            logger.error(f"Error updating milestone status: {str(e)}")
            raise
    
    async def mint_verifiable_credential(self, milestone: SmartContractMilestone, 
                                       photo_evidence: PhotoEvidence) -> Optional[Dict[str, Any]]:
        """Mint W3C Verifiable Credential on blockchain"""
        try:
            # Prepare verification data for blockchain
            verification_data = {
                'workerId': milestone.worker_id,
                'employerId': milestone.employer_id,
                'projectId': milestone.project_id,
                'milestoneId': milestone.milestone_id,
                'workDetails': {
                    'jobType': milestone.verification_criteria.get('job_type', 'General Work'),
                    'skillLevel': milestone.verification_criteria.get('skill_level', 'Intermediate'),
                    'duration': milestone.verification_criteria.get('duration', '1 day'),
                    'location': {
                        'address': milestone.verification_criteria.get('location_address', ''),
                        'coordinates': [
                            milestone.expected_location.latitude,
                            milestone.expected_location.longitude
                        ] if milestone.expected_location else [0, 0],
                        'pinCode': milestone.verification_criteria.get('pin_code', '')
                    },
                    'compensation': {
                        'amount': milestone.payment_amount,
                        'currency': milestone.currency,
                        'paymentMethod': 'UPI',
                        'transactionId': ''  # Will be updated when payment completes
                    },
                    'performance': {
                        'rating': milestone.verification_criteria.get('expected_rating', 5.0),
                        'completionRate': 100,
                        'qualityScore': milestone.verification_criteria.get('quality_score', 90),
                        'punctualityScore': milestone.verification_criteria.get('punctuality_score', 95),
                        'bonusEarned': milestone.verification_criteria.get('bonus', 0)
                    },
                    'projectId': milestone.project_id,
                    'milestoneId': milestone.milestone_id,
                    'evidence': [{
                        'type': 'geotagged_photo',
                        'url': photo_evidence.s3_url,
                        'hash': photo_evidence.hash,
                        'timestamp': photo_evidence.timestamp,
                        'description': 'Milestone completion evidence'
                    }]
                },
                'verifiedAt': datetime.utcnow().isoformat(),
                'verifierSignature': 'system_verified'
            }
            
            # Call blockchain service to mint credential
            credential_result = await self.blockchain_service.mint_credential(verification_data)
            
            if credential_result['success']:
                log_business_event(logger, 'credential_minted', {
                    'credential_id': credential_result['credential_id'],
                    'worker_id': milestone.worker_id,
                    'milestone_id': milestone.milestone_id,
                    'blockchain_tx_id': credential_result['transaction_id']
                })
            
            return credential_result
            
        except Exception as e:
            logger.error(f"Error minting verifiable credential: {str(e)}")
            return None

# AWS Lambda handler
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for agentic execution
    
    Supported events:
    - S3 photo upload events
    - Direct milestone verification requests
    - Payment status updates
    """
    
    try:
        # Set correlation ID for request tracing
        correlation_id = event.get('requestContext', {}).get('requestId', str(uuid.uuid4()))
        set_correlation_id(correlation_id)
        
        logger.info(f"Processing agentic execution event: {event.get('source', 'unknown')}")
        
        # Initialize service
        agentic_service = AgenticExecutionService()
        
        # Determine event type and route accordingly
        event_source = event.get('source', '')
        
        if event_source == 'aws:s3' or 'Records' in event:
            # S3 upload event
            return asyncio.run(handle_s3_upload_event(agentic_service, event))
        
        elif event.get('httpMethod') == 'POST':
            # API Gateway request
            body = json.loads(event.get('body', '{}'))
            return asyncio.run(handle_api_request(agentic_service, body))
        
        else:
            # Direct invocation
            return asyncio.run(handle_direct_invocation(agentic_service, event))
            
    except Exception as e:
        logger.error(f"Lambda execution failed: {str(e)}")
        return create_error_response(500, str(e))

async def handle_s3_upload_event(service: AgenticExecutionService, event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle S3 photo upload events"""
    try:
        # Extract S3 event details
        records = event.get('Records', [])
        if not records:
            return create_error_response(400, "No S3 records found in event")
        
        results = []
        for record in records:
            s3_info = record.get('s3', {})
            bucket = s3_info.get('bucket', {}).get('name', '')
            key = s3_info.get('object', {}).get('key', '')
            
            # Extract metadata from S3 object key (assuming structured naming)
            # Format: evidence/{worker_id}/{milestone_id}/{filename}
            key_parts = key.split('/')
            if len(key_parts) >= 4 and key_parts[0] == 'evidence':
                worker_id = key_parts[1]
                milestone_id = key_parts[2]
                
                # Get photo data from S3
                s3_client = boto3.client('s3')
                response = s3_client.get_object(Bucket=bucket, Key=key)
                photo_data = base64.b64encode(response['Body'].read()).decode('utf-8')
                
                # Process milestone evidence
                result = await service.process_milestone_evidence({
                    'worker_id': worker_id,
                    'milestone_id': milestone_id,
                    'photo_data': photo_data,
                    'photo_metadata': {
                        's3_bucket': bucket,
                        's3_key': key,
                        'upload_source': 's3_event'
                    }
                })
                
                results.append(result)
        
        return create_response(200, {
            'processed_records': len(results),
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error handling S3 upload event: {str(e)}")
        return create_error_response(500, str(e))

async def handle_api_request(service: AgenticExecutionService, body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle API Gateway requests"""
    try:
        action = body.get('action', 'process_evidence')
        
        if action == 'process_evidence':
            result = await service.process_milestone_evidence(body)
            return create_response(200, result)
        
        else:
            return create_error_response(400, f"Unknown action: {action}")
            
    except Exception as e:
        logger.error(f"Error handling API request: {str(e)}")
        return create_error_response(500, str(e))

async def handle_direct_invocation(service: AgenticExecutionService, event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle direct Lambda invocations"""
    try:
        result = await service.process_milestone_evidence(event)
        return {
            'statusCode': 200,
            'body': json.dumps(result, default=str)
        }
        
    except Exception as e:
        logger.error(f"Error handling direct invocation: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }