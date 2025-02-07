import logging
import json
import boto3
import os
import requests
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def setup_folder(root_dir):
    # Define the base folder in AWS
    base_folder = os.path.join(root_dir, 'work_flow')

    # Define the subfolders
    subfolders = ['RFdiffusion_output', 'mpnn_output', 'omegafold_output', 'native_proteins']

    # Check if the base folder already exists
    if not os.path.exists(base_folder):
        # Create the base folder
        os.makedirs(base_folder, exist_ok=True)

        # Create the subfolders
        for subfolder in subfolders:
            os.makedirs(os.path.join(base_folder, subfolder), exist_ok=True)

        print("work-flow folder structure created successfully.")
    else:
        print("The folder 'work_flow' already exists.")

#TODO: We would like to add a function that can parse the output work_flow folder for previously-created files

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
        return f"PDB file {pdb_code.upper()} downloaded successfully to {pdb_file_path}"
    else:
        return f"Failed to download PDB file {pdb_code.upper()}. Status code: {response.status_code}. Please verify PDB code is correct and exists in RCSB database."

#NOTE: We have swapped the order of "residues_backbone" (formerly residues) and number_proteins, so that we can hard-code number_proteins
def run_rfdiffusion(input_file: str, output_dir_and_prefix: str, residues_backbone: str,
                    number_proteins: int = 1, guide_scale: int = None, substrate_name: str = None, model_weights: str = None,
                    contig_length: str = None, guiding_potentials: str = None):
    if input_file is not None and not os.path.exists(input_file):
        raise ValueError("Input file does not exist")
    if residues_backbone is None and guide_scale is not None:
        raise ValueError("Please fill in residues for the backbone")
    sh_call = "./models/RFdiffusion/scripts/run_inference.py"
    sh_call += " inference.output_prefix=" + output_dir_and_prefix
    sh_call += " inference.num_designs=" + str(number_proteins)
    if input_file != "":
        sh_call += " inference.input_pdb=" + input_file
    if residues_backbone is not None:
        sh_call += " 'contigmap.contigs=" + residues_backbone + "'"
    if contig_length is not None:
        sh_call += " contigmap.length=" + contig_length
    if guide_scale is not None:
        sh_call += " potentials.guide_scale=" + str(guide_scale)
    if guiding_potentials is not None:
        sh_call += " 'potentials.guiding_potentials=[" + '"' + guiding_potentials + '"' + "]'"
    if substrate_name is not None:
        sh_call += " potentials.substrate=" + substrate_name
    if model_weights is not None:
        sh_call += " inference.ckpt_override_path=" + model_weights
    print("Running RFdiffusion with call", sh_call)
    os.system(sh_call)

def stream_messages(bedrock_client, model_id, messages, tool_config):
    logger.info("Streaming messages with model %s", model_id)

    response = bedrock_client.converse_stream(
        modelId=model_id,
        messages=messages,
        toolConfig=tool_config
    )

    stop_reason = ""
    message = {}
    content = []
    message['content'] = content
    text = ''
    tool_use = {}

    for chunk in response['stream']:
        if 'messageStart' in chunk:
            message['role'] = chunk['messageStart']['role']
        elif 'contentBlockStart' in chunk:
            tool = chunk['contentBlockStart']['start']['toolUse']
            tool_use['toolUseId'] = tool['toolUseId']
            tool_use['name'] = tool['name']
        elif 'contentBlockDelta' in chunk:
            delta = chunk['contentBlockDelta']['delta']
            if 'toolUse' in delta:
                if 'input' not in tool_use:
                    tool_use['input'] = ''
                tool_use['input'] += delta['toolUse']['input']
            elif 'text' in delta:
                text += delta['text']
                print(delta['text'], end='')
        elif 'contentBlockStop' in chunk:
            if 'input' in tool_use:
                tool_use['input'] = json.loads(tool_use['input'])
                content.append({'toolUse': tool_use})
                tool_use = {}
            else:
                content.append({'text': text})
                text = ''

        elif 'messageStop' in chunk:
            stop_reason = chunk['messageStop']['stopReason']

    return stop_reason, message

def process_tool_use(tool_name, tool_input):
    if tool_name == 'download_pdb':
        pdb_code = tool_input['pdb_code']
        target_directory = tool_input.get('target_directory', './work_flow/native_proteins')
        return download_pdb(pdb_code, target_directory)
    elif tool_name == 'run_rfdiffusion':
        input_file = tool_input['input_file']
        output_dir_and_prefix = tool_input['output_dir_and_prefix']
        residues_backbone = tool_input['residues_backbone']
        number_proteins = tool_input['number_proteins']
        guide_scale = tool_input.get('guide_scale')
        substrate_name = tool_input.get('substrate_name')
        model_weights = tool_input.get('model_weights')
        contig_length = tool_input.get('contig_length')
        guiding_potentials = tool_input.get('guiding_potentials')
        run_rfdiffusion(
            input_file, output_dir_and_prefix, residues_backbone, number_proteins, guide_scale,
            substrate_name, model_weights, contig_length, guiding_potentials
        )
        return "RFdiffusion run completed successfully."

