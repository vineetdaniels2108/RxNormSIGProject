# 📊 RxNorm Medication Database - Data Usage Guide

A comprehensive guide for developers and healthcare professionals on how to use the RxNorm medication database with SIG instructions in your applications.

## 📁 Dataset Overview

This database contains **74,521+ medications** from RxNorm with intelligently generated SIG (Signa/dosage) instructions, making it perfect for healthcare applications, EMR systems, pharmacy software, and medical research.

### 📊 Key Statistics
- **74,521 total medications**
- **353,830+ SIG instructions** (average 4.7 per medication)
- **39,398 Clinical Drugs (SCD)**
- **23,457 Branded Drugs (SBD)**
- **11,666 Brand Names (BN)**
- **38 standardized dose forms**
- **65% have dose form data, 30.1% have strength data**

## 📋 Data Structure

### Main Dataset: `medication_table_with_sigs.csv`

| Column | Description | Type | Example |
|--------|-------------|------|---------|
| `rxcui` | RxNorm Concept Unique Identifier | String | "197804" |
| `drug_name` | Original medication name | String | "aspirin 325 MG Oral Tablet" |
| `drug_name_clean` | Cleaned, properly capitalized name | String | "Aspirin 325 MG Oral Tablet" |
| `term_type` | RxNorm term type (SCD/SBD/BN) | String | "SCD" |
| `dose_form` | Original dose form abbreviation | String | "Tab" |
| `dose_form_clean` | Standardized dose form | String | "Tablet" |
| `available_strength` | Original strength information | String | "325 mg" |
| `available_strength_clean` | Standardized strength | String | "325 MG" |
| `sig_primary` | Primary dosage instruction | String | "Take 1 tablet by mouth once daily" |
| `sig_instructions_json` | All SIG instructions (JSON array) | JSON String | `["Take 1 tablet...", "Take 2 tablets..."]` |
| `search_keywords` | Generated search keywords | JSON Array | `["aspirin", "tablet", "325", "mg", "oral"]` |
| `searchable_text` | Comprehensive search text | String | "aspirin 325 mg tablet oral scd..." |

### Data Quality Columns
| Column | Description |
|--------|-------------|
| `filled_columns` | Number of core fields with data (0-5) |
| `completeness_percent` | Data completeness percentage |
| `has_dose_form` | Boolean - has dose form data |
| `has_strength` | Boolean - has strength data |
| `sig_count` | Number of SIG instructions |

## 🚀 Quick Start Examples

### Python - Basic Usage

```python
import pandas as pd
import json

# Load the medication database
df = pd.read_csv('data/medication_table_with_sigs.csv')

# Search for specific medications
aspirin_meds = df[df['drug_name_clean'].str.contains('Aspirin', case=False)]
print(f"Found {len(aspirin_meds)} Aspirin medications")

# Get SIG instructions for a medication
def get_sig_instructions(row):
    try:
        return json.loads(row['sig_instructions_json'])
    except:
        return []

# Example: Get all SIGs for first aspirin medication
first_aspirin = aspirin_meds.iloc[0]
sigs = get_sig_instructions(first_aspirin)
print(f"SIG instructions for {first_aspirin['drug_name_clean']}:")
for i, sig in enumerate(sigs, 1):
    print(f"{i}. {sig}")
```

### Python - Advanced Search

```python
def search_medications(df, query, field='all'):
    """Advanced medication search function"""
    query_lower = query.lower()
    
    if field == 'all':
        # Search across all fields including keywords
        mask = df['searchable_text'].str.contains(query_lower, case=False, na=False)
    elif field == 'name':
        mask = df['drug_name_clean'].str.contains(query, case=False, na=False)
    elif field == 'dose_form':
        mask = df['dose_form_clean'].str.contains(query, case=False, na=False)
    elif field == 'strength':
        mask = df['available_strength_clean'].str.contains(query, case=False, na=False)
    
    return df[mask]

# Example searches
tablets = search_medications(df, 'tablet', 'dose_form')
mg_500 = search_medications(df, '500 MG', 'strength')
comprehensive = search_medications(df, 'aspirin tablet 325')
```

