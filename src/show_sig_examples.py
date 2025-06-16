import pandas as pd
import json

def show_sig_examples():
    """Show comprehensive examples of SIG instructions for different medication types."""
    
    print("=" * 80)
    print("COMPREHENSIVE SIG INSTRUCTION EXAMPLES")
    print("=" * 80)
    
    # Load the enhanced table
    df = pd.read_csv('data/medication_table_with_sigs.csv', dtype={'rxcui': str})
    
    # Group by dose form and show examples
    dose_forms = ['Tab', 'Cap', 'Cream', 'Ointment', 'Sol', 'Gel', 'Lotion', 'Spray']
    
    for form in dose_forms:
        form_meds = df[df['dose_form'].str.contains(form, na=False, case=False)]
        if len(form_meds) > 0:
            print(f"\n🔹 {form.upper()} MEDICATIONS ({len(form_meds):,} total)")
            print("-" * 50)
            
            # Show first few examples
            for idx, row in form_meds.head(3).iterrows():
                print(f"\n📋 {row['drug_name']}")
                if row['available_strength']:
                    print(f"   Strength: {row['available_strength']}")
                
                # Parse and show SIG instructions
                sigs = json.loads(row['sig_instructions_json'])
                print(f"   SIG Options ({len(sigs)} total):")
                for i, sig in enumerate(sigs[:4], 1):
                    print(f"      {i}. {sig}")
                if len(sigs) > 4:
                    print(f"      ... and {len(sigs) - 4} more")
    
    # Show special categories
    print(f"\n\n🔹 SPECIAL MEDICATION CATEGORIES")
    print("-" * 50)
    
    # Show antibiotics
    antibiotics = df[df['drug_name'].str.contains('amoxicillin|penicillin|azithromycin', na=False, case=False)]
    if len(antibiotics) > 0:
        print(f"\n💊 ANTIBIOTICS Example:")
        row = antibiotics.iloc[0]
        sigs = json.loads(row['sig_instructions_json'])
        print(f"   {row['drug_name']}")
        for i, sig in enumerate(sigs[:3], 1):
            print(f"      {i}. {sig}")
    
    # Show pain medications
    pain_meds = df[df['drug_name'].str.contains('ibuprofen|acetaminophen|aspirin', na=False, case=False)]
    if len(pain_meds) > 0:
        print(f"\n🩹 PAIN MEDICATIONS Example:")
        row = pain_meds.iloc[0]
        sigs = json.loads(row['sig_instructions_json'])
        print(f"   {row['drug_name']}")
        for i, sig in enumerate(sigs[:3], 1):
            print(f"      {i}. {sig}")
    
    # Summary statistics
    print(f"\n\n📊 SUMMARY STATISTICS")
    print("-" * 50)
    
    total_sigs = df['sig_instructions_json'].apply(lambda x: len(json.loads(x))).sum()
    avg_sigs = df['sig_instructions_json'].apply(lambda x: len(json.loads(x))).mean()
    
    print(f"Total medications: {len(df):,}")
    print(f"Total SIG instructions generated: {total_sigs:,}")
    print(f"Average SIGs per medication: {avg_sigs:.1f}")
    
    # Coverage by dose form
    print(f"\nDose form coverage:")
    form_counts = df['dose_form'].value_counts()
    for form, count in form_counts.head(10).items():
        if form and str(form) != 'nan':
            print(f"  {form}: {count:,} medications")
    
    print(f"\n✅ Enhanced medication table with SIGs ready for use!")

if __name__ == "__main__":
    show_sig_examples() 