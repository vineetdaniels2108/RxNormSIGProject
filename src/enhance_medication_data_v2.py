#!/usr/bin/env python3

import pandas as pd
import numpy as np
import json
import re
from collections import defaultdict
from tqdm import tqdm

def clean_pharmaceutical_company_name(company_name):
    """Clean and standardize pharmaceutical company names."""
    if pd.isna(company_name) or not company_name:
        return None
    
    company = str(company_name).strip()
    
    # Comprehensive pharmaceutical company name mapping
    company_mappings = {
        # Eli Lilly variations
        'lilly': 'Eli Lilly',
        'eli lilly': 'Eli Lilly',
        'lilly, eli': 'Eli Lilly',
        'eli & company': 'Eli Lilly',
        
        # Pfizer variations
        'pfizer': 'Pfizer',
        'pfizer labs': 'Pfizer',
        'pfizer u.s.': 'Pfizer',
        'pfizer laboratories': 'Pfizer',
        'pfizer inc': 'Pfizer',
        'pfizer consumer': 'Pfizer',
        'parke-davis': 'Pfizer',  # Pfizer subsidiary
        'parke davis': 'Pfizer',
        
        # Johnson & Johnson variations
        'johnson': 'Johnson & Johnson',
        'johnson & johnson': 'Johnson & Johnson',
        'j & j': 'Johnson & Johnson',
        'janssen': 'Johnson & Johnson',  # J&J subsidiary
        'mcneil': 'Johnson & Johnson',   # J&J subsidiary
        
        # Merck variations
        'merck': 'Merck',
        'merck & co': 'Merck',
        'merck sharp': 'Merck',
        'merck sharp & dohme': 'Merck',
        'msd': 'Merck',
        
        # Novartis variations
        'novartis': 'Novartis',
        'novartis pharmaceuticals': 'Novartis',
        'novartis consumer': 'Novartis',
        'sandoz': 'Novartis',  # Novartis subsidiary
        'ciba': 'Novartis',    # Former Novartis company
        
        # Roche variations
        'roche': 'Roche',
        'roche laboratories': 'Roche',
        'hoffmann-la roche': 'Roche',
        'genentech': 'Roche',  # Roche subsidiary
        
        # Bristol-Myers Squibb variations
        'bristol': 'Bristol-Myers Squibb',
        'bristol-myers': 'Bristol-Myers Squibb',
        'bristol myers squibb': 'Bristol-Myers Squibb',
        'bms': 'Bristol-Myers Squibb',
        
        # Sanofi variations
        'sanofi': 'Sanofi',
        'sanofi-aventis': 'Sanofi',
        'sanofi-synthelabo': 'Sanofi',
        'aventis': 'Sanofi',
        'chattem': 'Sanofi',  # Sanofi subsidiary
        
        # AbbVie variations
        'abbvie': 'AbbVie',
        'abbott': 'AbbVie',  # AbbVie spun off from Abbott
        
        # Bayer variations
        'bayer': 'Bayer',
        'bayer healthcare': 'Bayer',
        'bayer corp': 'Bayer',
        'bayer pharmaceutical': 'Bayer',
        
        # GlaxoSmithKline variations
        'glaxosmithkline': 'GlaxoSmithKline',
        'gsk': 'GlaxoSmithKline',
        'glaxo': 'GlaxoSmithKline',
        'smithkline': 'GlaxoSmithKline',
        
        # Boehringer Ingelheim variations
        'boehringer': 'Boehringer Ingelheim',
        'boehringer ingelheim': 'Boehringer Ingelheim',
        
        # Amgen variations
        'amgen': 'Amgen',
        
        # Gilead variations
        'gilead': 'Gilead Sciences',
        'gilead sciences': 'Gilead Sciences',
        
        # Takeda variations
        'takeda': 'Takeda',
        'takeda pharmaceutical': 'Takeda',
        
        # Biogen variations
        'biogen': 'Biogen',
        'biogen idec': 'Biogen',
        
        # Regeneron variations
        'regeneron': 'Regeneron',
        
        # Moderna variations
        'moderna': 'Moderna',
        
        # BioNTech variations
        'biontech': 'BioNTech',
        
        # Allergan variations
        'allergan': 'Allergan',
        
        # Teva variations
        'teva': 'Teva',
        'teva pharmaceutical': 'Teva',
        
        # Mylan variations
        'mylan': 'Mylan',
        
        # Actavis variations
        'actavis': 'Actavis',
        
        # Sun Pharma variations
        'sun pharma': 'Sun Pharma',
        'sun pharmaceutical': 'Sun Pharma',
    }
    
    # Normalize the company name for matching
    company_lower = company.lower()
    
    # Try to find a match in our mapping
    for pattern, clean_name in company_mappings.items():
        if pattern in company_lower:
            return clean_name
    
    # If no direct match, try to extract the main company name
    # Remove common suffixes and clean up
    cleaned = re.sub(r',?\s*(inc\.?|llc\.?|corp\.?|ltd\.?|company|co\.?|pharmaceutical[s]?|pharma|laboratories|lab[s]?|division|div\.?|group|healthcare|consumer|care|biotechnology|bio)(\s|$)', '', company, flags=re.IGNORECASE)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    # If we have a reasonable company name left, return it
    if len(cleaned) > 2 and not re.match(r'^[^a-zA-Z]*$', cleaned):
        return cleaned
    
    # Otherwise return the original
    return company

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
    """Extract pharmaceutical company/labeler information with cleaning."""
    print("🏢 Extracting and cleaning pharmaceutical company/labeler information...")
    
    labeler_data = attributes_df[attributes_df['attribute_name'] == 'LABELER'].copy()
    
    # Group labelers by RXCUI
    labeler_groups = labeler_data.groupby('rxcui')['attribute_value'].apply(list).to_dict()
    
    # Create summary columns
    labeler_summary = {}
    
    for rxcui, labeler_list in labeler_groups.items():
        # Clean and format labeler names
        clean_labelers = [labeler.strip() for labeler in labeler_list if labeler and str(labeler).strip()]
        
        # Clean pharmaceutical company names
        cleaned_pharma_companies = []
        for labeler in clean_labelers:
            cleaned_name = clean_pharmaceutical_company_name(labeler)
            if cleaned_name:
                cleaned_pharma_companies.append(cleaned_name)
        
        # Remove duplicates while preserving order
        unique_pharma_companies = []
        seen = set()
        for company in cleaned_pharma_companies:
            if company not in seen:
                unique_pharma_companies.append(company)
                seen.add(company)
        
        labeler_summary[rxcui] = {
            'labelers': clean_labelers,
            'labeler_primary': clean_labelers[0] if clean_labelers else None,
            'labeler_count': len(clean_labelers),
            'pharma_companies_cleaned': unique_pharma_companies,
            'pharma_company_primary': unique_pharma_companies[0] if unique_pharma_companies else None,
            'labelers_json': json.dumps(clean_labelers) if clean_labelers else None,
            'pharma_companies_json': json.dumps(unique_pharma_companies) if unique_pharma_companies else None
        }
    
    print(f"   ✅ Found labeler info for {len(labeler_summary):,} medications")
    print(f"   ✅ Found cleaned pharma companies for {len([s for s in labeler_summary.values() if s['pharma_companies_cleaned']]):,} medications")
    
    # Show top cleaned pharmaceutical companies
    company_counts = {}
    for data in labeler_summary.values():
        for company in data.get('pharma_companies_cleaned', []):
            company_counts[company] = company_counts.get(company, 0) + 1
    
    if company_counts:
        print(f"   📊 Top cleaned pharmaceutical companies:")
        for company, count in sorted(company_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"      • {company}: {count:,} medications")
    
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
    """Enhance medication file with NDC, cleaned labeler, and GPI data."""
    print(f"📊 Enhancing {input_file}...")
    
    # Read medication data - include all columns
    df = pd.read_csv(input_file, dtype={'rxcui': str})
    original_count = len(df)
    
    print(f"   📋 Original data: {original_count:,} medications")
    
    # Add NDC columns
    print("   🔗 Adding NDC data...")
    df['ndc_primary'] = df['rxcui'].map(lambda x: ndc_data.get(x, {}).get('ndc_primary'))
    df['ndc_count'] = df['rxcui'].map(lambda x: ndc_data.get(x, {}).get('ndc_count', 0))
    df['ndc_codes_json'] = df['rxcui'].map(lambda x: ndc_data.get(x, {}).get('ndc_codes_json'))
    
    # Add labeler/company columns with cleaned names
    print("   🏢 Adding cleaned pharmaceutical company data...")
    df['labeler_primary'] = df['rxcui'].map(lambda x: labeler_data.get(x, {}).get('labeler_primary'))
    df['labeler_count'] = df['rxcui'].map(lambda x: labeler_data.get(x, {}).get('labeler_count', 0))
    df['pharma_company_cleaned'] = df['rxcui'].map(lambda x: labeler_data.get(x, {}).get('pharma_company_primary'))
    df['labelers_json'] = df['rxcui'].map(lambda x: labeler_data.get(x, {}).get('labelers_json'))
    df['pharma_companies_json'] = df['rxcui'].map(lambda x: labeler_data.get(x, {}).get('pharma_companies_json'))
    
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
    print("   🔍 Creating enhanced searchable text...")
    def create_enhanced_searchable_text(row):
        """Create enhanced searchable text including all relevant information."""
        search_terms = []
        
        # Add original searchable text if available
        if pd.notna(row.get('searchable_text')):
            search_terms.append(str(row['searchable_text']))
        
        # Add drug name variations
        if pd.notna(row.get('drug_name')):
            search_terms.append(str(row['drug_name']))
        if pd.notna(row.get('drug_name_clean')):
            search_terms.append(str(row['drug_name_clean']))
        
        # Add cleaned pharmaceutical company
        if pd.notna(row.get('pharma_company_cleaned')):
            search_terms.append(str(row['pharma_company_cleaned']))
        
        # Add primary labeler
        if pd.notna(row.get('labeler_primary')):
            search_terms.append(str(row['labeler_primary']))
        
        # Add all pharmaceutical companies
        if pd.notna(row.get('pharma_companies_json')):
            try:
                pharma_list = json.loads(row['pharma_companies_json'])
                search_terms.extend(pharma_list)
            except:
                pass
        
        # Add NDC code
        if pd.notna(row.get('ndc_primary')):
            search_terms.append(str(row['ndc_primary']))
        
        # Add dose form and strength
        if pd.notna(row.get('dose_form')):
            search_terms.append(str(row['dose_form']))
        if pd.notna(row.get('available_strength')):
            search_terms.append(str(row['available_strength']))
        
        return ' | '.join(search_terms) if search_terms else None
    
    df['enhanced_searchable_text'] = df.apply(create_enhanced_searchable_text, axis=1)
    
    # Create merged brand name + drug name column
    print("   🏷️ Creating merged brand + drug name column...")
    def create_merged_brand_drug_name(row):
        """Create a merged brand name + drug name for better identification."""
        parts = []
        
        # Add pharmaceutical company if available
        if pd.notna(row.get('pharma_company_cleaned')):
            parts.append(f"[{row['pharma_company_cleaned']}]")
        
        # Add drug name (use cleaned version if available)
        drug_name = row.get('drug_name_clean') if pd.notna(row.get('drug_name_clean')) else row.get('drug_name')
        if pd.notna(drug_name):
            parts.append(str(drug_name))
        
        # Add dose form if available
        dose_form = row.get('dose_form_clean') if pd.notna(row.get('dose_form_clean')) else row.get('dose_form')
        if pd.notna(dose_form):
            parts.append(f"({dose_form})")
        
        # Add strength if available
        strength = row.get('available_strength_clean') if pd.notna(row.get('available_strength_clean')) else row.get('available_strength')
        if pd.notna(strength):
            parts.append(f"{strength}")
        
        return ' '.join(parts) if parts else None
    
    df['brand_drug_name_merged'] = df.apply(create_merged_brand_drug_name, axis=1)
    
    # Add data completeness columns efficiently
    df['has_dose_form'] = df['dose_form'].notna() & (df['dose_form'] != '')
    df['has_strength'] = df['available_strength'].notna() & (df['available_strength'] != '')
    df['has_sig'] = df.get('sig_count', pd.Series(0)) > 0
    df['has_ndc'] = df.get('ndc_count', pd.Series(0)) > 0
    df['has_pharma_company'] = df.get('pharma_company_cleaned', pd.Series()).notna()
    
    # Create summary statistics
    ndc_coverage = (df['ndc_count'] > 0).sum()
    labeler_coverage = (df['labeler_count'] > 0).sum()
    pharma_coverage = df['pharma_company_cleaned'].notna().sum()
    gpi_coverage = (df['gpi_count'] > 0).sum() if 'gpi_count' in df.columns else 0
    merged_names = df['brand_drug_name_merged'].notna().sum()
    
    print(f"   📊 Enhanced data coverage:")
    print(f"      NDC codes: {ndc_coverage:,} medications ({(ndc_coverage/original_count)*100:.1f}%)")
    print(f"      Labeler info: {labeler_coverage:,} medications ({(labeler_coverage/original_count)*100:.1f}%)")
    print(f"      Cleaned pharma companies: {pharma_coverage:,} medications ({(pharma_coverage/original_count)*100:.1f}%)")
    print(f"      GPI codes: {gpi_coverage:,} medications ({(gpi_coverage/original_count)*100:.1f}%)")
    print(f"      Merged brand + drug names: {merged_names:,} medications ({(merged_names/original_count)*100:.1f}%)")
    
    # Save enhanced file
    df.to_csv(output_file, index=False)
    print(f"   ✅ Saved enhanced data to {output_file}")
    
    return df

