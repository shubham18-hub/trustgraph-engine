/*
TrustGraph Trust Ledger Chaincode
Hyperledger Fabric chaincode for minting W3C Verifiable Credentials
Integrates with AWS KMS for cryptographic signing
*/

package main

import (
	"crypto/sha256"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"log"
	"strconv"
	"time"

	"github.com/hyperledger/fabric-contract-api-go/contractapi"
	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/aws/session"
	"github.com/aws/aws-sdk-go/service/kms"
)

// TrustLedgerContract defines the smart contract for TrustGraph credentials
type TrustLedgerContract struct {
	contractapi.Contract
}

// VerifiableCredential represents a W3C Verifiable Credential
type VerifiableCredential struct {
	Context           []string                 `json:"@context"`
	ID                string                   `json:"id"`
	Type              []string                 `json:"type"`
	Issuer            CredentialIssuer         `json:"issuer"`
	IssuanceDate      string                   `json:"issuanceDate"`
	ExpirationDate    string                   `json:"expirationDate,omitempty"`
	CredentialSubject CredentialSubject        `json:"credentialSubject"`
	Proof             CredentialProof          `json:"proof"`
	Status            string                   `json:"status"`
	CreatedAt         string                   `json:"createdAt"`
	UpdatedAt         string                   `json:"updatedAt"`
}

// CredentialIssuer represents the issuer of the credential
type CredentialIssuer struct {
	ID   string `json:"id"`
	Name string `json:"name"`
	Type string `json:"type"`
}

// CredentialSubject represents the subject of the credential
type CredentialSubject struct {
	ID          string      `json:"id"`
	WorkDetails WorkDetails `json:"workDetails"`
}

// WorkDetails contains the work-related information
type WorkDetails struct {
	JobType        string      `json:"jobType"`
	SkillLevel     string      `json:"skillLevel"`
	Duration       string      `json:"duration"`
	Location       Location    `json:"location"`
	Compensation   Compensation `json:"compensation"`
	Performance    Performance `json:"performance"`
	ProjectID      string      `json:"projectId"`
	MilestoneID    string      `json:"milestoneId"`
	Evidence       []Evidence  `json:"evidence"`
}

// Location represents geographical location
type Location struct {
	Address     string    `json:"address"`
	Coordinates []float64 `json:"coordinates"`
	PinCode     string    `json:"pinCode"`
}

// Compensation represents payment information
type Compensation struct {
	Amount        int    `json:"amount"`
	Currency      string `json:"currency"`
	PaymentMethod string `json:"paymentMethod"`
	TransactionID string `json:"transactionId"`
}

// Performance represents work performance metrics
type Performance struct {
	Rating           float64 `json:"rating"`
	CompletionRate   int     `json:"completionRate"`
	QualityScore     int     `json:"qualityScore"`
	PunctualityScore int     `json:"punctualityScore"`
	BonusEarned      int     `json:"bonusEarned"`
}

// Evidence represents proof of work completion
type Evidence struct {
	Type        string `json:"type"`
	URL         string `json:"url"`
	Hash        string `json:"hash"`
	Timestamp   string `json:"timestamp"`
	Description string `json:"description"`
}

// CredentialProof represents the cryptographic proof
type CredentialProof struct {
	Type               string `json:"type"`
	Created            string `json:"created"`
	VerificationMethod string `json:"verificationMethod"`
	ProofPurpose       string `json:"proofPurpose"`
	JWS                string `json:"jws"`
	KMSKeyID           string `json:"kmsKeyId"`
}

// MilestoneVerification represents a milestone verification request
type MilestoneVerification struct {
	WorkerID     string      `json:"workerId"`
	EmployerID   string      `json:"employerId"`
	ProjectID    string      `json:"projectId"`
	MilestoneID  string      `json:"milestoneId"`
	WorkDetails  WorkDetails `json:"workDetails"`
	VerifiedAt   string      `json:"verifiedAt"`
	VerifierSig  string      `json:"verifierSignature"`
}

// CredentialRegistry maintains credential metadata
type CredentialRegistry struct {
	CredentialID   string `json:"credentialId"`
	WorkerID       string `json:"workerId"`
	EmployerID     string `json:"employerId"`
	Status         string `json:"status"`
	IssuanceDate   string `json:"issuanceDate"`
	ExpirationDate string `json:"expirationDate"`
	RevocationDate string `json:"revocationDate,omitempty"`
	TxID           string `json:"txId"`
}

