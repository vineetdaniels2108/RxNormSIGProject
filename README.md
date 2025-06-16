# 💊 RxNorm SIG Project

An intelligent medication database with automated SIG (Signa/Dosage Instructions) generation using RxNorm data.

## 🎯 Overview

This project processes RxNorm data to create a comprehensive medication database with intelligent dosage instructions. It includes **74,521+ medications** with **353,830+ SIG instructions** automatically generated based on medication properties.

## ✨ Features

- **🗄️ Complete Medication Database**: 74,521 medications from RxNorm
- **🧠 Intelligent SIG Generation**: Automated dosage instructions based on:
  - Dose form (tablets, creams, solutions, etc.)
  - Route of administration (oral, topical, ophthalmic, etc.)
  - Medication strength and drug category
- **🎛️ Interactive Dashboard**: Streamlit-powered web interface
- **🔍 Advanced Search**: Filter by term type, dose form, medication name
- **📊 Data Visualization**: Charts and statistics
- **💾 Export Capabilities**: Download filtered data and SIG instructions

## 📊 Database Statistics

| Metric | Count |
|--------|-------|
| **Total Medications** | 74,521 |
| **SIG Instructions** | 353,830 |
| **Clinical Drugs (SCD)** | 39,398 |
| **Branded Drugs (SBD)** | 23,457 |
| **Brand Names (BN)** | 11,666 |
| **Dose Forms** | 100+ types |
| **48,457 medications (65%)** with dose form data |
| **22,411 medications (30.1%)** with strength information |

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- RxNorm data files (download from [NIH](https://www.nlm.nih.gov/research/umls/rxnorm/docs/rxnormfiles.html))

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/vineetdaniels2108/RxNormSIGProject.git
   cd RxNormSIGProject
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Ready to use!**
   The main medication database (`data/medication_table_with_sigs.csv`) is included and ready to use.
   
   **Note**: Large intermediate files (`concepts.csv`, `attributes.csv`, `relationships.csv`) are excluded from GitHub due to size limits.

4. **Launch dashboard**
   ```bash
   streamlit run src/streamlit_dashboard.py
   ```

### Optional: Regenerate from source data

If you want to reprocess the data from RxNorm RRF files:

1. **Download RxNorm data**
   - Download RxNorm files from [NIH](https://www.nlm.nih.gov/research/umls/rxnorm/docs/rxnormfiles.html)
   - Extract to `~/Downloads/RxNorm_full_MMDDYYYY/rrf/`

2. **Process RxNorm data**
   ```bash
   python3 src/rxnorm_processor.py
   python3 src/create_medication_table.py
   python3 src/generate_sig_instructions.py
   ```

## 📁 Project Structure

```
RxNormSIGProject/
├── data/                              # Processed data files
│   ├── medication_table_with_sigs.csv # Main output file
│   ├── medication_table.csv           # Base medication table
│   ├── concepts.csv                   # Processed concepts
│   └── attributes.csv                 # Processed attributes
├── src/                               # Source code
│   ├── rxnorm_processor.py           # RRF file processor
│   ├── create_medication_table.py    # Table creation
│   ├── generate_sig_instructions.py  # SIG generation
│   ├── streamlit_dashboard.py        # Web dashboard
│   └── show_sig_examples.py          # Example viewer
├── requirements.txt                   # Python dependencies
└── README.md                         # This file
```

## 🎛️ Dashboard Features

### Interactive Visualizations
- **📊 Medication Distribution**: Pie charts by term type
- **📈 Dose Form Analysis**: Bar charts of most common forms
- **🧮 SIG Statistics**: Histogram of instructions per medication
- **💪 Strength Coverage**: Data completeness metrics

### Search & Filter
- **🔍 Text Search**: Find medications by name
- **🏷️ Term Type Filter**: SCD, SBD, or BN
- **💊 Dose Form Filter**: Tablets, creams, solutions, etc.

### Data Export
- **📄 CSV Download**: Filtered medication data
- **📋 SIG Export**: All dosage instructions

## 🧠 SIG Generation Logic

The system generates intelligent dosage instructions based on:

### Dose Form Rules
- **Tablets/Capsules**: "Take 1 tablet by mouth once daily"
- **Creams/Ointments**: "Apply a thin layer to affected area twice daily"
- **Solutions**: Route-specific (topical vs oral)
- **Sprays**: "Use 2 sprays in each nostril once daily"
- **Drops**: "Instill 1 drop in affected eye(s) twice daily"

### Drug Category Enhancements
- **Antibiotics**: "Take until completely finished"
- **Pain Medications**: "Take with food to prevent stomach upset"
- **Heart Medications**: "Take at the same time each day"
- **Controlled Substances**: Additional safety warnings

## 📊 Sample Data

```csv
rxcui,drug_name,term_type,dose_form,available_strength,sig_primary
91348,hydrogen peroxide 300 MG/ML Topical Solution,SCD,Sol,300 MG/ML,"Apply solution to affected area twice daily"
94406,amoxicillin 500 MG Oral Capsule [Trimox],SBD,Cap,500 MG,"Take 1 tablet by mouth once daily"
```

## 🛠️ Development

### Adding New SIG Rules

Edit `src/generate_sig_instructions.py` to add new medication categories or dosage patterns:

```python
# Example: New medication category
if 'your_drug_pattern' in drug_name:
    sigs.extend([
        "Your custom SIG instruction",
        "Alternative instruction"
    ])
```

### Customizing the Dashboard

Modify `src/streamlit_dashboard.py` to add new visualizations or filters.

## 📝 Data Sources

- **RxNorm**: National Library of Medicine (NLM)
- **File Format**: RRF (Rich Release Format)
- **Update Frequency**: Monthly releases from NIH

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🏥 Medical Disclaimer

**Important**: This tool is for educational and research purposes only. Generated SIG instructions should not be used for actual patient care without proper medical review and validation by licensed healthcare professionals.

## 👨‍💻 Author

**Vineet Daniels**
- Email: vineetdaniels@gmail.com
- GitHub: [@vineetdaniels2108](https://github.com/vineetdaniels2108)

## 🎉 Acknowledgments

- National Library of Medicine for RxNorm data
- Open source Python community
- Streamlit team for the amazing dashboard framework

---

**⭐ Star this repository if you found it helpful!** 