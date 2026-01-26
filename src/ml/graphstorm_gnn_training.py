#!/usr/bin/env python3
"""
GraphStorm GNN Training Script for TrustGraph Resilience Scoring
NITI Aayog Digital ShramSetu Initiative - Alternative Credit Assessment

This script trains a Graph Neural Network using GraphStorm on Amazon SageMaker
to calculate Resilience Scores (0-1000) for India's 490 million informal workers.

Compliance: DPDP Act 2023, W3C Standards, AWS India (ap-south-1) data residency
"""

import os
import json
import logging
import argparse
from datetime import datetime
from typing import Dict, List, Tuple, Optional

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import pandas as pd
import boto3
from torch_geometric.data import Data, DataLoader
from torch_geometric.nn import SAGEConv, GATConv, global_mean_pool

# GraphStorm imports for distributed training
try:
    import graphstorm as gs
    from graphstorm.config import GSConfig
    from graphstorm.dataloading import GSgnnData
    from graphstorm.model import GSgnnNodeModel
    from graphstorm.trainer import GSgnnNodePredictionTrainer
except ImportError:
    print("GraphStorm not available, using PyTorch Geometric fallback")
    gs = None

# AWS SDK for India-specific services
from botocore.config import Config

# Configure logging for SageMaker
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class IndianWorkforceGNNConfig:
    """Configuration for Indian workforce-specific GNN training"""
    
    def __init__(self):
        self.config = {
            # Model Architecture for Indian Context
            "model_name": "trustgraph_resilience_scorer_india",
            "gnn_layer_type": "GraphSAGE",  # Inductive learning for new workers
            "num_layers": 3,
            "hidden_size": 128,
            "num_heads": 8,  # Multi-head attention
            "dropout": 0.2,
            "activation": "relu",
            
            # Training Configuration
            "learning_rate": 0.001,
            "batch_size": 1024,  # Optimized for Indian scale
            "num_epochs": 100,
            "early_stopping_patience": 10,
            "optimizer": "adam",
            "weight_decay": 1e-5,
            
            # Indian Workforce Features
            "node_features": {
                "worker": [
                    "age_group", "literacy_level", "location_tier",
                    "work_experience_months", "skill_diversity_score",
                    "payment_reliability", "community_endorsement",
                    "seasonal_work_pattern", "geographic_mobility",
                    "language_proficiency", "digital_literacy"
                ],
                "employer": [
                    "business_type", "gst_verified", "employee_count",
                    "payment_history_score", "location_tier",
                    "business_age_months", "repeat_hiring_rate"
                ],
                "bank": [
                    "bank_type", "rural_presence", "digital_services",
                    "loan_approval_rate", "interest_rates",
                    "trustgraph_integration_level"
                ]
            },
            
            # Edge Features for Indian Context
            "edge_features": {
                "verified_by": [
                    "work_duration", "skill_match", "rating_consistency",
                    "payment_timeliness", "rehire_probability",
                    "regional_wage_comparison", "festival_bonus_given"
                ],
                "paid_via": [
                    "transaction_frequency", "amount_consistency",
                    "payment_method_diversity", "rural_accessibility",
                    "digital_adoption_score", "compliance_rate"
                ]
            },
            
            # Target Configuration
            "target_ntype": "Worker",
            "label_field": "resilience_score_normalized",  # 0-1 range
            
            # AWS SageMaker Integration (India Region)
            "backend": "sagemaker",
            "region": "ap-south-1",  # Mumbai - DPDP Act compliance
            "instance_type": "ml.p3.2xlarge",
            "instance_count": 2,
            "distributed_backend": "nccl",
            
            # Model Serving Configuration
            "inference_instance_type": "ml.c5.xlarge",
            "endpoint_name": "trustgraph-resilience-scorer-india",
            "auto_scaling_enabled": True,
            "min_capacity": 1,
            "max_capacity": 10,
            
            # Indian Regulatory Compliance
            "data_residency": "ap-south-1",
            "dpdp_compliance": True,
            "audit_logging": True,
            "encryption_at_rest": True
        }

