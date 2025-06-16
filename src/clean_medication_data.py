#!/usr/bin/env python3
"""
Medication Data Cleaning Script for Enhanced Searchability

This script cleans and standardizes medication data to improve search functionality:
- Capitalizes first letters of drug names
- Standardizes dose forms and strength formats
- Removes special characters and extra whitespace
- Creates searchable aliases and keywords
- Normalizes text for better matching
"""

import pandas as pd
import re
import json
from collections import defaultdict

def clean_drug_name(name):
    """Clean and standardize drug names for better searchability."""
    if pd.isna(name) or name == '':
        return name
    
    # Convert to string and strip whitespace
    name = str(name).strip()
    
    # Remove extra whitespace between words
    name = re.sub(r'\s+', ' ', name)
    
    # Handle common medication name patterns
    
    # 1. Capitalize first letter of each word (Title Case)
    name = name.title()
    
    # 2. Fix common abbreviations that should be uppercase
    uppercase_words = [
        'Mg', 'Ml', 'Mcg', 'Iu', 'Hr', 'Er', 'Xr', 'Sr', 'La', 'Xl',
        'Hcl', 'Hbr', 'Na', 'K', 'Ca', 'Fe', 'Zn', 'Cr', 'Se',
        'Usp', 'Fda', 'Otc', 'Rx', 'Iv', 'Im', 'Po', 'Pr', 'Sl',
        'Bid', 'Tid', 'Qid', 'Qd', 'Prn', 'Ac', 'Pc', 'Hs',
        'Dha', 'Epa', 'Atp', 'Dna', 'Rna', 'Hiv', 'Aids', 'Copd',
        'Adhd', 'Ptsd', 'Ocd', 'Gerd', 'Ibs', 'Uti', 'Std'
    ]
    
    for word in uppercase_words:
        # Use word boundaries to avoid partial matches
        pattern = r'\b' + re.escape(word.lower()) + r'\b'
        name = re.sub(pattern, word.upper(), name, flags=re.IGNORECASE)
    
    # 3. Fix Roman numerals
    roman_numerals = ['Ii', 'Iii', 'Iv', 'Vi', 'Vii', 'Viii', 'Ix']
    for roman in roman_numerals:
        pattern = r'\b' + re.escape(roman.lower()) + r'\b'
        name = re.sub(pattern, roman.upper(), name, flags=re.IGNORECASE)
    
    # 4. Fix brand names in brackets (keep original capitalization for brand names)
    bracket_pattern = r'\[([^\]]+)\]'
    matches = re.finditer(bracket_pattern, name)
    for match in matches:
        brand_name = match.group(1)
        # Common brand names should maintain their specific capitalization
        brand_fixes = {
            'tylenol': 'Tylenol',
            'advil': 'Advil',
            'motrin': 'Motrin',
            'aspirin': 'Aspirin',
            'bayer': 'Bayer',
            'excedrin': 'Excedrin',
            'aleve': 'Aleve',
            'sudafed': 'Sudafed',
            'robitussin': 'Robitussin',
            'mucinex': 'Mucinex',
            'claritin': 'Claritin',
            'zyrtec': 'Zyrtec',
            'allegra': 'Allegra',
            'benadryl': 'Benadryl'
        }
        
        brand_lower = brand_name.lower()
        if brand_lower in brand_fixes:
            name = name.replace(f'[{brand_name}]', f'[{brand_fixes[brand_lower]}]')
        else:
            name = name.replace(f'[{brand_name}]', f'[{brand_name.title()}]')
    
    return name