// TrustScore represents aggregated trust metrics
type TrustScore struct {
	WorkerID              string  `json:"workerId"`
	Score                 int     `json:"score"`
	CredentialCount       int     `json:"credentialCount"`
	AverageRating         float64 `json:"averageRating"`
	TotalEarnings         int     `json:"totalEarnings"`
	CompletionRate        float64 `json:"completionRate"`
	LastUpdated           string  `json:"lastUpdated"`
	SkillDiversityScore   int     `json:"skillDiversityScore"`
	PaymentConsistency    float64 `json:"paymentConsistency"`
}

// AWS KMS client for cryptographic operations
var kmsClient *kms.KMS

// Initialize AWS KMS client
func init() {
	sess, err := session.NewSession(&aws.Config{
		Region: aws.String("ap-south-1"), // Mumbai region for data residency
	})
	if err != nil {
		log.Fatalf("Failed to create AWS session: %v", err)
	}
	kmsClient = kms.New(sess)
}

// MintCredential creates a new W3C Verifiable Credential for verified milestone
func (t *TrustLedgerContract) MintCredential(ctx contractapi.TransactionContextInterface, verificationJSON string) (*VerifiableCredential, error) {
	// Parse milestone verification data
	var verification MilestoneVerification
	err := json.Unmarshal([]byte(verificationJSON), &verification)
	if err != nil {
		return nil, fmt.Errorf("failed to parse verification data: %v", err)
	}

	// Validate verification data
	if err := t.validateVerification(&verification); err != nil {
		return nil, fmt.Errorf("verification validation failed: %v", err)
	}

	// Generate credential ID
	credentialID := t.generateCredentialID(verification.WorkerID, verification.MilestoneID)

	// Check if credential already exists
	existingCred, err := t.GetCredential(ctx, credentialID)
	if err == nil && existingCred != nil {
		return nil, fmt.Errorf("credential already exists for milestone %s", verification.MilestoneID)
	}

	// Create W3C Verifiable Credential
	credential := &VerifiableCredential{
		Context: []string{
			"https://www.w3.org/2018/credentials/v1",
			"https://trustgraph.gov.in/contexts/work/v1",
		},
		ID:   fmt.Sprintf("https://trustgraph.gov.in/credentials/%s", credentialID),
		Type: []string{"VerifiableCredential", "WorkCredential"},
		Issuer: CredentialIssuer{
			ID:   fmt.Sprintf("did:india:employer:%s", verification.EmployerID),
			Name: "TrustGraph Employer",
			Type: "Organization",
		},
		IssuanceDate: time.Now().UTC().Format(time.RFC3339),
		CredentialSubject: CredentialSubject{
			ID:          fmt.Sprintf("did:india:worker:%s", verification.WorkerID),
			WorkDetails: verification.WorkDetails,
		},
		Status:    "active",
		CreatedAt: time.Now().UTC().Format(time.RFC3339),
		UpdatedAt: time.Now().UTC().Format(time.RFC3339),
	}

	// Set expiration date (1 year from issuance)
	expirationTime := time.Now().AddDate(1, 0, 0)
	credential.ExpirationDate = expirationTime.UTC().Format(time.RFC3339)

	// Generate cryptographic proof using AWS KMS
	proof, err := t.generateKMSProof(credential, verification.EmployerID)
	if err != nil {
		return nil, fmt.Errorf("failed to generate cryptographic proof: %v", err)
	}
	credential.Proof = *proof

	// Store credential on blockchain
	credentialJSON, err := json.Marshal(credential)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal credential: %v", err)
	}

	err = ctx.GetStub().PutState(credentialID, credentialJSON)
	if err != nil {
		return nil, fmt.Errorf("failed to store credential: %v", err)
	}

	// Update credential registry
	registry := &CredentialRegistry{
		CredentialID:   credentialID,
		WorkerID:       verification.WorkerID,
		EmployerID:     verification.EmployerID,
		Status:         "active",
		IssuanceDate:   credential.IssuanceDate,
		ExpirationDate: credential.ExpirationDate,
		TxID:           ctx.GetStub().GetTxID(),
	}

	registryJSON, err := json.Marshal(registry)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal registry entry: %v", err)
	}

	registryKey := fmt.Sprintf("registry_%s", credentialID)
	err = ctx.GetStub().PutState(registryKey, registryJSON)
	if err != nil {
		return nil, fmt.Errorf("failed to store registry entry: %v", err)
	}

	// Update worker's trust score
	err = t.updateTrustScore(ctx, verification.WorkerID, &verification.WorkDetails)
	if err != nil {
		// Log error but don't fail credential minting
		fmt.Printf("Warning: failed to update trust score for worker %s: %v", verification.WorkerID, err)
	}

	// Emit credential minted event
	eventPayload := map[string]interface{}{
		"credentialId": credentialID,
		"workerId":     verification.WorkerID,
		"employerId":   verification.EmployerID,
		"milestoneId":  verification.MilestoneID,
		"issuanceDate": credential.IssuanceDate,
	}
	eventJSON, _ := json.Marshal(eventPayload)
	err = ctx.GetStub().SetEvent("CredentialMinted", eventJSON)
	if err != nil {
		fmt.Printf("Warning: failed to emit credential minted event: %v", err)
	}

	return credential, nil
}

