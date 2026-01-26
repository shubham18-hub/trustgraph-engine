# TrustGraph Engine - User Stories

## Primary Personas

### 1. Informal Worker (राम कुमार - Mason)
**Background**: 32-year-old construction worker from Noida with 10+ years experience, Hindi speaker, basic digital literacy.

#### Epic: Digital Identity & Credential Management
- **US-001**: As an informal worker, I want to create a digital identity using my Aadhaar, so that I can build a verifiable work history.
- **US-002**: As a worker, I want to log my completed work via voice commands in Hindi, so that I can easily record milestones without typing.
- **US-003**: As a worker, I want to upload photos of completed work with GPS location, so that employers can verify my work remotely.
- **US-004**: As a worker, I want to receive automatic payments when my work is verified, so that I don't have to chase employers for payment.

#### Epic: Trust Building & Credit Access
- **US-005**: As a worker, I want to check my trust score via voice command, so that I know my creditworthiness for loans.
- **US-006**: As a worker, I want to share my work credentials with banks, so that I can access formal credit for my family's needs.
- **US-007**: As a worker, I want to see my complete work history, so that I can showcase my experience to new employers.

### 2. Employer (सुरेश शर्मा - Construction Company Owner)
**Background**: 45-year-old contractor running ABC Construction, manages 25+ workers, needs reliable workforce.

#### Epic: Worker Management & Verification
- **US-008**: As an employer, I want to find reliable workers based on their trust scores, so that I can hire quality workforce for my projects.
- **US-009**: As an employer, I want to create milestones with automatic payment triggers, so that workers are incentivized to complete work on time.
- **US-010**: As an employer, I want to verify worker's completed work through photos and GPS, so that I can ensure quality before payment.
- **US-011**: As an employer, I want to rate workers after project completion, so that their reputation reflects actual performance.

#### Epic: Payment Automation
- **US-012**: As an employer, I want payments to be automatically disbursed when milestones are verified, so that I don't have to manually process each payment.
- **US-013**: As an employer, I want to set payment conditions based on work quality, so that I maintain standards while ensuring fair compensation.

### 3. Bank Officer (अनिल गुप्ता - SBI Branch Manager)
**Background**: Bank manager looking to expand financial inclusion, needs reliable credit assessment for informal workers.

#### Epic: Alternative Credit Assessment
- **US-014**: As a bank officer, I want to access worker trust scores with their consent, so that I can make informed lending decisions.
- **US-015**: As a bank officer, I want to see verified work history and payment consistency, so that I can assess creditworthiness beyond traditional metrics.
- **US-016**: As a bank officer, I want automated loan recommendations based on trust scores, so that I can efficiently process applications.

### 4. Government Official (प्रिया शर्मा - NITI Aayog)
**Background**: Policy maker implementing Digital ShramSetu initiative, focused on financial inclusion and worker empowerment.

#### Epic: Policy Implementation & Monitoring
- **US-017**: As a government official, I want to monitor adoption rates across states, so that I can measure the success of Digital ShramSetu.
- **US-018**: As a government official, I want to track financial inclusion metrics, so that I can report progress toward Viksit Bharat 2047 goals.
- **US-019**: As a government official, I want to ensure data privacy compliance, so that worker rights are protected under DPDP Act 2023.

## Cross-Cutting User Stories

### Voice-First Accessibility
- **US-020**: As a user with limited literacy, I want to interact with the system using voice commands in my local language, so that I can access all features without reading/writing.
- **US-021**: As a user in a noisy environment, I want the system to understand my voice commands accurately, so that I can use it on construction sites.

### Security & Privacy
- **US-022**: As a worker, I want full control over who can access my work credentials, so that my privacy is protected.
- **US-023**: As a user, I want my data to be stored securely in India, so that it complies with data residency requirements.

