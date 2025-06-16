#!/usr/bin/env python3
"""
Data Cleaning Improvements Demonstration

This script shows examples of how the data cleaning improved searchability
by comparing original vs cleaned medication data.
"""

import pandas as pd
import random

def show_cleaning_improvements():
    """Demonstrate the improvements from data cleaning."""
    
    print("🔍 MEDICATION DATA CLEANING IMPROVEMENTS")
    print("="*60)
    
    # Load the cleaned data
    df = pd.read_csv('data/medication_table_with_sigs.csv', dtype={'rxcui': str})
    
    # Check if we have cleaned columns
    if 'drug_name_clean' not in df.columns:
        print("❌ Cleaned data not found. Please run: python3 src/clean_medication_data.py")
        return
    
    print(f"📊 Total medications analyzed: {len(df):,}")
    print(f"📈 Average search keywords per medication: {df['search_keywords'].apply(lambda x: len(eval(x)) if x else 0).mean():.1f}")
    
    # Show drug name improvements
    print(f"\n💊 DRUG NAME IMPROVEMENTS")
    print("-" * 40)
    
    # Find examples where cleaning made significant changes
    name_changes = df[df['drug_name'] != df['drug_name_clean']].copy()
    
    if len(name_changes) > 0:
        print(f"Medications with improved names: {len(name_changes):,}")
        print("\nExamples of name improvements:")
        
        for idx, row in name_changes.sample(min(8, len(name_changes))).iterrows():
            print(f"  Before: {row['drug_name']}")
            print(f"  After:  {row['drug_name_clean']}")
            print()
    
    # Show dose form standardization
    print(f"🏷️  DOSE FORM STANDARDIZATION")
    print("-" * 40)
    
    dose_changes = df[df['dose_form'] != df['dose_form_clean']].dropna(subset=['dose_form', 'dose_form_clean'])
    
    if len(dose_changes) > 0:
        print(f"Dose forms standardized: {len(dose_changes):,}")
        print("\nExamples of dose form improvements:")
        
        # Group by original -> clean to show patterns
        dose_patterns = dose_changes.groupby(['dose_form', 'dose_form_clean']).size().reset_index(name='count')
        dose_patterns = dose_patterns.sort_values('count', ascending=False)
        
        for _, row in dose_patterns.head(8).iterrows():
            print(f"  {row['dose_form']} -> {row['dose_form_clean']} ({row['count']:,} medications)")
    
    # Show strength improvements
    print(f"\n💪 STRENGTH FORMAT IMPROVEMENTS")
    print("-" * 40)
    
    strength_changes = df[df['available_strength'] != df['available_strength_clean']].dropna(subset=['available_strength', 'available_strength_clean'])
    
    if len(strength_changes) > 0:
        print(f"Strength formats improved: {len(strength_changes):,}")
        print("\nExamples of strength improvements:")
        
        for idx, row in strength_changes.sample(min(5, len(strength_changes))).iterrows():
            print(f"  Before: {row['available_strength']}")
            print(f"  After:  {row['available_strength_clean']}")
            print()
    
    # Show search keyword examples
    print(f"🔍 SEARCH KEYWORD GENERATION")
    print("-" * 40)
    
    # Sample medications with their keywords
    sample_meds = df.sample(5)
    
    print("Sample medications with generated search keywords:")
    for idx, row in sample_meds.iterrows():
        print(f"\n💊 {row['drug_name_clean']}")
        if pd.notna(row['dose_form_clean']):
            print(f"   Form: {row['dose_form_clean']}")
        if pd.notna(row['available_strength_clean']):
            print(f"   Strength: {row['available_strength_clean']}")
        
        try:
            keywords = eval(row['search_keywords']) if row['search_keywords'] else []
            print(f"   Keywords: {', '.join(keywords[:8])}{'...' if len(keywords) > 8 else ''}")
        except:
            print("   Keywords: [parsing error]")
    
    # Search improvement examples
    print(f"\n🎯 SEARCH IMPROVEMENT EXAMPLES")
    print("-" * 40)
    
    print("With the cleaned data, you can now search for:")
    print("✓ 'Tablet' or 'tab' - finds all tablet medications")
    print("✓ 'MG' or 'mg' - finds medications with milligram strengths")
    print("✓ 'Aspirin' - properly capitalized brand names")
    print("✓ 'Solution' or 'sol' - finds all solution forms")
    print("✓ Case-insensitive searches work better")
    print("✓ Partial word matching improved")
    
    # Show completeness impact
    print(f"\n📈 DATA COMPLETENESS IMPACT")
    print("-" * 40)
    
    # Calculate completeness using cleaned fields
    key_fields = ['drug_name_clean', 'term_type', 'dose_form_clean', 'available_strength_clean', 'sig_primary']
    
    for field in key_fields:
        if field in df.columns:
            filled = (df[field].notna() & (df[field] != '')).sum()
            percentage = (filled / len(df)) * 100
            print(f"{field.replace('_clean', '').replace('_', ' ').title()}: {filled:,} ({percentage:.1f}%)")
    
    print(f"\n🚀 DASHBOARD ENHANCEMENTS")
    print("-" * 40)
    print("The Streamlit dashboard now includes:")
    print("✓ Enhanced search with multiple field support")
    print("✓ Cleaned, properly capitalized medication names")
    print("✓ Standardized dose form names (Tablet, Capsule, etc.)")
    print("✓ Consistent strength formatting (MG, ML, etc.)")
    print("✓ Search keywords for better matching")
    print("✓ Searchable text fields for comprehensive queries")
    
    print(f"\n🎉 Launch the improved dashboard with:")
    print(f"   streamlit run src/streamlit_dashboard.py")

if __name__ == "__main__":
    show_cleaning_improvements() 