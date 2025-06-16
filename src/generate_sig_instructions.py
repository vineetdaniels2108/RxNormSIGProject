import pandas as pd
import re
import json

def generate_sig_templates(row):
    """
    Generate intelligent SIG (Signa/Dosage Instructions) templates based on medication properties.
    
    Args:
        row: Pandas series containing medication data
    
    Returns:
        List of suggested SIG templates
    """
    drug_name = str(row.get('drug_name', '')).lower()
    dose_form = str(row.get('dose_form', '')).lower()
    available_strength = str(row.get('available_strength', ''))
    term_type = str(row.get('term_type', ''))
    searchable_text = str(row.get('searchable_text', '')).lower()
    
    # Initialize SIG templates list
    sigs = []
    
    # Extract route information from drug name or searchable text
    route_keywords = {
        'oral': ['oral', 'mouth', 'po'],
        'topical': ['topical', 'skin'],
        'ophthalmic': ['ophthalmic', 'eye', 'ocular'],
        'otic': ['otic', 'ear', 'aural'],
        'nasal': ['nasal', 'nose', 'intranasal'],
        'rectal': ['rectal', 'rectally', 'pr'],
        'vaginal': ['vaginal', 'intravaginal'],
        'injection': ['injection', 'injectable', 'iv', 'im', 'subcutaneous'],
        'inhalation': ['inhalation', 'inhaled', 'respiratory']
    }
    
    detected_route = None
    for route, keywords in route_keywords.items():
        if any(keyword in searchable_text for keyword in keywords):
            detected_route = route
            break
    
    # TABLETS AND CAPSULES
    if any(form in dose_form for form in ['tab', 'cap', 'pill']):
        if 'extended' in drug_name or 'xl' in drug_name or 'er' in drug_name:
            sigs.extend([
                "Take 1 tablet by mouth once daily",
                "Take 1 tablet by mouth once daily with food",
                "Take 1 tablet by mouth at bedtime"
            ])
        else:
            sigs.extend([
                "Take 1 tablet by mouth once daily",
                "Take 1 tablet by mouth twice daily with meals",
                "Take 2 tablets by mouth once daily",
                "Take 1 tablet by mouth at bedtime",
                "Take 1 tablet by mouth every 12 hours",
                "Take 1 tablet by mouth three times daily with meals"
            ])
        
        # Add strength-specific instructions if available
        if available_strength and any(unit in available_strength.lower() for unit in ['mg', 'mcg', 'g']):
            sigs.append(f"Take 1 tablet ({available_strength}) by mouth as directed")
    
    # TOPICAL PREPARATIONS (Creams, Ointments, Gels, Lotions)
    elif any(form in dose_form for form in ['cream', 'ointment', 'gel', 'lotion', 'foam']):
        sigs.extend([
            "Apply a thin layer to affected area twice daily",
            "Apply to affected area once daily at bedtime",
            "Apply as needed for itching or rash",
            "Apply a small amount to affected area and rub in gently",
            "Apply twice daily and rub in until absorbed",
            "Apply to clean, dry skin as directed"
        ])
        
        # Specific instructions for different topical forms
        if 'ointment' in dose_form:
            sigs.append("Apply ointment sparingly to avoid occlusion")
        elif 'gel' in dose_form:
            sigs.append("Apply gel and allow to dry before covering")
    
    # SOLUTIONS AND LIQUIDS
    elif any(form in dose_form for form in ['sol', 'solution', 'liquid', 'syrup', 'suspension']):
        if detected_route == 'topical' or 'topical' in searchable_text:
            sigs.extend([
                "Apply solution to affected area twice daily",
                "Apply with cotton swab once daily",
                "Dab solution on affected area as needed",
                "Apply solution and allow to air dry"
            ])
        elif detected_route == 'oral' or 'oral' in searchable_text:
            sigs.extend([
                "Take 5 mL by mouth once daily",
                "Take 10 mL by mouth twice daily with meals",
                "Take 15 mL by mouth at bedtime",
                "Take as directed by physician",
                "Shake well before use, take with food"
            ])
        else:
            # General solution instructions
            sigs.extend([
                "Use as directed by physician",
                "Apply to affected area as needed",
                "Take 5-10 mL as directed"
            ])
    
    # SPRAYS AND NASAL PREPARATIONS
    elif any(form in dose_form for form in ['spray', 'nasal']) or detected_route == 'nasal':
        sigs.extend([
            "Use 2 sprays in each nostril once daily",
            "Use 1 spray in each nostril twice daily",
            "Prime pump before first use, spray once in each nostril",
            "Use 2 sprays in each nostril every 12 hours",
            "Spray once in each nostril as needed for congestion"
        ])
    
    # INHALERS AND RESPIRATORY
    elif any(form in dose_form for form in ['inhaler', 'aerosol']) or detected_route == 'inhalation':
        sigs.extend([
            "Inhale 2 puffs by mouth every 4 hours as needed",
            "Inhale 1 puff by mouth twice daily",
            "Inhale 2 puffs by mouth every 6 hours",
            "Use as rescue inhaler for shortness of breath",
            "Prime inhaler before first use, inhale deeply and hold"
        ])
    
    # SUPPOSITORIES
    elif 'suppository' in dose_form or detected_route == 'rectal':
        sigs.extend([
            "Insert 1 suppository rectally at bedtime",
            "Insert rectally once daily as needed",
            "Insert 1 suppository rectally every 8 hours as needed",
            "Moisten with water before insertion"
        ])
    
    # EYE DROPS AND OPHTHALMIC PREPARATIONS
    elif any(form in dose_form for form in ['drop']) or detected_route == 'ophthalmic':
        sigs.extend([
            "Instill 1 drop in affected eye(s) twice daily",
            "Instill 2 drops in affected eye(s) every 4 hours",
            "Place 1 drop in each eye once daily",
            "Instill 1 drop in affected eye(s) at bedtime",
            "Wash hands before use, do not touch tip to eye"
        ])
    
    # EAR DROPS AND OTIC PREPARATIONS  
    elif detected_route == 'otic':
        sigs.extend([
            "Instill 2 drops in affected ear three times daily",
            "Place 3-4 drops in affected ear twice daily",
            "Warm to room temperature before use, instill as directed",
            "Instill drops and keep head tilted for 2 minutes"
        ])
    
    # PATCHES AND TRANSDERMAL
    elif any(form in dose_form for form in ['patch', 'transdermal']):
        sigs.extend([
            "Apply 1 patch to clean, dry skin once daily",
            "Apply patch to hairless area, rotate sites",
            "Replace patch every 24 hours",
            "Apply patch and wear for 12 hours, then remove"
        ])
    
    # INJECTIONS
    elif detected_route == 'injection' or any(form in dose_form for form in ['injection', 'vial']):
        sigs.extend([
            "Inject as directed by healthcare provider",
            "Administer by healthcare professional only",
            "Use under medical supervision",
            "Single use vial - discard after use"
        ])
    
    # SPECIAL CATEGORIES BASED ON DRUG NAME PATTERNS
    
    # Antibiotics (common patterns)
    if any(antibiotic in drug_name for antibiotic in ['amoxicillin', 'penicillin', 'azithromycin', 'ciprofloxacin', 'doxycycline']):
        sigs.extend([
            "Take until completely finished even if feeling better",
            "Take with plenty of water",
            "Take at evenly spaced intervals"
        ])
    
    # Pain medications
    if any(pain_med in drug_name for pain_med in ['ibuprofen', 'acetaminophen', 'aspirin', 'naproxen']):
        sigs.extend([
            "Take with food to prevent stomach upset",
            "Do not exceed maximum daily dose",
            "Take as needed for pain"
        ])
    
    # Heart medications
    if any(heart_med in drug_name for heart_med in ['metoprolol', 'lisinopril', 'amlodipine', 'atorvastatin']):
        sigs.extend([
            "Take at the same time each day",
            "Do not stop suddenly without consulting physician",
            "Monitor blood pressure regularly"
        ])
    
    # Diabetes medications
    if any(diabetes_med in drug_name for diabetes_med in ['metformin', 'insulin', 'glyburide', 'glipizide']):
        sigs.extend([
            "Take with meals to reduce stomach upset",
            "Monitor blood sugar as directed",
            "Take at the same time each day"
        ])
    
    # Birth control
    if 'estradiol' in drug_name or 'levonorgestrel' in drug_name or 'ethinyl' in drug_name:
        sigs.extend([
            "Take at the same time every day",
            "Take continuously as directed",
            "Do not skip doses"
        ])
    
    # If no specific SIGs generated, add generic ones
    if not sigs:
        sigs.extend([
            f"Use {row.get('drug_name', 'medication')} as directed by physician",
            "Follow dosing instructions provided by healthcare provider",
            "Use as prescribed"
        ])
    
    # Add general safety instructions based on medication type
    safety_instructions = []
    
    if term_type == 'BN':  # Brand name
        safety_instructions.append("Brand name medication - do not substitute without consulting physician")
    
    if any(controlled in drug_name for controlled in ['oxycodone', 'morphine', 'fentanyl', 'adderall', 'xanax']):
        safety_instructions.extend([
            "Controlled substance - take exactly as prescribed",
            "Do not share with others",
            "Store securely away from children"
        ])
    
    # Combine main SIGs with safety instructions
    all_sigs = sigs + safety_instructions
    
    # Remove duplicates while preserving order
    seen = set()
    unique_sigs = []
    for sig in all_sigs:
        if sig not in seen:
            unique_sigs.append(sig)
            seen.add(sig)
    
    return unique_sigs[:10]  # Limit to 10 most relevant SIGs

