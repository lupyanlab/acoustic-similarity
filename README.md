# Calculate acoustic similarity for telephone game imitations

## Setup

```bash
virtualenv --python=python3 ~/.venvs/acoustic
source ~/.venvs/acoustic
pip install numpy scipy  # make sure these work first
pip install -r requirements.txt
```

## Downloading data from S3

The first step is to configure the AWS Command Line Tools.

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