### Scalability & Performance
- **US-024**: As any user, I want the system to respond within 2 seconds for voice interactions, so that it feels natural and responsive.
- **US-025**: As the system, I need to handle 10M+ concurrent users during peak hours, so that it can scale to serve all informal workers in India.

## Acceptance Criteria Examples

### US-002: Voice-based Work Logging
**Given** I am a worker who has completed a milestone
**When** I say "मैंने अपना काम पूरा कर दिया है" (I have completed my work)
**Then** the system should:
- Transcribe my voice with >95% accuracy
- Identify the intent as "milestone completion"
- Prompt me to upload photo evidence
- Respond in Hindi with next steps
- Complete the interaction within 2 seconds

### US-004: Automatic Payment Processing
**Given** I have uploaded geotagged photo evidence of completed work
**When** the system verifies the photo location matches the milestone requirements
**And** the employer confirms the work quality
**Then** the system should:
- Automatically initiate UPI payment within 30 seconds
- Send SMS confirmation to my registered mobile number
- Update my work history with the completed milestone
- Mint a W3C Verifiable Credential on the blockchain

### US-014: Bank Credit Assessment
**Given** I am a bank officer reviewing a loan application from an informal worker
**When** the worker provides consent to share their trust score
**Then** I should be able to:
- View their normalized trust score (0-1000 range)
- See breakdown of score components (work history, payment consistency, etc.)
- Access verified work credentials with cryptographic proofs
- Get automated loan amount recommendations based on their profile

## User Journey Maps

### Worker Onboarding Journey
1. **Discovery**: Worker learns about TrustGraph through community outreach
2. **Registration**: Creates account using Aadhaar verification
3. **First Work Entry**: Logs first milestone using voice commands
4. **Skill Verification**: Gets skills endorsed by employer
5. **Trust Building**: Accumulates verified work history over time
6. **Credit Access**: Uses trust score to access formal banking services

### Employer Adoption Journey
1. **Problem Recognition**: Struggles with worker reliability and payment disputes
2. **System Trial**: Tests TrustGraph with a small project
3. **Milestone Setup**: Creates automated payment milestones
4. **Worker Verification**: Experiences improved work quality through verification system
5. **Scale Adoption**: Expands usage to all projects and workers

## Success Metrics by User Story

### Worker Success Metrics
- **Onboarding**: 80% completion rate within 10 minutes
- **Voice Interaction**: 95% accuracy for common commands
- **Payment Speed**: 95% of payments processed within 5 minutes
- **Trust Score Growth**: Average 5+ credentials within 6 months

### Employer Success Metrics
- **Work Quality**: 20% improvement in project completion rates
- **Payment Efficiency**: 90% reduction in payment processing time
- **Worker Retention**: 30% increase in repeat worker hiring

### Bank Success Metrics
- **Loan Approval**: 40% improvement in approval rates for informal workers
- **Default Rates**: 25% reduction compared to traditional assessment methods
- **Processing Time**: 50% faster loan processing with automated trust scores

### Government Success Metrics
- **Financial Inclusion**: 60% of users access formal credit within 12 months
- **Geographic Coverage**: All 28 states and 8 UTs by Year 2
- **Economic Impact**: 300% average income increase for participating workers

## Implementation Priority

### Phase 1 (MVP) - Core User Stories
- US-001, US-002, US-003, US-004: Basic worker workflow
- US-008, US-009, US-010: Essential employer features
- US-020: Voice-first accessibility

### Phase 2 (Scale) - Enhanced Features
- US-005, US-006, US-007: Trust scoring and credit access
- US-011, US-012, US-013: Advanced employer tools
- US-014, US-015, US-016: Bank integration

### Phase 3 (Nationwide) - Full Platform
- US-017, US-018, US-019: Government monitoring and compliance
- US-021 through US-025: Performance and scalability features

This user story framework ensures that the TrustGraph Engine addresses real needs of all stakeholders while maintaining focus on the core mission of empowering India's informal workforce.