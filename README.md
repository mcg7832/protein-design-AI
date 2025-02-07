# S2DS 2024 Polyploy Project

Authors: Brian Nathan, Aleksandra (Ola) Olszewska, Julia Frankenberg Garcia, Micon Garvilles and Enrico Andriolo

This project was developed as part of the Science 2 Data Science programme, for our project partner Polyploy. Here you can find different inference pipelines for de novo protein design, with motif scaffolding. More information on the biology and different pipelines can be found in reports: report.txt.


## Pipelines list
A few different pipelines have been developed to be run in different virtual machines as follows: 

For running on GoogleColab: 
* Evodiff pipeline minimum viable model (notebooks/evodiff.ipynb)
* Rfdiffusion pipeline minimum viable model (notebooks/rfdiffusion.ipynb)
* Rfdiffusion pipeline tutorial (notebooks/rfdiffusion_tutorial.ipynb): with detailed explanations and to be used as a learning material

For running as python scripts (optimized for AWS): 
* Rfdiffusion pipeline (in src/scripts/rfdiffusion_pipeline.py and rfdiffudion_run.py)
* Chatbot (src/scripts/dynamic_chatbot_RFdiffusion.py)


## Additional branches
There is an additonal branches with some work in progress (work-in-progress), such as: 
* Evodiff py scripts (evodiff1.py, evodiff_julia.py, omegafold_func.py, not complete, may need some debugging)


## Installing libraries and preparing environments

* For running google colabs installation of libraries are done within notebooks and nothing from this repo is required
* For running python scripts: 
    * RFdiffusion Pipeline and Generative AI chatbot:
         1. Open terminal in VS code <br />
         2. Confirm correct SSH key <br />
            ```chmod 400 poly.pem``` <br />
            
        4. Connect to EC2 instance (Amazon Cloud computer with GPU), main user: <br />
            ```ssh -i "poly.pem" ubuntu@ec2-3-86-218-51.compute-1.amazonaws.com ``` <br />
           
        6. Activate environment for RFdiffusion pipeline and generative AI <br />
            ```conda activate poly``` <br />
  
        7. Stop EC2 instance when idle <br />
           ```exit``` <br />


#==================================================<br />
## Setup GPU & AWS-CLI in AWS cloud compute <br />
#==================================================<br />

### I. Connect to AWS EC2 instance: <br />

* 1. Save .pem key in the working folder and confirm in VS code terminal <br />
```chmod 400 poly.pem``` <br /> 

* 2. Connect to your EC2 instance (cloud computer with GPUs) run the comand <br />
```ssh -i "poly.pem" ubuntu@ec2-3-86-218-51.compute-1.amazonaws.com``` <br />

      * Check GPU <br />
      ```nvidia-smi``` <br />
      * If error says 'Command 'nvidia-smi' not found' proceed GPU setup in AWS below: <br />

      * Check specks <br />
      ```nvcc --version``` TU104GL [Tesla T4], amazon EC2 G4 Instances have up to 4 NVIDIA T4 GPUs <br /> 
      ```lsb_release -a``` <br />
      ```gcc --version``` gcc (Ubuntu 13.2.0-23ubuntu4) 13.2.0 <br />
      ```uname -m``` Check architecture (x86_64) <br />

### II. Setup GPU in AWS <br />

* 1. Setup useful tools in linux environment of AWS <br />
```sudo apt-get install python3.10 #is python 3.12.3 at the moment``` <br />

* 2. Install nvidia drivers <br />
```sudo apt install nvidia-driver-550 nvidia-dkms-550``` <br />

* 3. Donwload and install CUDA toolkit from NVIDIA <br />
```wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2404/x86_64/cuda-keyring_1.1-1_all.deb``` <br />
```sudo dpkg -i cuda-keyring_1.1-1_all.deb``` <br />
```sudo apt-get update``` <br />
```sudo apt-get -y install cuda-toolkit-12-5``` <br />
```sudo apt install nvidia-dkms-550``` <br />
```sudo apt install nvidia-driver-550``` <br />
```sudo apt install ec2-api-tools```<br />

* 5. Install linux modules <br />
```sudo apt-get install linux-modules-nvidia-550-$(uname -r)``` <br />
```sudo apt-cache policy linux-modules-nvidia-550-$(uname -r)``` <br />
```sudo apt install nvidia-dkms-550``` <br />
```sudo apt install nvidia-driver-550``` <br />
```sudo apt install ec2-api-tools``` <br />
```sudo apt install linux-headers-$(uname -r)``` <br />
```sudo apt-get install linux-modules-nvidia-550-$(uname -r)``` <br />
```sudo apt install nvidia-dkms-550``` <br />
```sudo apt install nvidia-driver-550``` <br />
```dpkg --list | grep linux-image``` #linux-image-6.8.0-1010-aws <br /> 
```sudo update-grub``` <br />

* final step <br />
```sudo reboot``` <br />

* NVML library version: 550.90 <br />
```nvidia-smi``` <br />

### III. Setup conda environment <br />
* Install conda  <br />
```echo getting conda```  <br />
```curl https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -o miniconda.sh``` <br />
```chmod +x miniconda.sh```  <br />
```./miniconda.sh ``` <br />
```source ~/.bashrc```  <br />

* check conda source <br />
```cd /home/ubuntu/miniconda3/bin``` <br />
```nano ~/.bashrc``` <br />
```export PATH="/home/username/miniconda3/bin:$PATH" ``` then save file <br />

* create environment called 'poly' <br />
```conda create -n poly python=3.10``` <br />
```conda init``` <br />
```conda activate poly``` <br />

* install pytorch  <br />
```conda install pytorch torchvision torchaudio pytorch-cuda=12.1 -c pytorch -c nvidia```  <br />
```python```  <br />
```import torch``` test <br />

### IV. AWS-CLI setup - connect EC2 instance with Amazon Bedrock <br />

* https://boto3.amazonaws.com/v1/documentation/api/latest/guide/quickstart.html <br />
```pip install boto3``` <br />
```sudo apt install unzip``` <br />

* https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html  <br />
```curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"```  <br />

```/usr/local/bin/aws --version```  <br />
```aws-cli/2.17.13 Python/3.11.9 Linux/6.8.0-1010-aws exe/x86_64.ubuntu.24```  <br />

* change source of aws <br />
```source ~/.bashrc``` <br />
```nano ~/.bashrc``` <br />
```export PATH="/usr/local/bin:$PATH"``` <br />
```source ~/.bashrc``` <br />

### 4. Setup credentials in AWS-CLI <br />
```aws configure``` <br />

      * aws_access_key_id = YOUR_ACCESS_KEY <br />
      * aws_secret_access_key = YOUR_SECRET_KEY <br />
      * region=us-east-1 <br />
      * write jason for default file 

```~/.aws/config``` save credentials file to <br />


#==================================================<br />
End of AWS cloud compute set up <br />
#==================================================<br />

## Repo Structure: 


```
├── README.md          <- The top-level README for developers using this project.
├── data
│   ├── external       <- PDB files downloaded from RSCB should be stored here.
│   ├── interim        <- Intermediate data that has been transformed. e.g. fastA files, intermediate PBD files etc.
│   └── processed      <- The final output PBD files. 
│   
│
├── notebooks          <- Jupyter notebooks. 
│                      
│
├── reports            <- state-of-the-art and summary report
│ 
│
├── requirements.txt   <- The requirements file for reproducing the analysis environment in a conda environment
│                       
│
├── src                <- Source code for use in this project.
    ├── scripts      
        └── working python scripts
```

