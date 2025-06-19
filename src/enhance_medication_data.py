#!/usr/bin/env python3

import pandas as pd
import numpy as np
import json
import re
from collections import defaultdict
from tqdm import tqdm

def extract_ndc_codes(attributes_df):
    """Extract NDC codes for each RXCUI."""
    print("📋 Extracting NDC codes...")
    
    ndc_data = attributes_df[attributes_df['attribute_name'] == 'NDC'].copy()
    
    # Group NDC codes by RXCUI
    ndc_groups = ndc_data.groupby('rxcui')['attribute_value'].apply(list).to_dict()
    
    # Create summary columns
    ndc_summary = {}
    for rxcui, ndc_list in ndc_groups.items():
        # Clean and format NDC codes
        clean_ndcs = [ndc.strip() for ndc in ndc_list if ndc and str(ndc).strip()]
        
        ndc_summary[rxcui] = {
            'ndc_codes': clean_ndcs,
            'ndc_primary': clean_ndcs[0] if clean_ndcs else None,
            'ndc_count': len(clean_ndcs),
            'ndc_codes_json': json.dumps(clean_ndcs) if clean_ndcs else None
        }
    
    print(f"   ✅ Found NDC codes for {len(ndc_summary):,} medications")
    return ndc_summary

def extract_labeler_info(attributes_df):
    """Extract pharmaceutical company/labeler information."""
    print("🏢 Extracting pharmaceutical company/labeler information...")
    
    labeler_data = attributes_df[attributes_df['attribute_name'] == 'LABELER'].copy()
    
    # Group labelers by RXCUI
    labeler_groups = labeler_data.groupby('rxcui')['attribute_value'].apply(list).to_dict()
    
    # Create summary columns
    labeler_summary = {}
    major_pharma_companies = [
        'Lilly', 'Pfizer', 'Johnson', 'Merck', 'Novartis', 'Roche', 'Bristol', 
        'AbbVie', 'Amgen', 'Gilead', 'Sanofi', 'GlaxoSmithKline', 'Bayer',
        'Boehringer', 'Takeda', 'Biogen', 'Regeneron', 'Moderna', 'BioNTech'
    ]
    
    for rxcui, labeler_list in labeler_groups.items():
        # Clean and format labeler names
        clean_labelers = [labeler.strip() for labeler in labeler_list if labeler and str(labeler).strip()]
        
        # Find major pharmaceutical companies
        major_pharma_found = []
        for labeler in clean_labelers:
            for company in major_pharma_companies:
                if company.lower() in labeler.lower():
                    major_pharma_found.append(labeler)
                    break
        
        labeler_summary[rxcui] = {
            'labelers': clean_labelers,
            'labeler_primary': clean_labelers[0] if clean_labelers else None,
            'labeler_count': len(clean_labelers),
            'major_pharma': major_pharma_found,
            'major_pharma_primary': major_pharma_found[0] if major_pharma_found else None,
            'labelers_json': json.dumps(clean_labelers) if clean_labelers else None,
            'major_pharma_json': json.dumps(major_pharma_found) if major_pharma_found else None
        }
    
    print(f"   ✅ Found labeler info for {len(labeler_summary):,} medications")
    print(f"   ✅ Found major pharma companies for {len([s for s in labeler_summary.values() if s['major_pharma']]):,} medications")
    return labeler_summary

def extract_gpi_codes(attributes_df):
    """Extract GPI codes from IMPRINT_CODE fields where available."""
    print("🔢 Extracting GPI codes from imprint data...")
    
    # Filter for imprint codes that contain GPI
    gpi_data = attributes_df[
        (attributes_df['attribute_name'] == 'IMPRINT_CODE') & 
        (attributes_df['attribute_value'].str.contains('GPI', case=False, na=False))
    ].copy()
    
    if gpi_data.empty:
        print("   ⚠️ No GPI codes found in imprint data")
        return {}
    
    # Group GPI codes by RXCUI
    gpi_groups = gpi_data.groupby('rxcui')['attribute_value'].apply(list).to_dict()
    
    # Extract GPI identifiers
    gpi_summary = {}
    for rxcui, gpi_list in gpi_groups.items():
        # Extract GPI patterns
        gpi_codes = []
        for item in gpi_list:
            if 'GPI' in str(item):
                gpi_codes.append(str(item))
        
        if gpi_codes:
            gpi_summary[rxcui] = {
                'gpi_codes': gpi_codes,
                'gpi_primary': gpi_codes[0],
                'gpi_count': len(gpi_codes),
                'gpi_codes_json': json.dumps(gpi_codes)
            }
    
    print(f"   ✅ Found GPI codes for {len(gpi_summary):,} medications")
    return gpi_summary

