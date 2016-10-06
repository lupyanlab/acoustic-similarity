# Calculate acoustic similarity for telephone game

## Quickstart

```bash
git clone https://github.com/lupyanlab/acoustic-similarity.git
cd acoustic-similarity
virtualenv --python=python3 ~/.venvs/acoustic
source ~/.venvs/acoustic
pip install -r requirements.txt
aws configure  # prompts for AWS Access Key Id and Secret Access Key
invoke --list  # list all available tasks
inv download   # run invoke task `download`
```

## Setup

After cloning the repo, create an isolated virtualenv for installing the
necessary packages. By convention I store my virtualenvs in `~/.venvs`.

```bash
virtualenv --python=python3 ~/.venvs/acoustic
source ~/.venvs/acoustic
```

With the virtualenv activated, now install the necessary packages.
Installing numpy and scipy is always scary. Do these first, and then
install the rest of the requirements.

```bash
pip install numpy scipy  # make sure these work first
pip install -r requirements.txt
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