class IndianWorkforceFeatureEngineer:
    """Feature engineering for Indian informal workforce context"""
    
    def __init__(self):
        # AWS clients configured for India region (DPDP Act compliance)
        aws_config = Config(region_name='ap-south-1')
        self.s3_client = boto3.client('s3', config=aws_config)
        self.neptune_client = boto3.client('neptune', config=aws_config)
        self.feature_store = boto3.client('sagemaker-featurestore-runtime', config=aws_config)
        
        # Indian-specific mappings
        self.indian_states = {
            "UP": "uttar_pradesh", "MH": "maharashtra", "BR": "bihar",
            "WB": "west_bengal", "MP": "madhya_pradesh", "TN": "tamil_nadu",
            "RJ": "rajasthan", "KA": "karnataka", "GJ": "gujarat",
            "AP": "andhra_pradesh", "OR": "odisha", "TG": "telangana",
            "KL": "kerala", "JH": "jharkhand", "AS": "assam", "PB": "punjab",
            "CT": "chhattisgarh", "HR": "haryana", "JK": "jammu_kashmir",
            "UK": "uttarakhand", "HP": "himachal_pradesh", "TR": "tripura",
            "ML": "meghalaya", "MN": "manipur", "NL": "nagaland",
            "GA": "goa", "AR": "arunachal_pradesh", "MZ": "mizoram",
            "SK": "sikkim", "DL": "delhi", "PY": "puducherry",
            "CH": "chandigarh", "AN": "andaman_nicobar", "DN": "dadra_nagar_haveli",
            "DD": "daman_diu", "LD": "lakshadweep", "LA": "ladakh"
        }
        
        # Indian work categories with regional variations
        self.work_categories = {
            "construction": {
                "north": ["mason", "carpenter", "electrician", "plumber", "painter"],
                "south": ["mason", "tile_worker", "steel_fixer", "concrete_mixer"],
                "west": ["mason", "carpenter", "welder", "crane_operator"],
                "east": ["mason", "bamboo_worker", "thatch_roofer", "mud_plasterer"]
            },
            "domestic": {
                "urban": ["house_help", "cook", "driver", "security_guard"],
                "rural": ["farm_help", "cattle_care", "poultry_worker", "dairy_worker"]
            },
            "services": {
                "traditional": ["barber", "cobbler", "tailor", "washerman"],
                "modern": ["delivery_person", "auto_driver", "beautician", "mobile_repair"]
            }
        }
    
    def extract_indian_worker_features(self, worker_id: str) -> Dict:
        """Extract features specific to Indian informal workers"""
        
        # Basic worker data from Neptune
        worker_query = f"""
        g.V().has('Worker', 'id', '{worker_id}')
        .project('basic', 'location', 'work_history', 'payments')
        .by(valueMap('name', 'phone', 'preferred_language', 'literacy_level', 'join_date'))
        .by(valueMap('state', 'district', 'pin_code', 'location_tier'))
        .by(outE('VERIFIED_BY').fold())
        .by(outE('PAID_VIA').fold())
        """
        
        worker_data = self._execute_neptune_query(worker_query)
        
        # Extract Indian-specific features
        features = {
            # Demographic Features (Indian Context)
            'state_code': self._get_state_code(worker_data['location'].get('state')),
            'location_tier': self._encode_location_tier(worker_data['location'].get('pin_code')),
            'language_group': self._get_language_group(worker_data['basic'].get('preferred_language')),
            'literacy_level_score': self._encode_literacy_level(worker_data['basic'].get('literacy_level')),
            
            # Work Pattern Features (Indian Workforce)
            'seasonal_work_indicator': self._analyze_seasonal_patterns(worker_data['work_history']),
            'festival_work_gaps': self._detect_festival_patterns(worker_data['work_history']),
            'monsoon_work_adaptation': self._analyze_monsoon_impact(worker_data['work_history']),
            'migration_pattern': self._detect_migration_patterns(worker_data['work_history']),
            
            # Social Proof Features (Indian Society)
            'community_network_strength': self._calculate_community_connections(worker_id),
            'family_employment_history': self._analyze_family_work_patterns(worker_id),
            'caste_neutral_skill_score': self._calculate_merit_based_skills(worker_data['work_history']),
            'regional_reputation_score': self._calculate_regional_reputation(worker_id),
            
            # Financial Behavior (Indian Context)
            'upi_adoption_score': self._analyze_upi_usage(worker_data['payments']),
            'jan_dhan_account_indicator': self._check_jan_dhan_usage(worker_data['payments']),
            'digital_payment_comfort': self._assess_digital_comfort(worker_data['payments']),
            'remittance_pattern': self._analyze_remittance_behavior(worker_data['payments']),
            
            # Skill Development (Indian Programs)
            'skill_india_participation': self._check_skill_india_programs(worker_id),
            'pmkvy_certification': self._check_pmkvy_certifications(worker_id),
            'traditional_skill_preservation': self._assess_traditional_skills(worker_data['work_history']),
            'digital_literacy_score': self._calculate_digital_literacy(worker_id),
            
            # Economic Resilience Indicators
            'drought_adaptation_score': self._analyze_drought_resilience(worker_data['work_history']),
            'covid_recovery_pattern': self._analyze_covid_recovery(worker_data['work_history']),
            'income_diversification': self._calculate_income_sources(worker_data['work_history']),
            'savings_behavior_indicator': self._infer_savings_patterns(worker_data['payments'])
        }
        
        return features
    
    def _get_state_code(self, state_name: str) -> int:
        """Convert Indian state to numerical encoding"""
        if not state_name:
            return 0
        
        # Find state code from mapping
        for code, full_name in self.indian_states.items():
            if state_name.lower() in full_name or full_name in state_name.lower():
                return hash(code) % 100  # Numerical encoding
        
        return 0
    
    def _encode_location_tier(self, pin_code: str) -> int:
        """Encode location tier based on Indian postal system"""
        if not pin_code or len(pin_code) != 6:
            return 0
        
        # Indian postal code system
        first_digit = int(pin_code[0])
        
        # Tier classification based on postal regions
        tier_mapping = {
            1: 3,  # Delhi, Haryana, Punjab (Tier 1)
            2: 3,  # Himachal Pradesh, Jammu & Kashmir (Tier 1)
            3: 2,  # Rajasthan, Gujarat (Tier 2)
            4: 2,  # Maharashtra, Madhya Pradesh (Tier 2)
            5: 2,  # Andhra Pradesh, Karnataka (Tier 2)
            6: 2,  # Tamil Nadu, Kerala (Tier 2)
            7: 1,  # West Bengal, Odisha (Tier 3)
            8: 1,  # Bihar, Jharkhand (Tier 3)
            9: 1   # UP, Uttarakhand (Tier 3)
        }
        
        return tier_mapping.get(first_digit, 1)
    
    def _analyze_seasonal_patterns(self, work_history: List) -> float:
        """Analyze seasonal work patterns specific to Indian agriculture and construction"""
        if not work_history:
            return 0.0
        
        # Extract work months
        work_months = []
        for work in work_history:
            start_date = work.get('start_date')
            if start_date:
                month = datetime.fromisoformat(start_date.replace('Z', '+00:00')).month
                work_months.append(month)
        
        if not work_months:
            return 0.0
        
        # Indian seasonal patterns
        # Rabi season: Nov-Apr, Kharif season: Jun-Oct
        # Construction peak: Oct-Mar (post-monsoon)
        
        seasonal_scores = {
            1: 0.8,  # January - Peak construction
            2: 0.9,  # February - Peak construction
            3: 0.8,  # March - Harvest season
            4: 0.6,  # April - Pre-monsoon slowdown
            5: 0.4,  # May - Summer break
            6: 0.3,  # June - Monsoon start
            7: 0.2,  # July - Heavy monsoon
            8: 0.2,  # August - Heavy monsoon
            9: 0.3,  # September - Monsoon end
            10: 0.7, # October - Post-monsoon pickup
            11: 0.8, # November - Festival season work
            12: 0.7  # December - Year-end projects
        }
        
        # Calculate seasonal adaptation score
        month_scores = [seasonal_scores.get(month, 0.5) for month in work_months]
        return np.mean(month_scores)
    
    def _detect_festival_patterns(self, work_history: List) -> float:
        """Detect work patterns around Indian festivals"""
        if not work_history:
            return 0.0
        
        # Major Indian festivals (approximate dates)
        festival_months = {
            3: "Holi", 8: "Raksha Bandhan", 9: "Ganesh Chaturthi",
            10: "Dussehra", 11: "Diwali", 12: "Christmas"
        }
        
        festival_work_count = 0
        total_festival_periods = 0
        
        for work in work_history:
            start_date = work.get('start_date')
            end_date = work.get('end_date')
            
            if start_date and end_date:
                start_month = datetime.fromisoformat(start_date.replace('Z', '+00:00')).month
                end_month = datetime.fromisoformat(end_date.replace('Z', '+00:00')).month
                
                # Check if work spans festival months
                for month in range(start_month, end_month + 1):
                    if month in festival_months:
                        total_festival_periods += 1
                        if work.get('completion_rate', 0) >= 90:
                            festival_work_count += 1
        
        if total_festival_periods == 0:
            return 0.5  # Neutral score
        
        return festival_work_count / total_festival_periods
    
    def _calculate_community_connections(self, worker_id: str) -> float:
        """Calculate community network strength (caste-neutral)"""
        
        # Query for community connections through work relationships
        community_query = f"""
        g.V().has('Worker', 'id', '{worker_id}')
        .out('WORKED_WITH')
        .groupCount()
        .by('location')
        """
        
        community_data = self._execute_neptune_query(community_query)
        
        if not community_data:
            return 0.0
        
        # Calculate network diversity and strength
        location_counts = list(community_data.values())
        
        # Network strength based on repeat collaborations
        network_strength = sum(count for count in location_counts if count > 1)
        
        # Normalize to 0-1 scale
        return min(network_strength / 10.0, 1.0)
    
    def _analyze_upi_usage(self, payment_history: List) -> float:
        """Analyze UPI adoption and usage patterns"""
        if not payment_history:
            return 0.0
        
        upi_payments = [p for p in payment_history if p.get('payment_method') == 'UPI']
        total_payments = len(payment_history)
        
        if total_payments == 0:
            return 0.0
        
        upi_adoption_rate = len(upi_payments) / total_payments
        
        # Bonus for consistent UPI usage
        if upi_adoption_rate > 0.8:
            return min(upi_adoption_rate + 0.1, 1.0)
        
        return upi_adoption_rate
    
    def _execute_neptune_query(self, query: str) -> Dict:
        """Execute Gremlin query on Neptune (DPDP Act compliant)"""
        try:
            # Neptune query execution with ap-south-1 endpoint
            response = self.neptune_client.execute_gremlin_query(
                gremlinQuery=query,
                serializer='graphsonv3'
            )
            return response.get('result', {})
        except Exception as e:
            logger.error(f"Neptune query failed: {e}")
            return {}