### JavaScript/Node.js - CSV Processing

```javascript
const fs = require('fs');
const csv = require('csv-parser');

const medications = [];

fs.createReadStream('data/medication_table_with_sigs.csv')
  .pipe(csv())
  .on('data', (row) => {
    // Parse SIG instructions
    try {
      row.sig_instructions = JSON.parse(row.sig_instructions_json);
      row.search_keywords = JSON.parse(row.search_keywords);
    } catch (e) {
      row.sig_instructions = [];
      row.search_keywords = [];
    }
    
    medications.push(row);
  })
  .on('end', () => {
    console.log(`Loaded ${medications.length} medications`);
    
    // Example: Find tablets
    const tablets = medications.filter(med => 
      med.dose_form_clean && med.dose_form_clean.toLowerCase().includes('tablet')
    );
    
    console.log(`Found ${tablets.length} tablet medications`);
  });
```

### SQL - Database Integration

```sql
-- Create medications table
CREATE TABLE medications (
    rxcui VARCHAR(20) PRIMARY KEY,
    drug_name TEXT,
    drug_name_clean TEXT,
    term_type VARCHAR(10),
    dose_form VARCHAR(100),
    dose_form_clean VARCHAR(100),
    available_strength TEXT,
    available_strength_clean TEXT,
    sig_primary TEXT,
    sig_instructions_json TEXT,
    search_keywords TEXT,
    searchable_text TEXT,
    filled_columns INT,
    completeness_percent DECIMAL(5,2),
    sig_count INT
);

-- Example queries
-- Find all tablet medications
SELECT * FROM medications 
WHERE dose_form_clean = 'Tablet';

-- Find medications by strength
SELECT * FROM medications 
WHERE available_strength_clean LIKE '%500 MG%';

-- Get complete records only
SELECT * FROM medications 
WHERE filled_columns = 5;

-- Search with multiple criteria
SELECT * FROM medications 
WHERE searchable_text LIKE '%aspirin%' 
AND dose_form_clean = 'Tablet';
```

## 🏥 Healthcare Application Use Cases

### 1. Electronic Medical Records (EMR)

```python
def emr_medication_lookup(search_term):
    """EMR-style medication lookup with autocomplete"""
    results = search_medications(df, search_term)
    
    # Return structured data for EMR
    emr_results = []
    for _, med in results.head(10).iterrows():
        emr_results.append({
            'rxcui': med['rxcui'],
            'display_name': med['drug_name_clean'],
            'dose_form': med['dose_form_clean'],
            'strength': med['available_strength_clean'],
            'default_sig': med['sig_primary'],
            'term_type': med['term_type']
        })
    
    return emr_results
```

### 2. Pharmacy Management System

```python
def pharmacy_dispensing_info(rxcui):
    """Get dispensing information for pharmacy system"""
    med = df[df['rxcui'] == rxcui].iloc[0]
    
    sig_options = json.loads(med['sig_instructions_json'])
    
    return {
        'medication': med['drug_name_clean'],
        'ndc_info': {
            'dose_form': med['dose_form_clean'],
            'strength': med['available_strength_clean']
        },
        'sig_options': sig_options,
        'default_sig': med['sig_primary'],
        'counseling_points': generate_counseling_points(med)
    }

def generate_counseling_points(med):
    """Generate patient counseling points"""
    points = []
    
    dose_form = med['dose_form_clean']
    if dose_form == 'Tablet':
        points.append("Take with a full glass of water")
    elif dose_form == 'Cream':
        points.append("Apply thin layer to affected area")
    elif 'Solution' in dose_form:
        points.append("Shake well before use")
    
    return points
```

### 3. Clinical Decision Support

