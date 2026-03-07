"""SQLite database for local development"""

import sqlite3
import json
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any, List
import os

class Database:
    def __init__(self, db_path: str = "trustgraph.db"):
        self.db_path = db_path
        self.init_db()
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_db(self):
        """Initialize database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                phone TEXT UNIQUE NOT NULL,
                aadhaar_hash TEXT NOT NULL,
                aadhaar_verified BOOLEAN DEFAULT 0,
                name TEXT,
                email TEXT,
                date_of_birth TEXT,
                gender TEXT,
                address TEXT,
                city TEXT,
                state TEXT,
                pincode TEXT,
                role TEXT DEFAULT 'worker',
                preferred_language TEXT DEFAULT 'hi',
                profile_photo TEXT,
                kyc_status TEXT DEFAULT 'pending',
                account_status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                verified BOOLEAN DEFAULT 0
            )
        """)
        
        # Sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                token TEXT NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # OTP table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS otp_codes (
                phone TEXT PRIMARY KEY,
                otp TEXT NOT NULL,
                aadhaar_hash TEXT NOT NULL,
                attempts INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL
            )
        """)
        
        # Credentials table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS credentials (
                credential_id TEXT PRIMARY KEY,
                worker_id TEXT NOT NULL,
                employer_id TEXT,
                work_type TEXT NOT NULL,
                duration INTEGER,
                amount REAL,
                rating REAL,
                status TEXT DEFAULT 'active',
                blockchain_hash TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (worker_id) REFERENCES users(user_id)
            )
        """)
        
        # Transactions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id TEXT PRIMARY KEY,
                worker_id TEXT NOT NULL,
                employer_id TEXT,
                amount REAL NOT NULL,
                payment_method TEXT DEFAULT 'UPI',
                status TEXT DEFAULT 'pending',
                upi_ref TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (worker_id) REFERENCES users(user_id)
            )
        """)
        
        # Trust scores table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trust_scores (
                score_id INTEGER PRIMARY KEY AUTOINCREMENT,
                worker_id TEXT NOT NULL,
                score INTEGER NOT NULL,
                confidence REAL,
                factors TEXT,
                calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (worker_id) REFERENCES users(user_id)
            )
        """)
        
        # Verifiable Credentials table (W3C standard)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS verifiable_credentials (
                credential_id TEXT PRIMARY KEY,
                worker_id TEXT NOT NULL,
                issuer_id TEXT NOT NULL,
                credential_type TEXT NOT NULL,
                credential_data TEXT NOT NULL,
                proof TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                blockchain_hash TEXT,
                FOREIGN KEY (worker_id) REFERENCES users(user_id)
            )
        """)
        
        # Jobs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                employer_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                work_type TEXT NOT NULL,
                location TEXT,
                latitude REAL,
                longitude REAL,
                payment_amount REAL NOT NULL,
                payment_type TEXT DEFAULT 'milestone',
                required_skills TEXT,
                status TEXT DEFAULT 'open',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                deadline TIMESTAMP,
                FOREIGN KEY (employer_id) REFERENCES users(user_id)
            )
        """)
        
        # Work Records table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS work_records (
                work_id TEXT PRIMARY KEY,
                job_id TEXT NOT NULL,
                worker_id TEXT NOT NULL,
                employer_id TEXT NOT NULL,
                status TEXT DEFAULT 'in_progress',
                start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_date TIMESTAMP,
                total_hours REAL,
                location TEXT,
                latitude REAL,
                longitude REAL,
                blockchain_hash TEXT,
                FOREIGN KEY (job_id) REFERENCES jobs(job_id),
                FOREIGN KEY (worker_id) REFERENCES users(user_id),
                FOREIGN KEY (employer_id) REFERENCES users(user_id)
            )
        """)
        
        # Milestones table (for milestone-based payments)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS milestones (
                milestone_id TEXT PRIMARY KEY,
                work_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                amount REAL NOT NULL,
                status TEXT DEFAULT 'pending',
                proof_required BOOLEAN DEFAULT 1,
                proof_submitted BOOLEAN DEFAULT 0,
                verified BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                verified_at TIMESTAMP,
                payment_ref TEXT,
                FOREIGN KEY (work_id) REFERENCES work_records(work_id)
            )
        """)
        
        # Documents table (work proof, certificates, etc.)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                document_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                work_id TEXT,
                milestone_id TEXT,
                document_type TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_name TEXT NOT NULL,
                file_size INTEGER,
                mime_type TEXT,
                latitude REAL,
                longitude REAL,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                verified BOOLEAN DEFAULT 0,
                blockchain_hash TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (work_id) REFERENCES work_records(work_id),
                FOREIGN KEY (milestone_id) REFERENCES milestones(milestone_id)
            )
        """)
        
        # Ratings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ratings (
                rating_id TEXT PRIMARY KEY,
                work_id TEXT NOT NULL,
                rater_id TEXT NOT NULL,
                ratee_id TEXT NOT NULL,
                rating REAL NOT NULL,
                review TEXT,
                rating_type TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (work_id) REFERENCES work_records(work_id),
                FOREIGN KEY (rater_id) REFERENCES users(user_id),
                FOREIGN KEY (ratee_id) REFERENCES users(user_id)
            )
        """)
        
        # Blockchain Records table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS blockchain_records (
                record_id TEXT PRIMARY KEY,
                record_type TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                transaction_hash TEXT NOT NULL,
                block_number INTEGER,
                data_hash TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                verified BOOLEAN DEFAULT 1
            )
        """)
        
        # Skills table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS skills (
                skill_id TEXT PRIMARY KEY,
                worker_id TEXT NOT NULL,
                skill_name TEXT NOT NULL,
                proficiency_level TEXT DEFAULT 'beginner',
                verified BOOLEAN DEFAULT 0,
                endorsements INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (worker_id) REFERENCES users(user_id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    # User operations
    def create_user(self, user_id: str, phone: str, aadhaar_hash: str, 
                   name: str = None, role: str = 'worker', **kwargs) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO users (
                    user_id, phone, aadhaar_hash, name, role, 
                    email, date_of_birth, gender, address, city, state, pincode,
                    preferred_language, kyc_status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id, phone, aadhaar_hash, name, role,
                kwargs.get('email'), kwargs.get('date_of_birth'), 
                kwargs.get('gender'), kwargs.get('address'),
                kwargs.get('city'), kwargs.get('state'), kwargs.get('pincode'),
                kwargs.get('preferred_language', 'hi'), 
                kwargs.get('kyc_status', 'pending')
            ))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()
    
    def update_user(self, user_id: str, **kwargs) -> bool:
        """Update user profile"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Build dynamic update query
            fields = []
            values = []
            for key, value in kwargs.items():
                if value is not None:
                    fields.append(f"{key} = ?")
                    values.append(value)
            
            if not fields:
                return False
            
            fields.append("updated_at = CURRENT_TIMESTAMP")
            values.append(user_id)
            
            query = f"UPDATE users SET {', '.join(fields)} WHERE user_id = ?"
            cursor.execute(query, values)
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    def update_last_login(self, user_id: str):
        """Update last login timestamp"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE users SET last_login = CURRENT_TIMESTAMP 
            WHERE user_id = ?
        """, (user_id,))
        
        conn.commit()
        conn.close()
    
    def verify_aadhaar(self, user_id: str) -> bool:
        """Mark Aadhaar as verified"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE users SET aadhaar_verified = 1, kyc_status = 'verified'
            WHERE user_id = ?
        """, (user_id,))
        
        conn.commit()
        conn.close()
        return True
    
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def get_user_by_phone(self, phone: str) -> Optional[Dict[str, Any]]:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE phone = ?", (phone,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    # OTP operations
    def save_otp(self, phone: str, otp: str, expires_at: str, aadhaar_hash: str = None):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if aadhaar_hash is None:
            aadhaar_hash = hashlib.sha256(phone.encode()).hexdigest()
        
        cursor.execute("""
            INSERT OR REPLACE INTO otp_codes (phone, otp, aadhaar_hash, attempts, expires_at)
            VALUES (?, ?, ?, 0, ?)
        """, (phone, otp, aadhaar_hash, expires_at))
        
        conn.commit()
        conn.close()
    
    def verify_otp(self, phone: str, otp: str) -> Optional[str]:
        """Verify OTP and return aadhaar_hash if valid"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT otp, aadhaar_hash, attempts, expires_at FROM otp_codes 
            WHERE phone = ?
        """, (phone,))
        
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return None
        
        stored_otp, aadhaar_hash, attempts, expires_at = row
        
        # Check expiry (use UTC time for comparison)
        if datetime.utcnow().isoformat() > expires_at:
            conn.close()
            return None
        
        # Check attempts
        if attempts >= 3:
            conn.close()
            return None
        
        # Verify OTP
        if stored_otp == otp:
            cursor.execute("DELETE FROM otp_codes WHERE phone = ?", (phone,))
            conn.commit()
            conn.close()
            return aadhaar_hash
        else:
            cursor.execute("""
                UPDATE otp_codes SET attempts = attempts + 1 
                WHERE phone = ?
            """, (phone,))
            conn.commit()
            conn.close()
            return None
    
    # Session operations
    def create_session(self, session_id: str, user_id: str, 
                      token: str, expires_at: str):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO sessions (session_id, user_id, token, expires_at)
            VALUES (?, ?, ?, ?)
        """, (session_id, user_id, token, expires_at))
        
        conn.commit()
        conn.close()
    
    # Credential operations
    def create_credential(self, credential_id: str, worker_id: str,
                         work_type: str, **kwargs) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO credentials 
                (credential_id, worker_id, employer_id, work_type, 
                 duration, amount, rating, blockchain_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                credential_id, worker_id, kwargs.get('employer_id'),
                work_type, kwargs.get('duration'), kwargs.get('amount'),
                kwargs.get('rating'), kwargs.get('blockchain_hash')
            ))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error creating credential: {e}")
            return False
        finally:
            conn.close()
    
    def get_worker_credentials(self, worker_id: str) -> List[Dict[str, Any]]:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM credentials 
            WHERE worker_id = ? 
            ORDER BY created_at DESC
        """, (worker_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    # Transaction operations
    def create_transaction(self, transaction_id: str, worker_id: str,
                          amount: float, **kwargs) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO transactions 
                (transaction_id, worker_id, employer_id, amount, 
                 payment_method, status, upi_ref)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                transaction_id, worker_id, kwargs.get('employer_id'),
                amount, kwargs.get('payment_method', 'UPI'),
                kwargs.get('status', 'pending'), kwargs.get('upi_ref')
            ))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error creating transaction: {e}")
            return False
        finally:
            conn.close()
    
    def get_worker_transactions(self, worker_id: str) -> List[Dict[str, Any]]:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM transactions 
            WHERE worker_id = ? 
            ORDER BY created_at DESC
        """, (worker_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    # Trust score operations
    def save_trust_score(self, worker_id: str, score: int, 
                        confidence: float, factors: Dict[str, Any]):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO trust_scores (worker_id, score, confidence, factors)
            VALUES (?, ?, ?, ?)
        """, (worker_id, score, confidence, json.dumps(factors)))
        
        conn.commit()
        conn.close()
    
    def get_latest_trust_score(self, worker_id: str) -> Optional[Dict[str, Any]]:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM trust_scores 
            WHERE worker_id = ? 
            ORDER BY calculated_at DESC 
            LIMIT 1
        """, (worker_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            result = dict(row)
            result['factors'] = json.loads(result['factors'])
            return result
        return None
    
    # Verifiable Credentials operations
    def create_credential_vc(self, credential_id: str, worker_id: str, issuer_id: str,
                            credential_type: str, credential_data: Dict, proof: Dict) -> bool:
        """Create W3C Verifiable Credential"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO verifiable_credentials 
                (credential_id, worker_id, issuer_id, credential_type, 
                 credential_data, proof, blockchain_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                credential_id, worker_id, issuer_id, credential_type,
                json.dumps(credential_data), json.dumps(proof),
                hashlib.sha256(json.dumps(credential_data).encode()).hexdigest()
            ))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error creating VC: {e}")
            return False
        finally:
            conn.close()
    
    def get_worker_credentials_vc(self, worker_id: str) -> List[Dict[str, Any]]:
        """Get all verifiable credentials for a worker"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM verifiable_credentials 
            WHERE worker_id = ? AND status = 'active'
            ORDER BY issued_at DESC
        """, (worker_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        credentials = []
        for row in rows:
            cred = dict(row)
            cred['credential_data'] = json.loads(cred['credential_data'])
            cred['proof'] = json.loads(cred['proof'])
            credentials.append(cred)
        
        return credentials
    
    # Jobs operations
    def create_job(self, job_id: str, employer_id: str, title: str, 
                   work_type: str, payment_amount: float, **kwargs) -> bool:
        """Create a new job posting"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO jobs 
                (job_id, employer_id, title, description, work_type, 
                 location, latitude, longitude, payment_amount, payment_type,
                 required_skills, deadline)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job_id, employer_id, title, kwargs.get('description'),
                work_type, kwargs.get('location'), kwargs.get('latitude'),
                kwargs.get('longitude'), payment_amount, 
                kwargs.get('payment_type', 'milestone'),
                json.dumps(kwargs.get('required_skills', [])),
                kwargs.get('deadline')
            ))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error creating job: {e}")
            return False
        finally:
            conn.close()

# Global database instance
db = Database()