// GetCredential retrieves a credential by ID
func (t *TrustLedgerContract) GetCredential(ctx contractapi.TransactionContextInterface, credentialID string) (*VerifiableCredential, error) {
	credentialJSON, err := ctx.GetStub().GetState(credentialID)
	if err != nil {
		return nil, fmt.Errorf("failed to read credential: %v", err)
	}
	if credentialJSON == nil {
		return nil, fmt.Errorf("credential %s does not exist", credentialID)
	}

	var credential VerifiableCredential
	err = json.Unmarshal(credentialJSON, &credential)
	if err != nil {
		return nil, fmt.Errorf("failed to unmarshal credential: %v", err)
	}

	return &credential, nil
}

// GetWorkerCredentials retrieves all credentials for a worker
func (t *TrustLedgerContract) GetWorkerCredentials(ctx contractapi.TransactionContextInterface, workerID string) ([]*VerifiableCredential, error) {
	// Query credentials by worker ID using rich query
	queryString := fmt.Sprintf(`{
		"selector": {
			"credentialSubject.id": "did:india:worker:%s",
			"status": "active"
		}
	}`, workerID)

	resultsIterator, err := ctx.GetStub().GetQueryResult(queryString)
	if err != nil {
		return nil, fmt.Errorf("failed to query credentials: %v", err)
	}
	defer resultsIterator.Close()

	var credentials []*VerifiableCredential
	for resultsIterator.HasNext() {
		queryResponse, err := resultsIterator.Next()
		if err != nil {
			return nil, fmt.Errorf("failed to iterate query results: %v", err)
		}

		var credential VerifiableCredential
		err = json.Unmarshal(queryResponse.Value, &credential)
		if err != nil {
			continue // Skip invalid credentials
		}

		credentials = append(credentials, &credential)
	}

	return credentials, nil
}

// VerifyCredential verifies the cryptographic integrity of a credential
func (t *TrustLedgerContract) VerifyCredential(ctx contractapi.TransactionContextInterface, credentialID string) (bool, error) {
	credential, err := t.GetCredential(ctx, credentialID)
	if err != nil {
		return false, err
	}

	// Verify KMS signature
	isValid, err := t.verifyKMSSignature(credential)
	if err != nil {
		return false, fmt.Errorf("failed to verify KMS signature: %v", err)
	}

	// Check expiration
	if credential.ExpirationDate != "" {
		expirationTime, err := time.Parse(time.RFC3339, credential.ExpirationDate)
		if err != nil {
			return false, fmt.Errorf("invalid expiration date format: %v", err)
		}
		if time.Now().After(expirationTime) {
			return false, fmt.Errorf("credential has expired")
		}
	}

	// Check revocation status
	if credential.Status != "active" {
		return false, fmt.Errorf("credential is not active (status: %s)", credential.Status)
	}

	return isValid, nil
}

