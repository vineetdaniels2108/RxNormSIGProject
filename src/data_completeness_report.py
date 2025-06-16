#!/usr/bin/env python3
"""
Data Completeness Report Generator for RxNorm Medication Database

This script analyzes the completeness of the medication database and generates
a comprehensive report showing missing data patterns and statistics.
"""

import pandas as pd
import json
from collections import Counter

def analyze_data_completeness():
    """Analyze and report on data completeness."""
    
    print("🔍 Loading medication database...")
    df = pd.read_csv('data/medication_table_with_sigs.csv', dtype={'rxcui': str})
    
    # Add completeness columns
    df['has_dose_form'] = df['dose_form'].notna() & (df['dose_form'] != '')
    df['has_strength'] = df['available_strength'].notna() & (df['available_strength'] != '')
    df['has_sig'] = df['sig_instructions_json'].notna() & (df['sig_instructions_json'] != '')
    
    # Parse SIG count
    df['sig_count'] = df['sig_instructions_json'].apply(
        lambda x: len(json.loads(x)) if x else 0
    )
    
    # Count filled key columns
    key_columns = ['drug_name', 'term_type', 'dose_form', 'available_strength', 'sig_primary']
    df['filled_columns'] = 0
    for col in key_columns:
        df['filled_columns'] += (df[col].notna() & (df[col] != '')).astype(int)
    
    df['completeness_percent'] = (df['filled_columns'] / len(key_columns)) * 100
    
    print("\n" + "="*60)
    print("📊 RXNORM MEDICATION DATABASE COMPLETENESS REPORT")
    print("="*60)
    
    # Overall statistics
    total_medications = len(df)
    print(f"\n📋 OVERALL STATISTICS")
    print(f"Total medications: {total_medications:,}")
    print(f"Average completeness: {df['completeness_percent'].mean():.1f}%")
    
    # Completeness by field
    print(f"\n🏷️  FIELD COMPLETENESS")
    field_stats = {
        'Drug Name': (df['drug_name'].notna() & (df['drug_name'] != '')).sum(),
        'Term Type': (df['term_type'].notna() & (df['term_type'] != '')).sum(), 
        'Dose Form': df['has_dose_form'].sum(),
        'Strength': df['has_strength'].sum(),
        'SIG Primary': (df['sig_primary'].notna() & (df['sig_primary'] != '')).sum()
    }
    
    for field, count in field_stats.items():
        percentage = (count / total_medications) * 100
        missing = total_medications - count
        print(f"{field:12}: {count:6,} ({percentage:5.1f}%) | Missing: {missing:6,}")
    
    # Completeness levels
    print(f"\n📈 COMPLETENESS LEVELS")
    completeness_ranges = [
        (100, 100, "Perfect (100%)"),
        (80, 99, "High (80-99%)"), 
        (60, 79, "Medium (60-79%)"),
        (40, 59, "Low (40-59%)"),
        (0, 39, "Very Low (0-39%)")
    ]
    
    for min_pct, max_pct, label in completeness_ranges:
        if min_pct == max_pct:
            count = len(df[df['completeness_percent'] == min_pct])
        else:
            count = len(df[(df['completeness_percent'] >= min_pct) & (df['completeness_percent'] <= max_pct)])
        percentage = (count / total_medications) * 100
        print(f"{label:18}: {count:6,} ({percentage:5.1f}%)")
    
    # Complete records analysis
    complete_records = df[df['filled_columns'] == 5]
    print(f"\n✅ COMPLETE RECORDS ANALYSIS")
    print(f"Complete records (all 5 fields): {len(complete_records):,} ({len(complete_records)/total_medications*100:.1f}%)")
    
    if len(complete_records) > 0:
        print(f"Average SIG count for complete records: {complete_records['sig_count'].mean():.1f}")
        
        # Top complete term types
        complete_by_type = complete_records['term_type'].value_counts()
        print(f"\nComplete records by term type:")
        for term_type, count in complete_by_type.items():
            print(f"  {term_type}: {count:,}")
    
    # Missing data patterns
    print(f"\n🕳️  MISSING DATA PATTERNS")
    
    # Most common missing combinations
    missing_patterns = df.groupby(['has_dose_form', 'has_strength']).size().reset_index(name='count')
    missing_patterns = missing_patterns.sort_values('count', ascending=False)
    
    print("Most common missing data combinations:")
    for _, row in missing_patterns.iterrows():
        dose_status = "✓" if row['has_dose_form'] else "✗"
        strength_status = "✓" if row['has_strength'] else "✗"
        percentage = (row['count'] / total_medications) * 100
        print(f"  Dose Form: {dose_status}, Strength: {strength_status} -> {row['count']:6,} ({percentage:5.1f}%)")
    
    # Term type analysis
    print(f"\n🏷️  COMPLETENESS BY TERM TYPE")
    term_completeness = df.groupby('term_type').agg({
        'has_dose_form': ['sum', 'count'],
        'has_strength': ['sum', 'count'],
        'has_sig': ['sum', 'count'],
        'completeness_percent': 'mean'
    }).round(1)
    
    for term_type in df['term_type'].unique():
        term_df = df[df['term_type'] == term_type]
        total = len(term_df)
        dose_pct = (term_df['has_dose_form'].sum() / total) * 100
        strength_pct = (term_df['has_strength'].sum() / total) * 100
        sig_pct = (term_df['has_sig'].sum() / total) * 100
        avg_completeness = term_df['completeness_percent'].mean()
        
        print(f"\n{term_type} ({total:,} medications):")
        print(f"  Dose Form: {dose_pct:5.1f}%")
        print(f"  Strength:  {strength_pct:5.1f}%") 
        print(f"  SIG:       {sig_pct:5.1f}%")
        print(f"  Average:   {avg_completeness:5.1f}%")
    
    # SIG analysis
    print(f"\n🧠 SIG INSTRUCTIONS ANALYSIS")
    print(f"Medications with SIG instructions: {df['has_sig'].sum():,} ({df['has_sig'].mean()*100:.1f}%)")
    print(f"Average SIG count per medication: {df['sig_count'].mean():.1f}")
    print(f"Maximum SIG count: {df['sig_count'].max()}")
    
    # SIG count distribution
    sig_dist = df['sig_count'].value_counts().sort_index()
    print(f"\nSIG count distribution:")
    for count, freq in sig_dist.head(10).items():
        percentage = (freq / total_medications) * 100
        print(f"  {count} SIGs: {freq:6,} medications ({percentage:5.1f}%)")
    
    # Dose form analysis
    print(f"\n💊 DOSE FORM ANALYSIS")
    dose_form_stats = df['dose_form'].value_counts()
    print(f"Unique dose forms: {df['dose_form'].nunique()}")
    print(f"Most common dose forms:")
    
    for dose_form, count in dose_form_stats.head(10).items():
        percentage = (count / total_medications) * 100
        print(f"  {dose_form:20}: {count:6,} ({percentage:5.1f}%)")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS")
    
    missing_dose = total_medications - df['has_dose_form'].sum()
    missing_strength = total_medications - df['has_strength'].sum()
    
    if missing_dose > 0:
        print(f"• {missing_dose:,} medications missing dose form data ({missing_dose/total_medications*100:.1f}%)")
    
    if missing_strength > 0:
        print(f"• {missing_strength:,} medications missing strength data ({missing_strength/total_medications*100:.1f}%)")
    
    incomplete_records = total_medications - len(complete_records)
    if incomplete_records > 0:
        print(f"• {incomplete_records:,} medications have incomplete data ({incomplete_records/total_medications*100:.1f}%)")
    
    print(f"\n📁 For detailed analysis, use the interactive dashboard:")
    print(f"   streamlit run src/streamlit_dashboard.py")
    
    return df

