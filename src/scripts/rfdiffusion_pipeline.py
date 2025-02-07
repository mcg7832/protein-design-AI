# Check and Setup work dir #cd /home/ubuntu/output
# import packages
import glob
import os
import re
import requests
import subprocess
import time


def setup_folder(root_dir):  

    # Define the base folder in AWS
    base_folder = f'{root_dir}/work_flow'

    # Define the subfolders
    subfolders = ['RFdiffusion_output', 'mpnn_output', 'omegafold_output', 'native_proteins']

    # Check if the base folder already exists
    if not os.path.exists(base_folder):
        # Create the base folder
        os.makedirs(base_folder, exist_ok=True)

        # Create the subfolders
        for subfolder in subfolders:
            os.makedirs(os.path.join(base_folder, subfolder), exist_ok=True)

        print("Folder structure created successfully.")
    else:
        print("The folder 'work_flow' already exists.")


def run_rfdiffusion(input_file: str, output_dir_and_prefix: str, number_proteins: int,
                    residues: str = None, guide_scale: int = None,
                    substrate_name: str = None, model_weights: str = None,
                    contig_length: str = None, guiding_potentials: str = None):
    """
    If the name of the substrate is specified (e.g. LLK), it must be present in the input pdb file.
    """
    if input_file is not None and not os.path.exists(input_file):
      raise ValueError("Input file does not exist")

    # Input checks
    if residues is None and guide_scale is not None:
        raise ValueError("Please fill in residues")

    # Create function call
    sh_call = "./RFdiffusion/scripts/run_inference.py"
    #sh_call = "run_inference.py"
    sh_call += " inference.output_prefix=" + output_dir_and_prefix
    sh_call += " inference.num_designs=" + str(number_proteins)

    # Optional arguments
    if input_file != "":
        sh_call += " inference.input_pdb=" + input_file

    if residues is not None:
        # contigmap.contigs line must be in single quotes
        sh_call += " 'contigmap.contigs=" + residues + "'"

    if contig_length is not None:
        sh_call += " contigmap.length=" + contig_length

    if guide_scale is not None:
        sh_call += " potentials.guide_scale=" + str(guide_scale)

    if guiding_potentials is not None:
        # potentials.guiding_potentials line must be in single quotes
        # the guiding_potentials must be in double quotes
        # sh_call += " " + repr('potentials.guiding_potentials=["type:substrate_contacts,s:1,r_0:8,rep_r_0:5.0,rep_s:2,rep_r_min:1"]')
        sh_call += " 'potentials.guiding_potentials=[" + '"' + guiding_potentials + '"' + "]'"

    if substrate_name is not None:
        sh_call += " potentials.substrate=" + substrate_name

    if model_weights is not None:
        sh_call += " inference.ckpt_override_path=" + model_weights

    print("Running RFdiffusion with call", sh_call)

    os.system(sh_call)


def run_protein_mpnn(input_file: str, output_dir: str,
                    num_seq_per_target: int = 10, #default
                    sampling_temp: str = "0.1", #default
                    seed: int = 0 , #default
                    batch_size: int = 1, #default
                    model_name: str = "v_48_020"): #default

    # Check if input file exists
    if not os.path.exists(input_file):
        raise ValueError("input_file does not exist")

    sh_call= "python ./ProteinMPNN/protein_mpnn_run.py"
    sh_call+= " --pdb_path " + input_file
    sh_call+= " --out_folder " + output_dir
    sh_call+= " --num_seq_per_target " + str(num_seq_per_target)
    # Must be a string, can contain multiple temps, e.g.  "0.1 0.2"
    sh_call+= " --sampling_temp " + '"' + sampling_temp + '"'
    sh_call+= " --seed " + str(seed)
    sh_call+= " --batch_size " + str(batch_size)
    sh_call+= " --model_name " + model_name

    print("Running ProteinMPNN with call", sh_call)

    os.system(sh_call)


def run_omegafold(input_file: str, output_file: str):

    if not os.path.exists(input_file):
        raise ValueError("input_file does not exist")

    sh_call= "omegafold"
    sh_call+= " " + input_file
    sh_call+= " " + output_file


    print("Running omegafold with call", sh_call)

    os.system(sh_call)


def download_pdb(pdb_code, target_directory='./work_flow/native_proteins'):
    # Ensure the target directory exists
    os.makedirs(target_directory, exist_ok=True)

    # Construct the full path for the PDB file
    pdb_file_path = os.path.join(target_directory, f"{pdb_code.upper()}.pdb")

    # URL for downloading the PDB file
    url = f"https://files.rcsb.org/download/{pdb_code.upper()}.pdb"

    # Request the PDB file
    response = requests.get(url)

    if response.status_code == 200:
        # Write the content to the PDB file
        with open(pdb_file_path, 'wb') as f:
            f.write(response.content)
        print(f"PDB file {pdb_code.upper()} downloaded successfully to {pdb_file_path}")
    else:
        print(f"Failed to download PDB file {pdb_code.upper()}. Status code: {response.status_code}")


