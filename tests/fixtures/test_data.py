"""
Test fixtures and sample documents for production testing
"""

SAMPLE_DOCUMENTS = {
    "healthcare_policy": """
# Healthcare Data Privacy Policy

## Overview
This document outlines our comprehensive healthcare data privacy and security policy.

## Data Protection
- All patient data is encrypted at rest and in transit
- Access is controlled through role-based permissions
- Regular security audits are conducted quarterly

## Compliance
We comply with HIPAA, GDPR, and local healthcare regulations.

## Contact
For privacy concerns: privacy@healthcare.com
Phone: +1-555-0100
""",
    
    "patient_onboarding": """
# Patient Onboarding Guide

## Registration Process
1. Complete registration form
2. Provide identification documents
3. Sign consent forms
4. Schedule initial consultation

## Required Documents
- Government-issued ID
- Insurance card
- Medical history forms
- Emergency contact information

## First Appointment
Your first appointment will include:
- Health assessment
- Vital signs check
- Treatment plan discussion
- Questions and answers

Contact: onboarding@hospital.com
""",
    
    "medication_guidelines": """
# Medication Administration Guidelines

## Dosage Instructions
- Take medication as prescribed
- Do not skip doses
- Complete full course of treatment

## Side Effects
Common side effects may include:
- Nausea
- Dizziness
- Fatigue

## Emergency Contacts
For urgent concerns: emergency@pharmacy.com
24/7 Hotline: +1-555-0911

## Storage
Store in cool, dry place away from direct sunlight.
""",
    
    "billing_procedures": """
# Billing and Payment Procedures

## Payment Methods
We accept:
- Credit/Debit cards
- Insurance
- Cash
- Payment plans

## Billing Cycle
Bills are generated monthly and due within 30 days.

## Insurance Claims
We submit claims directly to your insurance provider.
Processing typically takes 14-21 business days.

## Questions
Billing department: billing@hospital.com
Phone: +1-555-0200
Hours: Mon-Fri 9 AM - 5 PM
""",
    
    "emergency_protocols": """
# Emergency Response Protocols

## Code Blue - Cardiac Arrest
1. Call emergency response team
2. Start CPR immediately
3. Prepare defibrillator
4. Document timing and actions

## Code Red - Fire
1. Activate fire alarm
2. Evacuate patients safely
3. Close fire doors
4. Call fire department: 911

## Code Yellow - Missing Patient
1. Check last known location
2. Alert security
3. Search systematically
4. Notify family if not found within 30 minutes

## Emergency Contacts
Security: ext. 5555
Nursing Supervisor: ext. 5556
""",
}

SAMPLE_QUERIES = {
    "healthcare_policy": [
        "What is the data encryption policy?",
        "How is patient data protected?",
        "What compliance standards do you follow?",
        "What is the privacy contact information?",
    ],
    "patient_onboarding": [
        "What documents do I need for registration?",
        "What happens during the first appointment?",
        "How do I complete the onboarding process?",
        "What is the onboarding contact email?",
    ],
    "medication_guidelines": [
        "What are common side effects?",
        "How should I store my medication?",
        "What is the emergency contact number?",
        "What are the dosage instructions?",
    ],
    "billing_procedures": [
        "What payment methods are accepted?",
        "When are bills due?",
        "How long does insurance processing take?",
        "What is the billing department contact?",
    ],
    "emergency_protocols": [
        "What is Code Blue protocol?",
        "What should I do in case of fire?",
        "What is the security extension number?",
        "How do I report a missing patient?",
    ],
}

EXPECTED_KEYWORDS = {
    "healthcare_policy": {
        "What is the data encryption policy?": ["encrypted", "data", "rest", "transit"],
        "What compliance standards do you follow?": ["HIPAA", "GDPR", "compliance"],
    },
    "patient_onboarding": {
        "What documents do I need for registration?": ["ID", "insurance", "medical history"],
        "What happens during the first appointment?": ["health assessment", "vital signs"],
    },
    "medication_guidelines": {
        "What are common side effects?": ["nausea", "dizziness", "fatigue"],
        "What is the emergency contact number?": ["555-0911", "emergency"],
    },
    "billing_procedures": {
        "What payment methods are accepted?": ["credit", "debit", "insurance", "cash"],
        "When are bills due?": ["30 days", "monthly"],
    },
    "emergency_protocols": {
        "What is Code Blue protocol?": ["cardiac", "CPR", "defibrillator"],
        "What is the security extension number?": ["5555", "security"],
    },
}