```python
def clinical_decision_support(patient_meds, new_medication_rxcui):
    """Basic interaction checking and dosing guidance"""
    new_med = df[df['rxcui'] == new_medication_rxcui].iloc[0]
    
    # Get drug name for interaction checking
    drug_name = new_med['drug_name_clean'].split()[0]  # First word is usually the drug
    
    # Get appropriate SIG based on dose form
    dose_form = new_med['dose_form_clean']
    sig_options = json.loads(new_med['sig_instructions_json'])
    
    # Filter SIGs by dose form appropriateness
    appropriate_sigs = [sig for sig in sig_options if dose_form.lower() in sig.lower()]
    
    return {
        'medication': new_med['drug_name_clean'],
        'recommended_sigs': appropriate_sigs or sig_options,
        'dose_form_guidance': get_dose_form_guidance(dose_form),
        'strength': new_med['available_strength_clean']
    }

def get_dose_form_guidance(dose_form):
    """Provide dose form specific guidance"""
    guidance = {
        'Tablet': 'Oral administration - consider with food if GI upset',
        'Capsule': 'Oral administration - swallow whole, do not crush',
        'Solution': 'Measure dose carefully, shake if suspension',
        'Cream': 'Topical use only - apply thin layer',
        'Injection': 'Parenteral administration - verify route and concentration'
    }
    return guidance.get(dose_form, 'Follow prescriber instructions')
```

## 🔍 Search and Filtering Best Practices

### 1. Multi-Field Search Implementation

```python
def smart_medication_search(query, max_results=50):
    """Intelligent medication search with ranking"""
    results = []
    
    # Split query into terms
    terms = query.lower().split()
    
    for _, med in df.iterrows():
        score = 0
        searchable = med['searchable_text'].lower()
        
        # Score based on term matches
        for term in terms:
            if term in searchable:
                # Higher score for exact matches in drug name
                if term in med['drug_name_clean'].lower():
                    score += 3
                # Medium score for dose form matches
                elif term in med['dose_form_clean'].lower() if pd.notna(med['dose_form_clean']) else '':
                    score += 2
                # Lower score for other matches
                else:
                    score += 1
        
        if score > 0:
            results.append((score, med))
    
    # Sort by score and return top results
    results.sort(key=lambda x: x[0], reverse=True)
    return [med for _, med in results[:max_results]]
```

### 2. Autocomplete Implementation

```python
def medication_autocomplete(partial_query, limit=10):
    """Provide autocomplete suggestions"""
    query_lower = partial_query.lower()
    
    # Find medications that start with the query
    exact_matches = df[
        df['drug_name_clean'].str.lower().str.startswith(query_lower)
    ]['drug_name_clean'].unique()
    
    # Find medications that contain the query
    contains_matches = df[
        df['drug_name_clean'].str.lower().str.contains(query_lower)
    ]['drug_name_clean'].unique()
    
    # Combine and deduplicate
    suggestions = list(exact_matches) + [m for m in contains_matches if m not in exact_matches]
    
    return suggestions[:limit]
```

## 📊 Data Quality and Validation

### Completeness Analysis

```python
def analyze_data_quality():
    """Analyze dataset completeness and quality"""
    quality_report = {
        'total_medications': len(df),
        'complete_records': len(df[df['filled_columns'] == 5]),
        'completeness_by_term_type': df.groupby('term_type')['completeness_percent'].mean(),
        'dose_form_coverage': df['has_dose_form'].mean() * 100,
        'strength_coverage': df['has_strength'].mean() * 100,
        'sig_coverage': (df['sig_count'] > 0).mean() * 100
    }
    
    return quality_report
```

### Data Validation

```python
def validate_medication_record(med_record):
    """Validate a medication record"""
    issues = []
    
    # Required fields
    if not med_record.get('rxcui'):
        issues.append("Missing RXCUI")
    
    if not med_record.get('drug_name_clean'):
        issues.append("Missing drug name")
    
    # SIG validation
    try:
        sigs = json.loads(med_record.get('sig_instructions_json', '[]'))
        if not sigs:
            issues.append("No SIG instructions available")
    except:
        issues.append("Invalid SIG JSON format")
    
    return issues
```

## 🔄 Integration Patterns

### REST API Example

