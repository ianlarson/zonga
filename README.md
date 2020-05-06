This file quickly creates EC2 instances from the command line.

Usage example: "zonga.py [profile_name]"
Add a "-t" at the end if you want to terminate the instances that were just created (for debugging purposes).

zonga.config should be updated with your specific AWS objects for creation.

REQUIREMENTS:

boto3
python3

python3 must be in /usr/local/bin (or you can adjust the path manually at the top of the script)

If you don't have python3 installed(type python3 to find out):

Install homebrew:
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install.sh)"

Install python 3.8:
brew install python@3.8