def main():
    setup_folder(os.getcwd())

    model_id = "anthropic.claude-3-haiku-20240307-v1:0"

    try:
        bedrock_client = boto3.client(service_name='bedrock-runtime')

        messages = []
        tool_config = {
            "tools": [
                {
                    "toolSpec": {
                        "name": "download_pdb",
                        "description": "Download, from the RCSB PDB database, the PDB file of the protein identified by its PDB code. Examples of PDB codes are '5AN7' and '6KUS'.",
                        "inputSchema": {
                            "json": {
                                "type": "object",
                                "properties": {
                                    "pdb_code": {
                                        "type": "string",
                                        "description": "The PDB code of the protein to download."
                                    },
                                    "target_directory": {
                                        "type": "string",
                                        "description": "The directory where the PDB file will be saved.",
                                        "default": "./work_flow/native_proteins"
                                    }
                                },
                                "required": ["pdb_code"]
                            }
                        }
                    }
                },
                {
                    "toolSpec": {
                        "name": "run_rfdiffusion",
                        "description": "Execute the RFdiffusion model to generate protein designs.",
                        "inputSchema": {
                            "json": {
                                "type": "object",
                                "properties": {
                                    "input_file": {
                                        "type": "string",
                                        "description": "Path to the input PDB file."
                                    },
                                    "output_dir_and_prefix": {
                                        "type": "string",
                                        "description": "Output directory and prefix for the results.",
                                        "default": "./work_flow/RFdiffusion_output"
                                    },
                                    "residues_backbone": {
                                        "type": "string",
                                        "description": "Residues that specify how to build the backbone, enclosed in square brackets.  If there are multiple residues, they should be separated by /.  Examples are: [A20-30] which has one residue, [20-30/157-163] which has 2 residues, [10-100/A1083-1085/20-40/A1040-1051/25-61/B1180-1080/10-10] which has 5 residues."
                                    },
                                    "number_proteins": {
                                        "type": "integer",
                                        "description": "Number of protein designs to generate.",
                                        "default": "1"
                                    },
                                    "guide_scale": {
                                        "type": "integer",
                                        "description": "Guide scale for the potentials.",
                                        "default": "None"
                                    },
                                    "substrate_name": {
                                        "type": "string",
                                        "description": "Name of the substrate.",
                                        "default": "None"
                                    },
                                    "model_weights": {
                                        "type": "string",
                                        "description": "Path to the model weights file.",
                                        "default": "None"
                                    },
                                    "contig_length": {
                                        "type": "string",
                                        "description": "Contig length to be used.",
                                        "default": "None"
                                    },
                                    "guiding_potentials": {
                                        "type": "string",
                                        "description": "Guiding potentials to be used.",
                                        "default": "None"
                                    }
                                },
                                "required": ["input_file", "output_dir_and_prefix", "residues_backbone"]
                            }
                        }
                    }
                }
            ]
        }

        while True:
            user_input = input("User message to chatbot: ")
            if user_input.lower() in ["quit","leave chat"]:
                print("Goodbye!")
                break

            messages.append({
                "role": "user",
                "content": [{"text": user_input}]
            })

            stop_reason, message = stream_messages(bedrock_client, model_id, messages, tool_config)
            messages.append(message)

            if stop_reason == "tool_use":
                for content in message['content']:
                    if 'toolUse' in content:
                        tool = content['toolUse']
                        tool_name = tool['name']
                        tool_input = tool['input']
                        try:
                            result = process_tool_use(tool_name, tool_input)
                            tool_result = {
                                "toolUseId": tool['toolUseId'],
                                "content": [{"text": result}]
                            }
                        except Exception as err:
                            tool_result = {
                                "toolUseId": tool['toolUseId'],
                                "content": [{"text": str(err)}],
                                "status": 'error'
                            }

                        tool_result_message = {
                            "role": "user",
                            "content": [
                                {
                                    "toolResult": tool_result
                                }
                            ]
                        }
                        messages.append(tool_result_message)

                        stop_reason, message = stream_messages(bedrock_client, model_id, messages, tool_config)
                        messages.append(message)

    except ClientError as err:
        message = err.response['Error']['Message']
        logger.error("A client error occurred: %s", message)
        print("A client error occurred: " + format(message))

if __name__ == "__main__":
    main()
