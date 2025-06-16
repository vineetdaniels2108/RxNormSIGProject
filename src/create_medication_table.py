import pandas as pd
import os

def create_medication_table():
    """
    Create a comprehensive medication table by merging concepts and attributes data.
    """
    print("=" * 60)
    print("CREATING MEDICATION TABLE")
    print("=" * 60)
    
    # Read the processed CSV files with readable column names
    print("📂 Reading processed files...")
    concepts_df = pd.read_csv('data/concepts.csv', dtype={'rxcui': str}, low_memory=False)
    attributes_df = pd.read_csv('data/attributes.csv', dtype={'rxcui': str}, low_memory=False)
    
    print(f"Loaded {len(concepts_df):,} concept records")
    print(f"Loaded {len(attributes_df):,} attribute records")
    
    # STEP 1: Filter concepts to get medication names
    print("\n🔍 Filtering concepts for medications...")
    print("Looking for:")
    print("  - Source: RXNORM")
    print("  - Term types: SCD (Clinical Drug), SBD (Branded Drug), BN (Brand Name)")
    print("  - Language: English")
    print("  - Not suppressed")
    
    base_meds = concepts_df[
        (concepts_df['source_abbreviation'] == 'RXNORM') &
        (concepts_df['term_type'].isin(['SCD', 'SBD', 'BN'])) &
        (concepts_df['language'] == 'ENG') &
        (concepts_df['suppress_flag'] != 'Y')
    ][['rxcui', 'drug_name', 'term_type']].copy()
    
    print(f"✅ Found {len(base_meds):,} base medications")
    
    if len(base_meds) == 0:
        print("❌ No medications found with current filters. Let's check what's available...")
        print("\nUnique source_abbreviation values:")
        print(concepts_df['source_abbreviation'].value_counts().head(10))
        print("\nUnique term_type values:")
        print(concepts_df['term_type'].value_counts().head(20))
        return None
    
    print("\nSample medications:")
    print(base_meds.head())
    
    # STEP 2: Filter attributes for medication properties
    print("\n🔍 Filtering attributes for medication properties...")
    print("Looking for:")
    print("  - Source: RXNORM") 
    print("  - Attributes: RXN_STRENGTH, RXTERM_FORM, RXN_AVAILABLE_STRENGTH")
    print("  - Not suppressed")
    
    med_attributes = attributes_df[
        (attributes_df['source_abbreviation'] == 'RXNORM') &
        (attributes_df['attribute_name'].isin([
            'RXN_STRENGTH', 
            'RXTERM_FORM', 
            'RXN_AVAILABLE_STRENGTH',
            'RXN_BOSS_STRENGTH_NUM_VALUE',
            'RXN_BOSS_STRENGTH_NUM_UNIT',
            'RXN_BOSS_STRENGTH_DENOM_VALUE', 
            'RXN_BOSS_STRENGTH_DENOM_UNIT'
        ])) &
        (attributes_df['suppress_flag'] != 'Y')
    ][['rxcui', 'attribute_name', 'attribute_value']].copy()
    
    print(f"✅ Found {len(med_attributes):,} relevant attributes")
    
    if len(med_attributes) == 0:
        print("❌ No attributes found. Let's check what's available...")
        print("\nUnique attribute_name values:")
        print(attributes_df['attribute_name'].value_counts().head(20))
    else:
        print("\nAttribute breakdown:")
        print(med_attributes['attribute_name'].value_counts())
        print("\nSample attributes:")
        print(med_attributes.head())
    
    # STEP 3: Pivot attributes to create one row per medication
    print("\n🔄 Pivoting attributes...")
    
    if len(med_attributes) > 0:
        attribute_pivot = med_attributes.pivot_table(
            index='rxcui',
            columns='attribute_name',
            values='attribute_value',
            aggfunc='first'
        ).reset_index()
        
        # Rename columns to be more readable
        attribute_pivot = attribute_pivot.rename(columns={
            'RXN_STRENGTH': 'strength',
            'RXTERM_FORM': 'dose_form',
            'RXN_AVAILABLE_STRENGTH': 'available_strength',
            'RXN_BOSS_STRENGTH_NUM_VALUE': 'strength_num_value',
            'RXN_BOSS_STRENGTH_NUM_UNIT': 'strength_num_unit',
            'RXN_BOSS_STRENGTH_DENOM_VALUE': 'strength_denom_value',
            'RXN_BOSS_STRENGTH_DENOM_UNIT': 'strength_denom_unit'
        })
        
        print(f"✅ Pivoted to {len(attribute_pivot):,} unique medications with attributes")
        print("Available attribute columns:", [col for col in attribute_pivot.columns if col != 'rxcui'])
    else:
        # Create empty pivot table if no attributes found
        attribute_pivot = pd.DataFrame(columns=[
            'rxcui', 'strength', 'dose_form', 'available_strength',
            'strength_num_value', 'strength_num_unit', 'strength_denom_value', 'strength_denom_unit'
        ])
        print("⚠️  No attributes to pivot - creating empty attribute table")
    
    # STEP 4: Merge medications with their attributes
    print("\n🔗 Merging medications with attributes...")
    
    medication_table = pd.merge(
        base_meds,
        attribute_pivot,
        on='rxcui',
        how='left'
    )
    
    print(f"✅ Final table has {len(medication_table):,} medications")
    
    # STEP 5: Create searchable text column
    print("\n📝 Creating searchable text...")
    
    def create_searchable_text(row):
        parts = [str(row['drug_name'])]
        
        # Add non-empty attributes
        search_cols = ['dose_form', 'strength', 'available_strength']
        for col in search_cols:
            if col in row and pd.notna(row[col]) and str(row[col]).strip():
                parts.append(str(row[col]))
        
        return ' '.join(parts).strip()
    
    medication_table['searchable_text'] = medication_table.apply(create_searchable_text, axis=1)
    
    # STEP 6: Clean up the data
    print("🧹 Cleaning up data...")
    medication_table = medication_table.fillna('')
    
    # STEP 7: Save the final table
    output_path = 'data/medication_table.csv'
    print(f"\n💾 Saving medication table to {output_path}...")
    medication_table.to_csv(output_path, index=False)
    
    # STEP 8: Print final statistics
    print("\n" + "=" * 60)
    print("MEDICATION TABLE SUMMARY")
    print("=" * 60)
    print(f"Total medications: {len(medication_table):,}")
    
    # Term type breakdown
    print("\nTerm type breakdown:")
    print(medication_table['term_type'].value_counts())
    
    # Attribute coverage
    print("\nAttribute coverage:")
    attr_cols = ['dose_form', 'strength', 'available_strength', 'strength_num_value', 'strength_num_unit']
    for col in attr_cols:
        if col in medication_table.columns:
            non_empty = medication_table[col].astype(bool).sum()
            print(f"  {col}: {non_empty:,} medications ({non_empty/len(medication_table)*100:.1f}%)")
    
    # Sample of final data
    print(f"\nSample of final medication table:")
    display_cols = ['rxcui', 'drug_name', 'term_type']
    available_attr_cols = ['dose_form', 'strength', 'available_strength']
    for col in available_attr_cols:
        if col in medication_table.columns:
            display_cols.append(col)
    
    print(medication_table[display_cols].head(10).to_string(index=False))
    
    print("\n✅ Medication table created successfully!")
    return medication_table

if __name__ == "__main__":
    create_medication_table() 