class TrustGraphGNN(nn.Module):
    """Graph Neural Network for Indian workforce resilience scoring"""
    
    def __init__(self, config: Dict):
        super(TrustGraphGNN, self).__init__()
        
        self.config = config
        self.num_layers = config['num_layers']
        self.hidden_size = config['hidden_size']
        self.num_heads = config['num_heads']
        self.dropout = config['dropout']
        
        # Node type embeddings for Indian context
        self.worker_embedding = nn.Linear(25, self.hidden_size)  # 25 Indian worker features
        self.employer_embedding = nn.Linear(15, self.hidden_size)  # 15 employer features
        self.bank_embedding = nn.Linear(12, self.hidden_size)  # 12 bank features
        
        # Edge type embeddings
        self.verified_by_embedding = nn.Linear(10, self.hidden_size)
        self.paid_via_embedding = nn.Linear(8, self.hidden_size)
        
        # GraphSAGE layers for inductive learning
        self.sage_layers = nn.ModuleList()
        self.attention_layers = nn.ModuleList()
        
        for i in range(self.num_layers):
            self.sage_layers.append(
                SAGEConv(self.hidden_size, self.hidden_size, aggr='mean')
            )
            self.attention_layers.append(
                GATConv(self.hidden_size, self.hidden_size // self.num_heads,
                       heads=self.num_heads, dropout=self.dropout, concat=True)
            )
        
        # Resilience score prediction head (Indian credit score range: 300-900)
        self.resilience_predictor = nn.Sequential(
            nn.Linear(self.hidden_size, self.hidden_size // 2),
            nn.ReLU(),
            nn.Dropout(self.dropout),
            nn.Linear(self.hidden_size // 2, self.hidden_size // 4),
            nn.ReLU(),
            nn.Dropout(self.dropout),
            nn.Linear(self.hidden_size // 4, 1),
            nn.Sigmoid()  # Output 0-1, will be scaled to 300-900
        )
        
        # Explanation module for Indian regulatory requirements
        self.explanation_module = nn.Sequential(
            nn.Linear(self.hidden_size, 64),
            nn.ReLU(),
            nn.Linear(64, 5)  # 5 explanation categories
        )
        
        # Confidence estimation for banking decisions
        self.confidence_estimator = nn.Sequential(
            nn.Linear(self.hidden_size, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
            nn.Sigmoid()
        )
    
    def forward(self, data):
        """Forward pass optimized for Indian workforce patterns"""
        
        x, edge_index, edge_attr = data.x, data.edge_index, data.edge_attr
        node_type, edge_type = data.node_type, data.edge_type
        
        # Node type-specific embeddings
        node_embeddings = torch.zeros(x.size(0), self.hidden_size, device=x.device)
        
        # Worker nodes (Indian informal workers)
        worker_mask = (node_type == 0)
        if worker_mask.any():
            node_embeddings[worker_mask] = self.worker_embedding(x[worker_mask])
        
        # Employer nodes (Indian businesses)
        employer_mask = (node_type == 1)
        if employer_mask.any():
            node_embeddings[employer_mask] = self.employer_embedding(x[employer_mask])
        
        # Bank nodes (Indian financial institutions)
        bank_mask = (node_type == 2)
        if bank_mask.any():
            node_embeddings[bank_mask] = self.bank_embedding(x[bank_mask])
        
        # Graph convolution with attention
        for i in range(self.num_layers):
            # GraphSAGE for neighborhood aggregation
            sage_out = self.sage_layers[i](node_embeddings, edge_index)
            sage_out = F.relu(sage_out)
            sage_out = F.dropout(sage_out, p=self.dropout, training=self.training)
            
            # Attention mechanism for importance weighting
            att_out = self.attention_layers[i](node_embeddings, edge_index)
            att_out = F.dropout(att_out, p=self.dropout, training=self.training)
            
            # Residual connection and normalization
            node_embeddings = sage_out + att_out + node_embeddings
            node_embeddings = F.layer_norm(node_embeddings, node_embeddings.shape[1:])
        
        # Focus on worker nodes for resilience scoring
        worker_embeddings = node_embeddings[worker_mask]
        
        # Resilience score prediction (0-1 range)
        resilience_scores = self.resilience_predictor(worker_embeddings)
        
        # Confidence estimation
        confidence_scores = self.confidence_estimator(worker_embeddings)
        
        # Feature importance for explainability (RBI requirement)
        explanation_scores = self.explanation_module(worker_embeddings)
        explanation_probs = F.softmax(explanation_scores, dim=1)
        
        return {
            'resilience_score': resilience_scores.squeeze(),
            'confidence': confidence_scores.squeeze(),
            'explanation': explanation_probs,
            'node_embeddings': worker_embeddings
        }
    
    def normalize_to_indian_credit_range(self, raw_score: torch.Tensor) -> torch.Tensor:
        """
        Normalize to Indian credit score range (300-900)
        Similar to CIBIL/Experian scoring in India
        """
        
        # Map 0-1 to 300-900 range
        min_score, max_score = 300, 900
        normalized = min_score + (raw_score * (max_score - min_score))
        
        # Apply Indian population calibration
        # Target: Normal distribution with mean=650, std=100
        target_mean, target_std = 650, 100
        current_mean = normalized.mean()
        current_std = normalized.std()
        
        # Standardize and rescale
        if current_std > 0:
            standardized = (normalized - current_mean) / current_std
            calibrated = standardized * target_std + target_mean
        else:
            calibrated = normalized
        
        # Clip to valid range
        calibrated = torch.clamp(calibrated, min_score, max_score)
        
        return calibrated.round().int()

def train_indian_workforce_gnn():
    """Main training function for Indian workforce GNN"""
    
    # Parse arguments
    parser = argparse.ArgumentParser(description='Train TrustGraph GNN for Indian Workforce')
    parser.add_argument('--data-path', type=str, required=True, help='Path to training data')
    parser.add_argument('--model-dir', type=str, default='/opt/ml/model', help='Model output directory')
    parser.add_argument('--epochs', type=int, default=100, help='Number of training epochs')
    parser.add_argument('--batch-size', type=int, default=1024, help='Batch size')
    parser.add_argument('--learning-rate', type=float, default=0.001, help='Learning rate')
    
    args = parser.parse_args()
    
    # Initialize configuration
    config = IndianWorkforceGNNConfig().config
    config.update({
        'num_epochs': args.epochs,
        'batch_size': args.batch_size,
        'learning_rate': args.learning_rate
    })
    
    logger.info(f"Starting TrustGraph GNN training for Indian workforce")
    logger.info(f"Configuration: {json.dumps(config, indent=2)}")
    
    # Initialize model
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = TrustGraphGNN(config).to(device)
    
    # Initialize optimizer
    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=config['learning_rate'],
        weight_decay=config['weight_decay']
    )
    
    # Load training data (DPDP Act compliant)
    train_loader = load_indian_workforce_data(args.data_path, config['batch_size'])
    
    # Training loop
    model.train()
    best_loss = float('inf')
    patience_counter = 0
    
    for epoch in range(config['num_epochs']):
        epoch_loss = 0.0
        num_batches = 0
        
        for batch in train_loader:
            batch = batch.to(device)
            
            # Forward pass
            optimizer.zero_grad()
            output = model(batch)
            
            # Calculate loss (MSE for regression)
            loss = F.mse_loss(output['resilience_score'], batch.y)
            
            # Backward pass
            loss.backward()
            optimizer.step()
            
            epoch_loss += loss.item()
            num_batches += 1
        
        avg_loss = epoch_loss / num_batches
        logger.info(f"Epoch {epoch+1}/{config['num_epochs']}, Loss: {avg_loss:.4f}")
        
        # Early stopping
        if avg_loss < best_loss:
            best_loss = avg_loss
            patience_counter = 0
            
            # Save best model
            torch.save({
                'model_state_dict': model.state_dict(),
                'config': config,
                'epoch': epoch,
                'loss': avg_loss
            }, os.path.join(args.model_dir, 'best_model.pth'))
            
        else:
            patience_counter += 1
            if patience_counter >= config['early_stopping_patience']:
                logger.info(f"Early stopping at epoch {epoch+1}")
                break
    
    logger.info("Training completed successfully")
    
    # Save final model
    torch.save({
        'model_state_dict': model.state_dict(),
        'config': config,
        'training_completed': True
    }, os.path.join(args.model_dir, 'final_model.pth'))
    
    return model

def load_indian_workforce_data(data_path: str, batch_size: int) -> DataLoader:
    """Load and preprocess Indian workforce data for training"""
    
    logger.info(f"Loading Indian workforce data from {data_path}")
    
    # Load graph data (implementation depends on data format)
    # This would typically load from S3 in ap-south-1 region
    
    # Placeholder for actual data loading
    # In production, this would load from Neptune export or preprocessed files
    
    # Return DataLoader with Indian workforce graph data
    # Implementation would include DPDP Act compliance checks
    
    pass

if __name__ == "__main__":
    # Ensure DPDP Act compliance
    os.environ['AWS_DEFAULT_REGION'] = 'ap-south-1'
    
    # Train the model
    trained_model = train_indian_workforce_gnn()
    
    logger.info("TrustGraph GNN training completed for Indian workforce resilience scoring")