// RevokeCredential revokes a credential
func (t *TrustLedgerContract) RevokeCredential(ctx contractapi.TransactionContextInterface, credentialID string, reason string) error {
	credential, err := t.GetCredential(ctx, credentialID)
	if err != nil {
		return err
	}

	if credential.Status != "active" {
		return fmt.Errorf("credential is already revoked or inactive")
	}

	// Update credential status
	credential.Status = "revoked"
	credential.UpdatedAt = time.Now().UTC().Format(time.RFC3339)

	credentialJSON, err := json.Marshal(credential)
	if err != nil {
		return fmt.Errorf("failed to marshal updated credential: %v", err)
	}

	err = ctx.GetStub().PutState(credentialID, credentialJSON)
	if err != nil {
		return fmt.Errorf("failed to update credential: %v", err)
	}

	// Update registry
	registryKey := fmt.Sprintf("registry_%s", credentialID)
	registryJSON, err := ctx.GetStub().GetState(registryKey)
	if err == nil && registryJSON != nil {
		var registry CredentialRegistry
		json.Unmarshal(registryJSON, &registry)
		registry.Status = "revoked"
		registry.RevocationDate = time.Now().UTC().Format(time.RFC3339)
		
		updatedRegistryJSON, _ := json.Marshal(registry)
		ctx.GetStub().PutState(registryKey, updatedRegistryJSON)
	}

	// Emit revocation event
	eventPayload := map[string]interface{}{
		"credentialId":   credentialID,
		"reason":         reason,
		"revocationDate": credential.UpdatedAt,
	}
	eventJSON, _ := json.Marshal(eventPayload)
	ctx.GetStub().SetEvent("CredentialRevoked", eventJSON)

	return nil
}

// GetTrustScore retrieves the trust score for a worker
func (t *TrustLedgerContract) GetTrustScore(ctx contractapi.TransactionContextInterface, workerID string) (*TrustScore, error) {
	trustScoreKey := fmt.Sprintf("trustscore_%s", workerID)
	trustScoreJSON, err := ctx.GetStub().GetState(trustScoreKey)
	if err != nil {
		return nil, fmt.Errorf("failed to read trust score: %v", err)
	}
	if trustScoreJSON == nil {
		// Return default trust score for new workers
		return &TrustScore{
			WorkerID:              workerID,
			Score:                 500, // Default neutral score
			CredentialCount:       0,
			AverageRating:         0.0,
			TotalEarnings:         0,
			CompletionRate:        0.0,
			LastUpdated:           time.Now().UTC().Format(time.RFC3339),
			SkillDiversityScore:   0,
			PaymentConsistency:    0.0,
		}, nil
	}

	var trustScore TrustScore
	err = json.Unmarshal(trustScoreJSON, &trustScore)
	if err != nil {
		return nil, fmt.Errorf("failed to unmarshal trust score: %v", err)
	}

	return &trustScore, nil
}

// Helper function to validate milestone verification
func (t *TrustLedgerContract) validateVerification(verification *MilestoneVerification) error {
	if verification.WorkerID == "" {
		return fmt.Errorf("worker ID is required")
	}
	if verification.EmployerID == "" {
		return fmt.Errorf("employer ID is required")
	}
	if verification.MilestoneID == "" {
		return fmt.Errorf("milestone ID is required")
	}
	if verification.WorkDetails.JobType == "" {
		return fmt.Errorf("job type is required")
	}
	if verification.WorkDetails.Performance.Rating < 1 || verification.WorkDetails.Performance.Rating > 5 {
		return fmt.Errorf("rating must be between 1 and 5")
	}
	return nil
}

// Helper function to generate credential ID
func (t *TrustLedgerContract) generateCredentialID(workerID, milestoneID string) string {
	data := fmt.Sprintf("%s_%s_%d", workerID, milestoneID, time.Now().Unix())
	hash := sha256.Sum256([]byte(data))
	return fmt.Sprintf("cred_%x", hash[:16])
}

// Helper function to generate KMS-based cryptographic proof
func (t *TrustLedgerContract) generateKMSProof(credential *VerifiableCredential, employerID string) (*CredentialProof, error) {
	// Create canonical representation for signing
	canonicalData := t.createCanonicalCredential(credential)
	
	// Get KMS key ID for employer
	kmsKeyID := fmt.Sprintf("alias/trustgraph-employer-%s", employerID)
	
	// Sign with AWS KMS
	signInput := &kms.SignInput{
		KeyId:            aws.String(kmsKeyID),
		Message:          []byte(canonicalData),
		MessageType:      aws.String("RAW"),
		SigningAlgorithm: aws.String("ECDSA_SHA_256"),
	}
	
	signOutput, err := kmsClient.Sign(signInput)
	if err != nil {
		return nil, fmt.Errorf("KMS signing failed: %v", err)
	}
	
	// Encode signature as JWS
	jws := base64.URLEncoding.EncodeToString(signOutput.Signature)
	
	proof := &CredentialProof{
		Type:               "EcdsaSecp256k1Signature2019",
		Created:            time.Now().UTC().Format(time.RFC3339),
		VerificationMethod: fmt.Sprintf("did:india:employer:%s#key-1", employerID),
		ProofPurpose:       "assertionMethod",
		JWS:                jws,
		KMSKeyID:           kmsKeyID,
	}
	
	return proof, nil
}

