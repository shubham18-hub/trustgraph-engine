"""
UPI Service for TrustGraph Engine
Handles UPI payment processing and integration with NPCI
Supports automatic milestone-based payment disbursal
"""

import json
import boto3
import asyncio
import aiohttp
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import os
import hashlib
import hmac
import uuid
from dataclasses import dataclass
from decimal import Decimal

from src.utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class UPIPayment:
    """Represents a UPI payment transaction"""
    payment_id: str
    transaction_ref: str
    payee_upi_id: str
    payer_upi_id: str
    amount: Decimal
    currency: str
    description: str
    status: str
    initiated_at: str
    completed_at: Optional[str] = None
    failure_reason: Optional[str] = None
    gateway_response: Optional[Dict[str, Any]] = None

class UPIService:
    """Service for handling UPI payments and integrations"""
    
    def __init__(self):
        self.region = 'ap-south-1'
        self.dynamodb = boto3.resource('dynamodb', region_name=self.region)
        self.secrets_manager = boto3.client('secretsmanager', region_name=self.region)
        
        # DynamoDB table for payment tracking
        self.payments_table = self.dynamodb.Table(
            os.environ.get('UPI_PAYMENTS_TABLE', 'trustgraph-upi-payments')
        )
        
        # UPI Gateway configuration
        self.gateway_config = self._load_gateway_config()
        
        # Payment limits and validation
        self.min_amount = Decimal('1.00')  # Minimum ₹1
        self.max_amount = Decimal('200000.00')  # Maximum ₹2,00,000 per transaction
        self.daily_limit = Decimal('1000000.00')  # ₹10,00,000 per day per user
        
    def _load_gateway_config(self) -> Dict[str, Any]:
        """Load UPI gateway configuration from AWS Secrets Manager"""
        try:
            secret_name = 'trustgraph/upi/gateway-config'
            response = self.secrets_manager.get_secret_value(SecretId=secret_name)
            config = json.loads(response['SecretString'])
            
            return {
                'primary_gateway': config.get('primary_gateway', 'paytm'),
                'fallback_gateway': config.get('fallback_gateway', 'phonepe'),
                'merchant_id': config.get('merchant_id'),
                'merchant_key': config.get('merchant_key'),
                'api_endpoints': config.get('api_endpoints', {}),
                'webhook_secret': config.get('webhook_secret'),
                'timeout': config.get('timeout', 30)
            }
            
        except Exception as e:
            logger.error(f"Failed to load UPI gateway config: {str(e)}")
            # Return default configuration
            return {
                'primary_gateway': 'paytm',
                'fallback_gateway': 'phonepe',
                'merchant_id': 'TRUSTGRAPH001',
                'api_endpoints': {
                    'paytm': 'https://securegw.paytm.in/theia/api/v1/initiateTransaction',
                    'phonepe': 'https://api.phonepe.com/apis/hermes/pg/v1/pay'
                },
                'timeout': 30
            }
    
    async def initiate_payment(self, payment_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Initiate a UPI payment transaction
        
        Args:
            payment_request: Payment details including amount, UPI ID, description
            
        Returns:
            Payment initiation result
        """
        try:
            # Validate payment request
            validation_result = await self._validate_payment_request(payment_request)
            if not validation_result['valid']:
                return {
                    'success': False,
                    'error': validation_result['error'],
                    'error_code': 'VALIDATION_FAILED'
                }
            
            # Generate payment ID and transaction reference
            payment_id = payment_request.get('payment_id', f"pay_{uuid.uuid4().hex[:12]}")
            transaction_ref = f"TG{int(datetime.utcnow().timestamp())}{payment_id[-6:]}"
            
            # Create payment record
            payment = UPIPayment(
                payment_id=payment_id,
                transaction_ref=transaction_ref,
                payee_upi_id=payment_request['payee_upi_id'],
                payer_upi_id=self.gateway_config['merchant_id'] + '@paytm',
                amount=Decimal(str(payment_request['amount'])),
                currency=payment_request.get('currency', 'INR'),
                description=payment_request['description'],
                status='initiated',
                initiated_at=datetime.utcnow().isoformat()
            )
            
            # Store payment record
            await self._store_payment_record(payment)
            
            # Process payment through primary gateway
            gateway_result = await self._process_payment_gateway(payment, 'primary')
            
            if gateway_result['success']:
                # Update payment status
                payment.status = 'processing'
                payment.gateway_response = gateway_result['response']
                await self._update_payment_record(payment)
                
                logger.info(f"Payment {payment_id} initiated successfully via {self.gateway_config['primary_gateway']}")
                
                return {
                    'success': True,
                    'payment_id': payment_id,
                    'transaction_ref': transaction_ref,
                    'status': 'processing',
                    'gateway_response': gateway_result['response'],
                    'estimated_completion': (datetime.utcnow() + timedelta(minutes=5)).isoformat()
                }
            else:
                # Try fallback gateway
                logger.warning(f"Primary gateway failed for payment {payment_id}, trying fallback")
                
                fallback_result = await self._process_payment_gateway(payment, 'fallback')
                
                if fallback_result['success']:
                    payment.status = 'processing'
                    payment.gateway_response = fallback_result['response']
                    await self._update_payment_record(payment)
                    
                    return {
                        'success': True,
                        'payment_id': payment_id,
                        'transaction_ref': transaction_ref,
                        'status': 'processing',
                        'gateway_response': fallback_result['response'],
                        'gateway_used': 'fallback'
                    }
                else:
                    # Both gateways failed
                    payment.status = 'failed'
                    payment.failure_reason = f"Both gateways failed: {gateway_result['error']}, {fallback_result['error']}"
                    await self._update_payment_record(payment)
                    
                    return {
                        'success': False,
                        'payment_id': payment_id,
                        'error': 'Payment processing failed on all gateways',
                        'details': {
                            'primary_error': gateway_result['error'],
                            'fallback_error': fallback_result['error']
                        }
                    }
                    
        except Exception as e:
            logger.error(f"Error initiating payment: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'INTERNAL_ERROR'
            }
    
    async def check_payment_status(self, payment_id: str) -> Dict[str, Any]:
        """
        Check the status of a UPI payment
        
        Args:
            payment_id: Payment identifier
            
        Returns:
            Payment status information
        """
        try:
            # Get payment record from DynamoDB
            payment = await self._get_payment_record(payment_id)
            if not payment:
                return {
                    'success': False,
                    'error': f'Payment {payment_id} not found',
                    'error_code': 'PAYMENT_NOT_FOUND'
                }
            
            # If payment is still processing, check with gateway
            if payment.status == 'processing':
                gateway_status = await self._check_gateway_status(payment)
                
                if gateway_status['success']:
                    # Update payment status based on gateway response
                    gateway_payment_status = gateway_status['status']
                    
                    if gateway_payment_status == 'SUCCESS':
                        payment.status = 'completed'
                        payment.completed_at = datetime.utcnow().isoformat()
                    elif gateway_payment_status == 'FAILED':
                        payment.status = 'failed'
                        payment.failure_reason = gateway_status.get('failure_reason', 'Gateway reported failure')
                    # If still processing, keep current status
                    
                    await self._update_payment_record(payment)
            
            return {
                'success': True,
                'payment_id': payment_id,
                'status': payment.status,
                'transaction_ref': payment.transaction_ref,
                'amount': float(payment.amount),
                'currency': payment.currency,
                'payee_upi_id': payment.payee_upi_id,
                'initiated_at': payment.initiated_at,
                'completed_at': payment.completed_at,
                'failure_reason': payment.failure_reason,
                'last_checked': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error checking payment status for {payment_id}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'STATUS_CHECK_FAILED'
            }
    
    async def handle_webhook(self, webhook_data: Dict[str, Any], signature: str) -> Dict[str, Any]:
        """
        Handle UPI gateway webhook notifications
        
        Args:
            webhook_data: Webhook payload from gateway
            signature: Webhook signature for verification
            
        Returns:
            Webhook processing result
        """
        try:
            # Verify webhook signature
            if not self._verify_webhook_signature(webhook_data, signature):
                return {
                    'success': False,
                    'error': 'Invalid webhook signature',
                    'error_code': 'INVALID_SIGNATURE'
                }
            
            # Extract payment information from webhook
            payment_id = webhook_data.get('merchantTransactionId') or webhook_data.get('payment_id')
            transaction_ref = webhook_data.get('transactionId') or webhook_data.get('transaction_ref')
            status = webhook_data.get('code') or webhook_data.get('status')
            
            if not payment_id:
                return {
                    'success': False,
                    'error': 'Payment ID not found in webhook data',
                    'error_code': 'MISSING_PAYMENT_ID'
                }
            
            # Get payment record
            payment = await self._get_payment_record(payment_id)
            if not payment:
                logger.warning(f"Webhook received for unknown payment: {payment_id}")
                return {
                    'success': False,
                    'error': f'Payment {payment_id} not found',
                    'error_code': 'PAYMENT_NOT_FOUND'
                }
            
            # Update payment status based on webhook
            previous_status = payment.status
            
            if status in ['PAYMENT_SUCCESS', 'SUCCESS', 'COMPLETED']:
                payment.status = 'completed'
                payment.completed_at = datetime.utcnow().isoformat()
            elif status in ['PAYMENT_ERROR', 'FAILED', 'FAILURE']:
                payment.status = 'failed'
                payment.failure_reason = webhook_data.get('message', 'Payment failed')
            elif status in ['PAYMENT_PENDING', 'PENDING', 'PROCESSING']:
                payment.status = 'processing'
            
            # Update gateway response
            payment.gateway_response = webhook_data
            
            # Store updated payment record
            await self._update_payment_record(payment)
            
            # Log status change
            if previous_status != payment.status:
                logger.info(f"Payment {payment_id} status changed from {previous_status} to {payment.status}")
                
                # Trigger downstream notifications if payment completed
                if payment.status == 'completed':
                    await self._notify_payment_completion(payment)
            
            return {
                'success': True,
                'payment_id': payment_id,
                'previous_status': previous_status,
                'new_status': payment.status,
                'processed_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error handling webhook: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'WEBHOOK_PROCESSING_FAILED'
            }
    
    async def get_payment_history(self, user_id: str, limit: int = 50) -> Dict[str, Any]:
        """
        Get payment history for a user
        
        Args:
            user_id: User identifier
            limit: Maximum number of payments to return
            
        Returns:
            Payment history
        """
        try:
            # Query DynamoDB for user's payments
            # This assumes we have a GSI on payee_upi_id or user_id
            response = self.payments_table.query(
                IndexName='payee-index',  # Assuming GSI exists
                KeyConditionExpression='payee_upi_id = :upi_id',
                ExpressionAttributeValues={
                    ':upi_id': f"{user_id}@paytm"  # Assuming UPI ID format
                },
                Limit=limit,
                ScanIndexForward=False  # Get most recent first
            )
            
            payments = []
            for item in response.get('Items', []):
                payments.append({
                    'payment_id': item['payment_id'],
                    'transaction_ref': item['transaction_ref'],
                    'amount': float(item['amount']),
                    'currency': item['currency'],
                    'description': item['description'],
                    'status': item['status'],
                    'initiated_at': item['initiated_at'],
                    'completed_at': item.get('completed_at'),
                    'failure_reason': item.get('failure_reason')
                })
            
            return {
                'success': True,
                'user_id': user_id,
                'payments': payments,
                'payment_count': len(payments),
                'total_amount': sum(p['amount'] for p in payments if p['status'] == 'completed'),
                'query_timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error retrieving payment history for {user_id}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'HISTORY_RETRIEVAL_FAILED'
            }
    
    async def _validate_payment_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Validate payment request parameters"""
        try:
            # Required fields
            required_fields = ['payee_upi_id', 'amount', 'description']
            for field in required_fields:
                if field not in request:
                    return {
                        'valid': False,
                        'error': f'Missing required field: {field}'
                    }
            
            # Validate UPI ID format
            upi_id = request['payee_upi_id']
            if '@' not in upi_id or len(upi_id.split('@')) != 2:
                return {
                    'valid': False,
                    'error': 'Invalid UPI ID format'
                }
            
            # Validate amount
            try:
                amount = Decimal(str(request['amount']))
                if amount < self.min_amount:
                    return {
                        'valid': False,
                        'error': f'Amount below minimum limit of ₹{self.min_amount}'
                    }
                if amount > self.max_amount:
                    return {
                        'valid': False,
                        'error': f'Amount exceeds maximum limit of ₹{self.max_amount}'
                    }
            except (ValueError, TypeError):
                return {
                    'valid': False,
                    'error': 'Invalid amount format'
                }
            
            # Validate description
            description = request['description']
            if len(description) < 5 or len(description) > 200:
                return {
                    'valid': False,
                    'error': 'Description must be between 5 and 200 characters'
                }
            
            return {'valid': True}
            
        except Exception as e:
            return {
                'valid': False,
                'error': f'Validation error: {str(e)}'
            }
    
    async def _process_payment_gateway(self, payment: UPIPayment, gateway_type: str) -> Dict[str, Any]:
        """Process payment through specified gateway"""
        try:
            gateway_name = (self.gateway_config['primary_gateway'] if gateway_type == 'primary' 
                          else self.gateway_config['fallback_gateway'])
            
            if gateway_name == 'paytm':
                return await self._process_paytm_payment(payment)
            elif gateway_name == 'phonepe':
                return await self._process_phonepe_payment(payment)
            else:
                return {
                    'success': False,
                    'error': f'Unsupported gateway: {gateway_name}'
                }
                
        except Exception as e:
            logger.error(f"Gateway processing error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _process_paytm_payment(self, payment: UPIPayment) -> Dict[str, Any]:
        """Process payment through Paytm gateway"""
        try:
            # Prepare Paytm API request
            paytm_request = {
                'body': {
                    'requestType': 'Payment',
                    'mid': self.gateway_config['merchant_id'],
                    'websiteName': 'TRUSTGRAPH',
                    'orderId': payment.transaction_ref,
                    'txnAmount': {
                        'value': str(payment.amount),
                        'currency': payment.currency
                    },
                    'userInfo': {
                        'custId': payment.payee_upi_id.split('@')[0]
                    },
                    'paymentMode': {
                        'mode': 'UPI',
                        'upiDetails': {
                            'vpa': payment.payee_upi_id
                        }
                    }
                }
            }
            
            # Generate checksum
            checksum = self._generate_paytm_checksum(paytm_request['body'])
            paytm_request['head'] = {
                'signature': checksum
            }
            
            # Make API call
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.gateway_config['api_endpoints']['paytm'],
                    json=paytm_request,
                    timeout=aiohttp.ClientTimeout(total=self.gateway_config['timeout'])
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        
                        if result['body']['resultInfo']['resultStatus'] == 'S':
                            return {
                                'success': True,
                                'response': result['body'],
                                'gateway': 'paytm'
                            }
                        else:
                            return {
                                'success': False,
                                'error': result['body']['resultInfo']['resultMsg'],
                                'gateway': 'paytm'
                            }
                    else:
                        return {
                            'success': False,
                            'error': f'Paytm API error: {response.status}',
                            'gateway': 'paytm'
                        }
                        
        except Exception as e:
            return {
                'success': False,
                'error': f'Paytm processing error: {str(e)}',
                'gateway': 'paytm'
            }
    
    async def _process_phonepe_payment(self, payment: UPIPayment) -> Dict[str, Any]:
        """Process payment through PhonePe gateway"""
        try:
            # Prepare PhonePe API request
            phonepe_request = {
                'merchantId': self.gateway_config['merchant_id'],
                'merchantTransactionId': payment.transaction_ref,
                'merchantUserId': payment.payee_upi_id.split('@')[0],
                'amount': int(payment.amount * 100),  # Amount in paise
                'redirectUrl': 'https://trustgraph.gov.in/payment/callback',
                'redirectMode': 'POST',
                'callbackUrl': 'https://trustgraph.gov.in/api/upi/webhook',
                'paymentInstrument': {
                    'type': 'UPI_COLLECT',
                    'vpa': payment.payee_upi_id
                }
            }
            
            # Encode and generate checksum
            encoded_request = base64.b64encode(json.dumps(phonepe_request).encode()).decode()
            checksum = self._generate_phonepe_checksum(encoded_request)
            
            headers = {
                'Content-Type': 'application/json',
                'X-VERIFY': checksum
            }
            
            payload = {
                'request': encoded_request
            }
            
            # Make API call
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.gateway_config['api_endpoints']['phonepe'],
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.gateway_config['timeout'])
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        
                        if result['success']:
                            return {
                                'success': True,
                                'response': result['data'],
                                'gateway': 'phonepe'
                            }
                        else:
                            return {
                                'success': False,
                                'error': result['message'],
                                'gateway': 'phonepe'
                            }
                    else:
                        return {
                            'success': False,
                            'error': f'PhonePe API error: {response.status}',
                            'gateway': 'phonepe'
                        }
                        
        except Exception as e:
            return {
                'success': False,
                'error': f'PhonePe processing error: {str(e)}',
                'gateway': 'phonepe'
            }
    
    def _generate_paytm_checksum(self, params: Dict[str, Any]) -> str:
        """Generate Paytm checksum"""
        # Simplified checksum generation (use Paytm's official library in production)
        param_str = '|'.join([str(v) for v in sorted(params.values())])
        return hashlib.sha256((param_str + self.gateway_config['merchant_key']).encode()).hexdigest()
    
    def _generate_phonepe_checksum(self, encoded_request: str) -> str:
        """Generate PhonePe checksum"""
        payload = encoded_request + '/pg/v1/pay' + self.gateway_config['merchant_key']
        return hashlib.sha256(payload.encode()).hexdigest() + '###1'
    
    def _verify_webhook_signature(self, data: Dict[str, Any], signature: str) -> bool:
        """Verify webhook signature"""
        try:
            expected_signature = hmac.new(
                self.gateway_config['webhook_secret'].encode(),
                json.dumps(data, sort_keys=True).encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(expected_signature, signature)
            
        except Exception as e:
            logger.error(f"Webhook signature verification failed: {str(e)}")
            return False
    
    async def _store_payment_record(self, payment: UPIPayment) -> None:
        """Store payment record in DynamoDB"""
        try:
            item = {
                'payment_id': payment.payment_id,
                'transaction_ref': payment.transaction_ref,
                'payee_upi_id': payment.payee_upi_id,
                'payer_upi_id': payment.payer_upi_id,
                'amount': payment.amount,
                'currency': payment.currency,
                'description': payment.description,
                'status': payment.status,
                'initiated_at': payment.initiated_at,
                'completed_at': payment.completed_at,
                'failure_reason': payment.failure_reason,
                'gateway_response': payment.gateway_response
            }
            
            # Remove None values
            item = {k: v for k, v in item.items() if v is not None}
            
            self.payments_table.put_item(Item=item)
            
        except Exception as e:
            logger.error(f"Error storing payment record: {str(e)}")
            raise
    
    async def _update_payment_record(self, payment: UPIPayment) -> None:
        """Update payment record in DynamoDB"""
        try:
            update_expression = "SET #status = :status, updated_at = :updated_at"
            expression_values = {
                ':status': payment.status,
                ':updated_at': datetime.utcnow().isoformat()
            }
            expression_names = {'#status': 'status'}
            
            if payment.completed_at:
                update_expression += ", completed_at = :completed_at"
                expression_values[':completed_at'] = payment.completed_at
            
            if payment.failure_reason:
                update_expression += ", failure_reason = :failure_reason"
                expression_values[':failure_reason'] = payment.failure_reason
            
            if payment.gateway_response:
                update_expression += ", gateway_response = :gateway_response"
                expression_values[':gateway_response'] = payment.gateway_response
            
            self.payments_table.update_item(
                Key={'payment_id': payment.payment_id},
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expression_names,
                ExpressionAttributeValues=expression_values
            )
            
        except Exception as e:
            logger.error(f"Error updating payment record: {str(e)}")
            raise
    
    async def _get_payment_record(self, payment_id: str) -> Optional[UPIPayment]:
        """Get payment record from DynamoDB"""
        try:
            response = self.payments_table.get_item(Key={'payment_id': payment_id})
            
            if 'Item' not in response:
                return None
            
            item = response['Item']
            
            return UPIPayment(
                payment_id=item['payment_id'],
                transaction_ref=item['transaction_ref'],
                payee_upi_id=item['payee_upi_id'],
                payer_upi_id=item['payer_upi_id'],
                amount=Decimal(str(item['amount'])),
                currency=item['currency'],
                description=item['description'],
                status=item['status'],
                initiated_at=item['initiated_at'],
                completed_at=item.get('completed_at'),
                failure_reason=item.get('failure_reason'),
                gateway_response=item.get('gateway_response')
            )
            
        except Exception as e:
            logger.error(f"Error retrieving payment record: {str(e)}")
            return None
    
    async def _check_gateway_status(self, payment: UPIPayment) -> Dict[str, Any]:
        """Check payment status with gateway"""
        # This would implement actual gateway status check APIs
        # For now, return a placeholder response
        return {
            'success': True,
            'status': 'PROCESSING',
            'message': 'Payment is being processed'
        }
    
    async def _notify_payment_completion(self, payment: UPIPayment) -> None:
        """Notify downstream services of payment completion"""
        try:
            # Send notification to EventBridge for downstream processing
            eventbridge = boto3.client('events', region_name=self.region)
            
            event_detail = {
                'payment_id': payment.payment_id,
                'transaction_ref': payment.transaction_ref,
                'payee_upi_id': payment.payee_upi_id,
                'amount': float(payment.amount),
                'currency': payment.currency,
                'completed_at': payment.completed_at
            }
            
            eventbridge.put_events(
                Entries=[
                    {
                        'Source': 'trustgraph.upi',
                        'DetailType': 'Payment Completed',
                        'Detail': json.dumps(event_detail),
                        'Time': datetime.utcnow()
                    }
                ]
            )
            
            logger.info(f"Payment completion notification sent for {payment.payment_id}")
            
        except Exception as e:
            logger.error(f"Error sending payment completion notification: {str(e)}")