def clean_dose_form(dose_form):
    """Standardize dose form abbreviations and names."""
    if pd.isna(dose_form) or dose_form == '':
        return dose_form
    
    dose_form = str(dose_form).strip()
    
    # Common dose form standardizations
    dose_form_mapping = {
        'tab': 'Tablet',
        'tabs': 'Tablet',
        'tablet': 'Tablet',
        'tablets': 'Tablet',
        'cap': 'Capsule',
        'caps': 'Capsule',
        'capsule': 'Capsule',
        'capsules': 'Capsule',
        'sol': 'Solution',
        'soln': 'Solution',
        'solution': 'Solution',
        'susp': 'Suspension',
        'suspension': 'Suspension',
        'syr': 'Syrup',
        'syrup': 'Syrup',
        'inj': 'Injection',
        'injection': 'Injection',
        'cr': 'Cream',
        'cream': 'Cream',
        'oint': 'Ointment',
        'ointment': 'Ointment',
        'gel': 'Gel',
        'lot': 'Lotion',
        'lotion': 'Lotion',
        'spr': 'Spray',
        'spray': 'Spray',
        'drop': 'Drops',
        'drops': 'Drops',
        'patch': 'Patch',
        'film': 'Film',
        'powder': 'Powder',
        'granules': 'Granules'
    }
    
    dose_form_lower = dose_form.lower()
    if dose_form_lower in dose_form_mapping:
        return dose_form_mapping[dose_form_lower]
    
    # If not in mapping, return title case
    return dose_form.title()

def clean_strength(strength):
    """Standardize strength format for better readability."""
    if pd.isna(strength) or strength == '':
        return strength
    
    strength = str(strength).strip()
    
    # Standardize units
    unit_replacements = {
        'mg': 'MG',
        'mcg': 'MCG',
        'ml': 'ML',
        'iu': 'IU',
        'units': 'Units',
        'unit': 'Unit',
        '%': '%'
    }
    
    for old_unit, new_unit in unit_replacements.items():
        # Use word boundaries for exact matches
        pattern = r'\b' + re.escape(old_unit) + r'\b'
        strength = re.sub(pattern, new_unit, strength, flags=re.IGNORECASE)
    
    # Add space before units if missing
    strength = re.sub(r'(\d)([A-Za-z%])', r'\1 \2', strength)
    
    # Remove extra spaces
    strength = re.sub(r'\s+', ' ', strength).strip()
    
    return strength

def create_search_keywords(row):
    """Create additional search keywords for each medication."""
    keywords = set()
    
    # Add drug name words
    if pd.notna(row['drug_name_clean']):
        # Remove brackets and split into words
        name_words = re.sub(r'[\[\]]', '', row['drug_name_clean']).split()
        keywords.update([word.lower() for word in name_words if len(word) > 2])
    
    # Add dose form variations
    if pd.notna(row['dose_form_clean']):
        dose_form = row['dose_form_clean'].lower()
        keywords.add(dose_form)
        
        # Add common abbreviations
        dose_form_abbrevs = {
            'tablet': ['tab', 'tabs'],
            'capsule': ['cap', 'caps'],
            'solution': ['sol', 'soln'],
            'suspension': ['susp'],
            'injection': ['inj'],
            'cream': ['cr'],
            'ointment': ['oint'],
            'spray': ['spr'],
            'lotion': ['lot']
        }
        
        if dose_form in dose_form_abbrevs:
            keywords.update(dose_form_abbrevs[dose_form])
    
    # Add strength components
    if pd.notna(row['available_strength_clean']):
        strength_words = row['available_strength_clean'].split()
        keywords.update([word.lower() for word in strength_words])
    
    # Add term type
    if pd.notna(row['term_type']):
        keywords.add(row['term_type'].lower())
    
    return list(keywords)

def create_searchable_text(row):
    """Create a comprehensive searchable text field."""
    text_parts = []
    
    if pd.notna(row['drug_name_clean']):
        text_parts.append(row['drug_name_clean'])
    
    if pd.notna(row['dose_form_clean']):
        text_parts.append(row['dose_form_clean'])
    
    if pd.notna(row['available_strength_clean']):
        text_parts.append(row['available_strength_clean'])
    
    if pd.notna(row['term_type']):
        text_parts.append(row['term_type'])
    
    # Add search keywords
    if 'search_keywords' in row:
        text_parts.extend(row['search_keywords'])
    
    return ' '.join(text_parts).lower()

