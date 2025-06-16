import os
import pandas as pd
from pathlib import Path
import shutil

class RxNormProcessor:
    def __init__(self, downloads_dir=None, data_dir="data"):
        self.data_dir = data_dir
        # Default to user's Downloads folder if not specified
        self.downloads_dir = downloads_dir or str(Path.home() / "Downloads")
        self.rxnorm_dir = os.path.join(self.downloads_dir, "RxNorm_full_06022025", "rrf")
        self.rrf_dir = os.path.join(self.data_dir, "rrf")
        
        # Create data directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(self.rrf_dir, exist_ok=True)
    
    def copy_rrf_files(self):
        """Copy RRF files from the RxNorm rrf subdirectory."""
        if not os.path.exists(self.rxnorm_dir):
            print(f"Error: {self.rxnorm_dir} not found in Downloads folder.")
            return False
            
        print(f"Copying RRF files from {self.rxnorm_dir}...")
        try:
            # Copy all RRF files from the rrf subdirectory
            for file in os.listdir(self.rxnorm_dir):
                if file.endswith('.RRF'):
                    src_path = os.path.join(self.rxnorm_dir, file)
                    dst_path = os.path.join(self.rrf_dir, file)
                    shutil.copy2(src_path, dst_path)
            print("Copy complete!")
            return True
        except Exception as e:
            print(f"Error copying files: {str(e)}")
            return False
    
    def process_concepts(self):
        """Process the RXNCONSO.RRF file with readable column names."""
        filepath = os.path.join(self.rrf_dir, "RXNCONSO.RRF")
        
        if not os.path.exists(filepath):
            print(f"Warning: {filepath} not found.")
            return None
        
        print(f"Processing {filepath}...")
        
        # Define readable column names for RXNCONSO.RRF
        concepts_columns = [
            "rxcui", "language", "term_status", "language_unique_id", "string_type", "string_unique_id",
            "is_preferred", "atom_id", "source_aui", "source_cui", "source_dui", "source_abbreviation",
            "term_type", "source_code", "drug_name", "source_rank", "suppress_flag", "cvf_flag"
        ]
        
        # Read the file with readable column names
        df = pd.read_csv(
            filepath,
            sep='|',
            names=concepts_columns,
            dtype=str,
            index_col=False,
            engine='python'
        )
        
        print(f"Loaded {len(df)} concept records")
        print("Sample of processed concepts:")
        print(df[['rxcui', 'drug_name', 'term_type', 'source_abbreviation']].head())
        
        # Save as CSV for easier reading
        output_path = os.path.join(self.data_dir, "concepts.csv")
        df.to_csv(output_path, index=False)
        print(f"Processed concepts saved to {output_path}")
        
        return df
    
    def process_attributes(self):
        """Process the RXNSAT.RRF file with readable column names."""
        filepath = os.path.join(self.rrf_dir, "RXNSAT.RRF")
        
        if not os.path.exists(filepath):
            print(f"Warning: {filepath} not found.")
            return None
        
        print(f"Processing {filepath}...")
        
        # Define readable column names for RXNSAT.RRF
        attributes_columns = [
            "rxcui", "language_unique_id", "string_unique_id", "atom_id", "source_type",
            "source_code", "attribute_id", "source_attribute_id", "attribute_name",
            "source_abbreviation", "attribute_value", "suppress_flag", "cvf_flag"
        ]
        
        # Read the file with readable column names
        df = pd.read_csv(
            filepath,
            sep='|',
            names=attributes_columns,
            dtype=str,
            index_col=False,
            engine='python'
        )
        
        print(f"Loaded {len(df)} attribute records")
        print("Sample of processed attributes:")
        print(df[['rxcui', 'attribute_name', 'attribute_value', 'source_abbreviation']].head())
        
        # Save as CSV for easier reading
        output_path = os.path.join(self.data_dir, "attributes.csv")
        df.to_csv(output_path, index=False)
        print(f"Processed attributes saved to {output_path}")
        
        return df
    
    def process_relationships(self):
        """Process the RXNREL.RRF file with readable column names."""
        filepath = os.path.join(self.rrf_dir, "RXNREL.RRF")
        
        if not os.path.exists(filepath):
            print(f"Warning: {filepath} not found.")
            return None
        
        print(f"Processing {filepath}...")
        
        # Define readable column names for RXNREL.RRF
        rel_columns = [
            "rxcui1", "rxaui1", "stype1", "rel", "rxcui2", "rxaui2", "stype2",
            "rela", "rui", "srui", "source_abbreviation", "sl", "rg", "dir", "suppress_flag", "cvf_flag"
        ]
        
        # Read the file with readable column names
        df = pd.read_csv(
            filepath,
            sep='|',
            names=rel_columns,
            dtype=str,
            index_col=False,
            engine='python'
        )
        
        print(f"Loaded {len(df)} relationship records")
        print("Sample of processed relationships:")
        print(df[['rxcui1', 'rel', 'rxcui2', 'source_abbreviation']].head())
        
        # Save as CSV for easier reading
        output_path = os.path.join(self.data_dir, "relationships.csv")
        df.to_csv(output_path, index=False)
        print(f"Processed relationships saved to {output_path}")
        
        return df
    
    def cleanup(self):
        """Clean up temporary RRF files."""
        if os.path.exists(self.rrf_dir):
            shutil.rmtree(self.rrf_dir)
            print("Cleaned up temporary files.")

def main():
    processor = RxNormProcessor()
    
    # Copy RRF files from the rrf subdirectory
    if not processor.copy_rrf_files():
        print("Failed to copy RRF files. Exiting.")
        return
    
    # Process files
    print("\nProcessing RxNorm files...")
    concepts_df = processor.process_concepts()
    attributes_df = processor.process_attributes()
    relationships_df = processor.process_relationships()
    
    # Clean up temporary files
    processor.cleanup()
    
    print("\nDone! Files have been processed with readable column names.")
    print(f"Processed files are available in the '{processor.data_dir}' directory.")

if __name__ == "__main__":
    main() 