def enhance_medication_file(input_file, output_file, ndc_data, labeler_data, gpi_data):
    """Enhance medication file with NDC, labeler, and GPI data."""
    print(f"📊 Enhancing {input_file}...")
    
    # Read medication data
    df = pd.read_csv(input_file, dtype={'rxcui': str})
    original_count = len(df)
    
    print(f"   📋 Original data: {original_count:,} medications")
    
    # Add NDC columns
    print("   🔗 Adding NDC data...")
    df['ndc_primary'] = df['rxcui'].map(lambda x: ndc_data.get(x, {}).get('ndc_primary'))
    df['ndc_count'] = df['rxcui'].map(lambda x: ndc_data.get(x, {}).get('ndc_count', 0))
    df['ndc_codes_json'] = df['rxcui'].map(lambda x: ndc_data.get(x, {}).get('ndc_codes_json'))
    
    # Add labeler/company columns
    print("   🏢 Adding pharmaceutical company data...")
    df['labeler_primary'] = df['rxcui'].map(lambda x: labeler_data.get(x, {}).get('labeler_primary'))
    df['labeler_count'] = df['rxcui'].map(lambda x: labeler_data.get(x, {}).get('labeler_count', 0))
    df['major_pharma_primary'] = df['rxcui'].map(lambda x: labeler_data.get(x, {}).get('major_pharma_primary'))
    df['labelers_json'] = df['rxcui'].map(lambda x: labeler_data.get(x, {}).get('labelers_json'))
    df['major_pharma_json'] = df['rxcui'].map(lambda x: labeler_data.get(x, {}).get('major_pharma_json'))
    
    # Add GPI columns (if available)
    if gpi_data:
        print("   🔢 Adding GPI data...")
        df['gpi_primary'] = df['rxcui'].map(lambda x: gpi_data.get(x, {}).get('gpi_primary'))
        df['gpi_count'] = df['rxcui'].map(lambda x: gpi_data.get(x, {}).get('gpi_count', 0))
        df['gpi_codes_json'] = df['rxcui'].map(lambda x: gpi_data.get(x, {}).get('gpi_codes_json'))
    else:
        df['gpi_primary'] = None
        df['gpi_count'] = 0
        df['gpi_codes_json'] = None
    
    # Add search functionality for brand names
    print("   🔍 Creating searchable brand name fields...")
    def create_brand_searchable_text(row):
        """Create searchable text including all brand/company information."""
        search_terms = []
        
        # Add original searchable text if available
        if pd.notna(row.get('searchable_text')):
            search_terms.append(str(row['searchable_text']))
        
        # Add major pharma company
        if pd.notna(row.get('major_pharma_primary')):
            search_terms.append(str(row['major_pharma_primary']))
        
        # Add primary labeler
        if pd.notna(row.get('labeler_primary')):
            search_terms.append(str(row['labeler_primary']))
        
        # Add all major pharma companies
        if pd.notna(row.get('major_pharma_json')):
            try:
                major_pharma_list = json.loads(row['major_pharma_json'])
                search_terms.extend(major_pharma_list)
            except:
                pass
        
        return ' | '.join(search_terms) if search_terms else None
    
    df['brand_searchable_text'] = df.apply(create_brand_searchable_text, axis=1)
    
    # Create summary statistics
    ndc_coverage = (df['ndc_count'] > 0).sum()
    labeler_coverage = (df['labeler_count'] > 0).sum()
    major_pharma_coverage = df['major_pharma_primary'].notna().sum()
    gpi_coverage = (df['gpi_count'] > 0).sum() if 'gpi_count' in df.columns else 0
    
    print(f"   📊 Enhanced data coverage:")
    print(f"      NDC codes: {ndc_coverage:,} medications ({(ndc_coverage/original_count)*100:.1f}%)")
    print(f"      Labeler info: {labeler_coverage:,} medications ({(labeler_coverage/original_count)*100:.1f}%)")
    print(f"      Major pharma: {major_pharma_coverage:,} medications ({(major_pharma_coverage/original_count)*100:.1f}%)")
    print(f"      GPI codes: {gpi_coverage:,} medications ({(gpi_coverage/original_count)*100:.1f}%)")
    
    # Save enhanced file
    df.to_csv(output_file, index=False)
    print(f"   ✅ Saved enhanced data to {output_file}")
    
    return df