def clean_medication_data():
    """Main function to clean the medication database."""
    
    print("🧹 Starting medication data cleaning...")
    
    # Load the data
    print("📂 Loading medication database...")
    df = pd.read_csv('data/medication_table_with_sigs.csv', dtype={'rxcui': str})
    
    print(f"   Loaded {len(df):,} medications")
    
    # Clean drug names
    print("💊 Cleaning drug names...")
    df['drug_name_clean'] = df['drug_name'].apply(clean_drug_name)
    
    # Clean dose forms
    print("🏷️  Standardizing dose forms...")
    df['dose_form_clean'] = df['dose_form'].apply(clean_dose_form)
    
    # Clean strength information
    print("💪 Standardizing strength data...")
    df['available_strength_clean'] = df['available_strength'].apply(clean_strength)
    
    # Create search keywords
    print("🔍 Generating search keywords...")
    df['search_keywords'] = df.apply(create_search_keywords, axis=1)
    
    # Create searchable text
    print("📝 Creating searchable text fields...")
    df['searchable_text'] = df.apply(create_searchable_text, axis=1)
    
    # Update the primary SIG with cleaned drug name
    print("🧠 Updating SIG instructions with cleaned names...")
    df['sig_primary_clean'] = df['sig_primary'].copy()
    
    # Create a summary of changes
    print("\n📊 CLEANING SUMMARY")
    print("="*50)
    
    # Drug name changes
    name_changes = df[df['drug_name'] != df['drug_name_clean']]
    print(f"Drug names cleaned: {len(name_changes):,}")
    
    # Dose form changes  
    dose_changes = df[df['dose_form'] != df['dose_form_clean']]
    print(f"Dose forms standardized: {len(dose_changes):,}")
    
    # Strength changes
    strength_changes = df[df['available_strength'] != df['available_strength_clean']]
    print(f"Strength formats cleaned: {len(strength_changes):,}")
    
    # Show examples of cleaning
    if len(name_changes) > 0:
        print(f"\n📝 Example drug name cleanings:")
        for idx, row in name_changes.head(5).iterrows():
            print(f"   Before: {row['drug_name']}")
            print(f"   After:  {row['drug_name_clean']}")
            print()
    
    if len(dose_changes) > 0:
        print(f"📝 Example dose form standardizations:")
        for idx, row in dose_changes.head(3).iterrows():
            if pd.notna(row['dose_form']) and pd.notna(row['dose_form_clean']):
                print(f"   Before: {row['dose_form']} -> After: {row['dose_form_clean']}")
    
    # Save cleaned data
    output_file = 'data/medication_table_with_sigs_cleaned.csv'
    print(f"\n💾 Saving cleaned data to: {output_file}")
    df.to_csv(output_file, index=False)
    
    # Also update the original file with cleaned versions as additional columns
    print(f"💾 Adding cleaned columns to original file...")
    df.to_csv('data/medication_table_with_sigs.csv', index=False)
    
    print(f"\n✅ Data cleaning complete!")
    print(f"   Original medications: {len(df):,}")
    print(f"   Average search keywords per medication: {df['search_keywords'].apply(len).mean():.1f}")
    
    return df

def show_cleaning_examples(df):
    """Show examples of the cleaned data."""
    
    print("\n🔍 CLEANING EXAMPLES")
    print("="*60)
    
    # Show a sample of cleaned medications
    sample_cols = [
        'drug_name', 'drug_name_clean', 
        'dose_form', 'dose_form_clean',
        'available_strength', 'available_strength_clean'
    ]
    
    print("Sample of cleaned medications:")
    sample_df = df[sample_cols].head(10)
    
    for idx, row in sample_df.iterrows():
        print(f"\nMedication {idx + 1}:")
        print(f"  Name:     {row['drug_name']} -> {row['drug_name_clean']}")
        if pd.notna(row['dose_form']):
            print(f"  Form:     {row['dose_form']} -> {row['dose_form_clean']}")
        if pd.notna(row['available_strength']):
            print(f"  Strength: {row['available_strength']} -> {row['available_strength_clean']}")

if __name__ == "__main__":
    print("🚀 Starting comprehensive medication data cleaning...")
    
    # Clean the data
    df = clean_medication_data()
    
    # Show examples
    show_cleaning_examples(df)
    
    print(f"\n🎉 All done! Use the cleaned data for improved search functionality.")
    print(f"📁 Files updated:")
    print(f"   - data/medication_table_with_sigs.csv (with new clean columns)")
    print(f"   - data/medication_table_with_sigs_cleaned.csv (cleaned version)") 