def main():
    """Main function to enhance medication data with cleaned pharmaceutical companies and new features."""
    print("🚀 RxNorm Medication Data Enhancement v2.0")
    print("=" * 60)
    
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
        ('data/medication_table_with_sigs_cleaned.csv', 'data/medication_table_with_sigs_enhanced_v2.csv'),
        ('data/medication_table_with_sigs.csv', 'data/medication_table_with_sigs_enhanced_original_v2.csv')
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
    
    print("\n" + "=" * 60)
    print("✅ Enhancement v2.0 complete!")
    print("\n📊 New/Updated columns in enhanced files:")
    print("   • ndc_primary - Primary NDC code")
    print("   • ndc_count - Number of NDC codes")
    print("   • ndc_codes_json - All NDC codes (JSON)")
    print("   • labeler_primary - Primary manufacturer/labeler")
    print("   • labeler_count - Number of labelers")
    print("   • pharma_company_cleaned - CLEANED major pharmaceutical company ⭐ NEW")
    print("   • labelers_json - All labelers (JSON)")
    print("   • pharma_companies_json - All cleaned pharma companies (JSON)")
    print("   • gpi_primary - Primary GPI code (if available)")
    print("   • gpi_count - Number of GPI codes")
    print("   • gpi_codes_json - All GPI codes (JSON)")
    print("   • enhanced_searchable_text - Enhanced searchable text with all data ⭐ IMPROVED")
    print("   • brand_drug_name_merged - Brand + drug + dose form merged ⭐ NEW")
    
    print("\n🏢 Pharmaceutical Company Name Cleaning:")
    print("   • Standardized 'Lilly, Eli & Company' → 'Eli Lilly'")
    print("   • Unified all Pfizer variations → 'Pfizer'")
    print("   • Consolidated Novartis subsidiaries → 'Novartis'")
    print("   • Cleaned Merck variations → 'Merck'")
    print("   • And many more standardizations...")
    
    print("\n🔍 Usage examples:")
    print("   • Search for 'Eli Lilly' (now standardized)")
    print("   • Search for 'Pfizer' (all variations unified)")
    print("   • Use the merged brand+drug names for better identification")
    print("   • Enhanced searchable text includes all relevant data")

if __name__ == "__main__":
    main() 