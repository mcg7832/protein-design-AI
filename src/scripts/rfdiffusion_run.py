import os
from rfdiffusion_pipeline import process_protein, setup_folder, visual_comparison, find_score_file

root_dir = "/home/ubuntu"
os.chdir(root_dir)
setup_folder(root_dir)

# user must change below: (1) PDB code & (2) amino acid positions
result=process_protein('7SH6', "[20-30/157-163/20-40/157-163/20-30]")
print(result)

# user must change PDB code below to match the PDB code above
pdb_code_native='7SH6'
pdb_native=f"./work_flow/native_proteins/{pdb_code_native.upper()}.pdb"
pdb_artificial=find_score_file(pdb_code_native)
print(pdb_native)
print(pdb_artificial)
visual_comparison(pdb_native,pdb_artificial)