def extract_scores(ref_protein, generated_protein): #it takes as inputs the path of the two pdb files
    ref_protein_abs = os.path.abspath(ref_protein)
    generated_protein_abs = os.path.abspath(generated_protein)

    # Run the TMalign command
    tmalign_command = ["./TMalign", ref_protein_abs, generated_protein_abs]
    result = subprocess.run(tmalign_command, capture_output=True, text=True)

    if result.returncode == 0:
        output = result.stdout

        # Extract TM-scores from the output using regex
        tm_scores = re.findall(r"TM-score=\s+([\d.]+)", output)
        if len(tm_scores) >= 2:
            tm_score_1 = float(tm_scores[0])
            tm_score_2 = float(tm_scores[1])
        else:
            print("TM-scores not found in the output.")
            return None

        # Extract RMSD score from the output using regex
        rmsd_score_match = re.findall(r"RMSD=\s+([\d.]+)", output)
        if rmsd_score_match:
            rmsd_score = float(rmsd_score_match[0])
        else:
            print("RMSD score not found in the output.")
            return None

        return tm_score_1, tm_score_2, rmsd_score
    else:
        print(f"Error running TMalign for {generated_protein}. Return code: {result.returncode}")
        print(result.stderr)
        return None

#we will need this function to isolate the correct pdb file from the files that omegafold will give as output
def find_score_file(pdb_code):
    directory = f'./work_flow/omegafold_output/{pdb_code}'
    score_file_prefix = f'{pdb_code}_score'

    for filename in os.listdir(directory):
        if filename.startswith(score_file_prefix):
            return os.path.join(directory, filename)

    return None


# Main pipeline (RFdiffusion using PDB code + ProteinMPNN + OmegaFold)
def process_protein(pdb_code, residues_input):

    tic = time.time()

    download_pdb(pdb_code)
    # Ensure the pdb_code is in uppercase
    pdb_code_upper = pdb_code.upper()

    # Construct the input and output paths
    RF_input = f"./work_flow/native_proteins/{pdb_code_upper}.pdb"
    RF_output = f"./work_flow/RFdiffusion_output/{pdb_code}/{pdb_code}_scaffold"

    # Check if the input file exists
    if not os.path.exists(RF_input):
        raise ValueError(f"Input file {RF_input} does not exist")

    # Run RFdiffusion
    run_rfdiffusion(
        input_file=RF_input,
        output_dir_and_prefix=RF_output,
        number_proteins=1,
        residues=residues_input
    )

    # Run ProteinMPNN
    run_protein_mpnn(
        input_file=f"./work_flow/RFdiffusion_output/{pdb_code}/{pdb_code}_scaffold_0.pdb",
        output_dir=f"./work_flow/mpnn_output/{pdb_code}",
        num_seq_per_target=1,
        sampling_temp="0.1",
        seed=0,
        batch_size=1,
        model_name="v_48_020"
    )

    # Run OmegaFold
    run_omegafold(
        input_file=f"./work_flow/mpnn_output/{pdb_code}/seqs/{pdb_code}_scaffold_0.fa",
        output_file=f"./work_flow/omegafold_output/{pdb_code}"
    )

    #now we change the names in the omegafold folder such that in the name there is information about the score:
    #we perform this task in 4 steps
    # 1. Define the folder containing the .pdb files
    folder_path = f'./work_flow/omegafold_output/{pdb_code}'

    # 2. List all files in the folder
    files = os.listdir(folder_path)

    # 3. Define a regular expression to extract the relevant parts of the filename
    pattern = re.compile(r"([a-zA-Z0-9]+)_.*score=([\d.]+)")

    # 4. Process each file
    for filename in files:
       if filename.endswith('.pdb'):
           match = pattern.search(filename)
           if match:
                alphanumeric_part = match.group(1)
                score_part = match.group(2)
                new_filename = f"{alphanumeric_part}_score_{score_part}.pdb"
                old_file = os.path.join(folder_path, filename)
                new_file = os.path.join(folder_path, new_filename)
                os.rename(old_file, new_file)
                print(f"Renamed '{filename}' to '{new_filename}'")


    #now let's print the metrics between the output of the first and third steps of the pipeline
    output_first_step=f'./work_flow/RFdiffusion_output/{pdb_code}/{pdb_code}_scaffold_0.pdb'
    output_third_step=find_score_file(pdb_code)

    toc = time.time()
    print("It took {:.2f} minutes to run RFdiffusion + ProteinMPNN + OmegaFold".format((toc - tic)/60))

    return extract_scores(output_first_step, output_third_step)

# TM and LM score metric to determine quality of newly designed protein and compare it from native protein
def visual_comparison(ref_protein, generated_protein): #it takes as inputs the path of the two pdb files
    ref_protein_abs = os.path.abspath(ref_protein)
    generated_protein_abs = os.path.abspath(generated_protein)

    # Run the TMalign command
    tmalign_command = ["./TMalign", ref_protein_abs, generated_protein_abs]
    result = subprocess.run(tmalign_command, capture_output=True, text=True)

    if result.returncode == 0:
      output = result.stdout
      print(output)
    else:
      print(f"Error running TMalign for {generated_protein}. Return code: {result.returncode}")
      print(result.stderr)