def add_sig_instructions_to_table():
    """
    Add SIG instructions to the medication table and save the enhanced version.
    """
    print("=" * 60)
    print("GENERATING SIG INSTRUCTIONS FOR MEDICATIONS")
    print("=" * 60)
    
    # Read the medication table
    print("📂 Reading medication table...")
    df = pd.read_csv('data/medication_table.csv', dtype={'rxcui': str})
    print(f"Loaded {len(df):,} medications")
    
    # Generate SIG instructions for each medication
    print("🧠 Generating intelligent SIG instructions...")
    df['sig_instructions'] = df.apply(generate_sig_templates, axis=1)
    
    # Convert list to JSON string for CSV storage
    df['sig_instructions_json'] = df['sig_instructions'].apply(lambda x: json.dumps(x))
    
    # Create a readable sig_primary column with the first/primary SIG
    df['sig_primary'] = df['sig_instructions'].apply(lambda x: x[0] if x else "Use as directed")
    
    # Count total SIGs generated
    total_sigs = df['sig_instructions'].apply(len).sum()
    print(f"✅ Generated {total_sigs:,} total SIG instructions")
    
    # Show coverage statistics
    print(f"📊 SIG coverage:")
    print(f"  - All medications have at least 1 SIG: {(df['sig_instructions'].apply(len) > 0).sum():,}")
    print(f"  - Average SIGs per medication: {df['sig_instructions'].apply(len).mean():.1f}")
    
    # Save enhanced table
    output_path = 'data/medication_table_with_sigs.csv'
    print(f"\n💾 Saving enhanced table to {output_path}...")
    df.to_csv(output_path, index=False)
    
    # Show sample results
    print("\n" + "=" * 60)
    print("SAMPLE SIG INSTRUCTIONS")
    print("=" * 60)
    
    sample_df = df.head(10)
    for idx, row in sample_df.iterrows():
        print(f"\n🔹 {row['drug_name']} ({row['term_type']})")
        if row['dose_form']:
            print(f"   Form: {row['dose_form']}")
        if row['available_strength']:
            print(f"   Strength: {row['available_strength']}")
        print(f"   Primary SIG: {row['sig_primary']}")
        print(f"   Total SIG options: {len(row['sig_instructions'])}")
        
        # Show first 3 SIG options
        for i, sig in enumerate(row['sig_instructions'][:3], 1):
            print(f"     {i}. {sig}")
        if len(row['sig_instructions']) > 3:
            print(f"     ... and {len(row['sig_instructions']) - 3} more options")
    
    print(f"\n✅ Enhanced medication table saved successfully!")
    print(f"📁 Files created:")
    print(f"   - {output_path} (full table with SIG instructions)")
    print(f"   - Original table preserved at: data/medication_table.csv")
    
    return df

if __name__ == "__main__":
    enhanced_df = add_sig_instructions_to_table() 