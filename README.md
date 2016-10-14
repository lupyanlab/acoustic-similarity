# Calculate acoustic similarity for telephone game

How does the fidelity of verbal imitation change over generations of repetition?

![](/definitions.png)

## Quickstart

    git clone https://github.com/lupyanlab/acoustic-similarity.git
    cd acoustic-similarity
    invoke --list               # list available tasks
    inv download compare_sounds # run invoke tasks

## Setup

After cloning the repo, create an isolated virtualenv for installing the
necessary packages. The `acousticsim` package has some heavy dependencies.
Best thing to do is create a `conda` environment.

    conda create -n acoustic
    source activate acoustic              # activate the new environment
    conda install numpy scipy matplotlib  # install the hard stuff
    pip install -r requirements.txt       # install the easy stuff

## Downloading data from S3

Once everything is installed, you need to configure the AWS
Command Line Tools so that you can get the data.

    aws configure

Then you can download the data as an invoke task.

    inv download

If you have multiple AWS profiles, you can name the one you want to use
in the configure step as well as the download step.

    aws --profile=myprofile configure
    inv download --profile=myprofile

## Comparing sounds with acousticsim

The invoke task `compare` is for using acousticsim to compare two sounds.
The arguments x and y can be specified to test out individual comparisons.

    inv compare_sounds -x path/to/sound1.wav -y path/to/sound2.wav

If you are comparing sounds that were downloaded via the `download` invoke task (i.e., sounds that are in the "data/sounds" directory and named with unique integer ids, like "data/sounds/100.wav"), then you can just specify the ids to compare.

    inv compare_sounds -x 34 -y 101

Comparisons can also happen from specific structures within the telephone
game data. Here's how to calculate linear similarity along all branches.

    inv compare_sounds --type linear

The results are saved as "data/{type}.csv", so the results from the linear
comparison are "data/linear.csv". If no type is specified, all types will
be calculated.

    inv compare_sounds

## Comparing words with Phonological Corpus Tools

## Getting subjective judgments of similarity
