# Calculate acoustic similarity for telephone game

## Quickstart

```bash
git clone https://github.com/lupyanlab/acoustic-similarity.git && cd acoustic-similarity
conda create -n acoustic
source activate acoustic
conda install numpy scipy matplotlib
pip install -r requirements.txt
aws configure  # prompts for AWS Access Key Id and Secret Access Key
invoke --list  # list all available tasks
inv download   # run invoke task `download`
```

## Setup

After cloning the repo, create an isolated virtualenv for installing the
necessary packages. The acousticsim package has some heavy dependencies.
Best thing to do is create a conda environment.

```bash
conda create -n acoustic
source activate acoustic              # activate the new environment
conda install numpy scipy matplotlib  # install the hard stuff
pip install -r requirements.txt       # install the easy stuff
```

## Downloading data from S3

Once everything is installed, you need to configure the AWS
Command Line Tools so that you can get the data.

```bash
aws configure
```

Then you can download the data as an invoke task.

```bash
inv download
```

If you have multiple AWS profiles, you can name the one you want to use
in the configure step as well as the download step.

```bash
aws --profile=myprofile configure
inv download --profile=myprofile
```