// Helper function to verify KMS signature
func (t *TrustLedgerContract) verifyKMSSignature(credential *VerifiableCredential) (bool, error) {
	// Create canonical representation
	canonicalData := t.createCanonicalCredential(credential)
	
	// Decode JWS signature
	signature, err := base64.URLEncoding.DecodeString(credential.Proof.JWS)
	if err != nil {
		return false, fmt.Errorf("failed to decode JWS signature: %v", err)
	}
	
	// Verify with AWS KMS
	verifyInput := &kms.VerifyInput{
		KeyId:            aws.String(credential.Proof.KMSKeyID),
		Message:          []byte(canonicalData),
		MessageType:      aws.String("RAW"),
		Signature:        signature,
		SigningAlgorithm: aws.String("ECDSA_SHA_256"),
	}
	
	verifyOutput, err := kmsClient.Verify(verifyInput)
	if err != nil {
		return false, fmt.Errorf("KMS verification failed: %v", err)
	}
	
	return *verifyOutput.SignatureValid, nil
}

// Helper function to create canonical credential representation for signing
func (t *TrustLedgerContract) createCanonicalCredential(credential *VerifiableCredential) string {
	// Create a copy without the proof for signing
	credentialCopy := *credential
	credentialCopy.Proof = CredentialProof{}
	
	canonicalJSON, _ := json.Marshal(credentialCopy)
	return string(canonicalJSON)
}

// Helper function to update trust score
func (t *TrustLedgerContract) updateTrustScore(ctx contractapi.TransactionContextInterface, workerID string, workDetails *WorkDetails) error {
	trustScore, err := t.GetTrustScore(ctx, workerID)
	if err != nil {
		return err
	}
	
	// Update metrics
	trustScore.CredentialCount++
	trustScore.TotalEarnings += workDetails.Compensation.Amount
	
	// Calculate new average rating
	if trustScore.CredentialCount == 1 {
		trustScore.AverageRating = workDetails.Performance.Rating
	} else {
		trustScore.AverageRating = ((trustScore.AverageRating * float64(trustScore.CredentialCount-1)) + workDetails.Performance.Rating) / float64(trustScore.CredentialCount)
	}
	
	// Update completion rate (assuming 100% for verified milestones)
	trustScore.CompletionRate = float64(workDetails.Performance.CompletionRate) / 100.0
	
	// Calculate trust score (300-900 range)
	baseScore := 300
	ratingBonus := int(trustScore.AverageRating * 100)
	completionBonus := int(trustScore.CompletionRate * 100)
	experienceBonus := min(trustScore.CredentialCount*10, 200)
	
	trustScore.Score = baseScore + ratingBonus + completionBonus + experienceBonus
	if trustScore.Score > 900 {
		trustScore.Score = 900
	}
	
	trustScore.LastUpdated = time.Now().UTC().Format(time.RFC3339)
	
	// Store updated trust score
	trustScoreKey := fmt.Sprintf("trustscore_%s", workerID)
	trustScoreJSON, err := json.Marshal(trustScore)
	if err != nil {
		return fmt.Errorf("failed to marshal trust score: %v", err)
	}
	
	return ctx.GetStub().PutState(trustScoreKey, trustScoreJSON)
}

// Helper function for min calculation
func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}

// Main function to start the chaincode
func main() {
	trustLedgerContract := new(TrustLedgerContract)
	
	chaincode, err := contractapi.NewChaincode(trustLedgerContract)
	if err != nil {
		log.Panicf("Error creating TrustLedger chaincode: %v", err)
	}
	
	if err := chaincode.Start(); err != nil {
		log.Panicf("Error starting TrustLedger chaincode: %v", err)
	}
}