def export_completeness_summary(df):
    """Export a summary of completeness data."""
    
    # Create summary dataframe
    summary_data = []
    
    for term_type in df['term_type'].unique():
        term_df = df[df['term_type'] == term_type]
        total = len(term_df)
        
        summary_data.append({
            'term_type': term_type,
            'total_medications': total,
            'complete_records': len(term_df[term_df['filled_columns'] == 5]),
            'has_dose_form': term_df['has_dose_form'].sum(),
            'has_strength': term_df['has_strength'].sum(),
            'has_sig': term_df['has_sig'].sum(),
            'avg_completeness_percent': term_df['completeness_percent'].mean(),
            'avg_sig_count': term_df['sig_count'].mean()
        })
    
    summary_df = pd.DataFrame(summary_data)
    
    # Add percentage columns
    summary_df['complete_records_pct'] = (summary_df['complete_records'] / summary_df['total_medications']) * 100
    summary_df['dose_form_pct'] = (summary_df['has_dose_form'] / summary_df['total_medications']) * 100
    summary_df['strength_pct'] = (summary_df['has_strength'] / summary_df['total_medications']) * 100
    summary_df['sig_pct'] = (summary_df['has_sig'] / summary_df['total_medications']) * 100
    
    # Round percentages
    pct_cols = [col for col in summary_df.columns if 'pct' in col or 'percent' in col]
    summary_df[pct_cols] = summary_df[pct_cols].round(1)
    
    # Export
    output_file = 'data/completeness_summary.csv'
    summary_df.to_csv(output_file, index=False)
    print(f"\n📊 Completeness summary exported to: {output_file}")
    
    return summary_df

if __name__ == "__main__":
    print("🚀 Starting data completeness analysis...")
    df = analyze_data_completeness()
    
    print(f"\n💾 Exporting summary...")
    summary_df = export_completeness_summary(df)
    
    print(f"\n✅ Analysis complete!") 