```python
from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route('/api/medications/search')
def search_medications_api():
    query = request.args.get('q', '')
    limit = min(int(request.args.get('limit', 50)), 100)
    
    results = smart_medication_search(query, limit)
    
    return jsonify({
        'query': query,
        'count': len(results),
        'medications': [
            {
                'rxcui': med['rxcui'],
                'name': med['drug_name_clean'],
                'dose_form': med['dose_form_clean'],
                'strength': med['available_strength_clean'],
                'primary_sig': med['sig_primary'],
                'completeness': med['completeness_percent']
            }
            for med in results
        ]
    })

@app.route('/api/medications/<rxcui>/sigs')
def get_medication_sigs(rxcui):
    med = df[df['rxcui'] == rxcui]
    
    if med.empty:
        return jsonify({'error': 'Medication not found'}), 404
    
    med = med.iloc[0]
    sigs = json.loads(med['sig_instructions_json'])
    
    return jsonify({
        'rxcui': rxcui,
        'medication': med['drug_name_clean'],
        'primary_sig': med['sig_primary'],
        'all_sigs': sigs,
        'sig_count': len(sigs)
    })
```

### Database Sync Pattern

```python
def sync_to_database(connection_string):
    """Sync medication data to database"""
    import sqlite3
    
    conn = sqlite3.connect(connection_string)
    
    # Create table if not exists
    conn.execute('''
        CREATE TABLE IF NOT EXISTS medications (
            rxcui TEXT PRIMARY KEY,
            drug_name_clean TEXT,
            term_type TEXT,
            dose_form_clean TEXT,
            available_strength_clean TEXT,
            sig_primary TEXT,
            sig_instructions_json TEXT,
            completeness_percent REAL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Batch insert
    medications_data = []
    for _, med in df.iterrows():
        medications_data.append((
            med['rxcui'],
            med['drug_name_clean'],
            med['term_type'],
            med['dose_form_clean'],
            med['available_strength_clean'],
            med['sig_primary'],
            med['sig_instructions_json'],
            med['completeness_percent']
        ))
    
    conn.executemany('''
        INSERT OR REPLACE INTO medications 
        (rxcui, drug_name_clean, term_type, dose_form_clean, 
         available_strength_clean, sig_primary, sig_instructions_json, 
         completeness_percent) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', medications_data)
    
    conn.commit()
    conn.close()
```

## 📊 Analytics and Reporting

### Medication Usage Analytics

```python
def generate_usage_analytics():
    """Generate medication database usage analytics"""
    analytics = {
        'dose_form_distribution': df['dose_form_clean'].value_counts().to_dict(),
        'term_type_distribution': df['term_type'].value_counts().to_dict(),
        'completeness_distribution': df['completeness_percent'].describe().to_dict(),
        'sig_count_distribution': df['sig_count'].value_counts().to_dict(),
        'top_medications': df.nlargest(10, 'sig_count')[['drug_name_clean', 'sig_count']].to_dict('records')
    }
    
    return analytics
```

## 🚨 Important Considerations

### Medical Disclaimer
⚠️ **This data is for educational and development purposes only. Generated SIG instructions should be reviewed and validated by licensed healthcare professionals before use in patient care.**

### Data Licensing
- RxNorm data is sourced from the National Library of Medicine
- SIG instructions are algorithmically generated based on medication properties
- This dataset is provided under MIT License for research and development use

### Best Practices
1. **Always validate** medication data against current sources
2. **Include human review** for clinical applications
3. **Implement proper error handling** for missing data
4. **Keep data updated** with latest RxNorm releases
5. **Test thoroughly** before production deployment

## 🔗 Resources and Support

- **GitHub Repository:** [https://github.com/vineetdaniels2108/RxNormSIGProject](https://github.com/vineetdaniels2108/RxNormSIGProject)
- **Interactive Dashboard:** Run `streamlit run src/streamlit_dashboard.py`
- **Data Processing Scripts:** See `src/` directory for all processing tools
- **RxNorm Documentation:** [https://www.nlm.nih.gov/research/umls/rxnorm/](https://www.nlm.nih.gov/research/umls/rxnorm/)

## 📞 Contact and Contributions

For questions, issues, or contributions:
- **GitHub Issues:** [Open an issue](https://github.com/vineetdaniels2108/RxNormSIGProject/issues)
- **Email:** vineetdaniels@gmail.com

---

**🎉 Happy coding and building better healthcare applications!** 

*This comprehensive dataset can power medication lookup systems, clinical decision support tools, pharmacy management software, and medical research applications.* 