def create_brand_name_index(enhanced_df):
    """Create a searchable index of brand names for quick lookup."""
    print("📇 Creating brand name search index...")
    
    brand_index = {}
    
    for idx, row in enhanced_df.iterrows():
        rxcui = row['rxcui']
        drug_name = row.get('drug_name', '')
        
        # Index major pharma companies
        if pd.notna(row.get('major_pharma_json')):
            try:
                major_pharma_list = json.loads(row['major_pharma_json'])
                for company in major_pharma_list:
                    # Extract company name keywords
                    company_words = re.findall(r'\b[A-Za-z]+\b', company)
                    for word in company_words:
                        if len(word) > 2:  # Ignore short words
                            word_lower = word.lower()
                            if word_lower not in brand_index:
                                brand_index[word_lower] = []
                            brand_index[word_lower].append({
                                'rxcui': rxcui,
                                'drug_name': drug_name,
                                'company': company
                            })
            except:
                pass
    
    # Save brand index
    with open('data/brand_name_index.json', 'w') as f:
        json.dump(brand_index, f, indent=2)
    
    print(f"   ✅ Created brand index with {len(brand_index):,} searchable terms")
    print(f"   💾 Saved to data/brand_name_index.json")
    
    return brand_index

def main():
    """Main function to enhance medication data with NDC, brand names, and GPI codes."""
    print("🚀 RxNorm Medication Data Enhancement")
    print("=" * 50)
    
    # Load attributes data
    print("📂 Loading RxNorm attributes data...")
    try:
        # Read only the columns we need for better performance
        attributes_df = pd.read_csv(
            'data/attributes.csv',
            dtype={'rxcui': str},
            usecols=['rxcui', 'attribute_name', 'attribute_value']
        )
        print(f"   ✅ Loaded {len(attributes_df):,} attribute records")
    except Exception as e:
        print(f"   ❌ Error loading attributes.csv: {e}")
        return
    
    # Extract data
    ndc_data = extract_ndc_codes(attributes_df)
    labeler_data = extract_labeler_info(attributes_df)
    gpi_data = extract_gpi_codes(attributes_df)
    
    # Enhancement files to process
    files_to_enhance = [
        ('data/medication_table_with_sigs_cleaned.csv', 'data/medication_table_with_sigs_enhanced.csv'),
        ('data/medication_table_with_sigs.csv', 'data/medication_table_with_sigs_enhanced_original.csv')
    ]
    
    enhanced_data = None
    
    # Enhance each file
    for input_file, output_file in files_to_enhance:
        try:
            if pd.io.common.file_exists(input_file):
                enhanced_df = enhance_medication_file(input_file, output_file, ndc_data, labeler_data, gpi_data)
                if enhanced_data is None:  # Use first enhanced file for index creation
                    enhanced_data = enhanced_df
            else:
                print(f"   ⚠️ File not found: {input_file}")
        except Exception as e:
            print(f"   ❌ Error enhancing {input_file}: {e}")
    
    # Create brand name search index
    if enhanced_data is not None:
        brand_index = create_brand_name_index(enhanced_data)
        
        # Show some examples
        print("\n🎯 Brand Name Search Examples:")
        example_brands = ['lilly', 'pfizer', 'johnson', 'merck', 'novartis']
        for brand in example_brands:
            if brand in brand_index:
                count = len(brand_index[brand])
                print(f"   '{brand.title()}': {count} medications")
    
    print("\n" + "=" * 50)
    print("✅ Enhancement complete!")
    print("\n📊 New columns added to enhanced files:")
    print("   • ndc_primary - Primary NDC code")
    print("   • ndc_count - Number of NDC codes")
    print("   • ndc_codes_json - All NDC codes (JSON)")
    print("   • labeler_primary - Primary manufacturer/labeler")
    print("   • labeler_count - Number of labelers")
    print("   • major_pharma_primary - Primary major pharmaceutical company")
    print("   • labelers_json - All labelers (JSON)")
    print("   • major_pharma_json - All major pharma companies (JSON)")
    print("   • gpi_primary - Primary GPI code (if available)")
    print("   • gpi_count - Number of GPI codes")
    print("   • gpi_codes_json - All GPI codes (JSON)")
    print("   • brand_searchable_text - Enhanced searchable text with brand names")
    
    print("\n🔍 Usage examples:")
    print("   • Search for 'Lilly' to find Eli Lilly medications")
    print("   • Search for 'Pfizer' to find Pfizer medications")
    print("   • Filter by major_pharma_primary for specific companies")
    print("   • Use NDC codes for precise medication identification")

if __name__ == "__main__":
    main() 