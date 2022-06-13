import pandas as pd
import json
import glob
from pathlib import Path


def make_df(json_dir: str) -> pd.DataFrame:
    file_list = list(Path(json_dir).glob("**/*.json"))
    dfs = []

    for fl in file_list:
        with open(fl) as f:
            data = pd.json_normalize(json.loads(f.read()))
        dfs.append(data)

    return pd.concat(dfs)


def find_existing_files(prefix):
    list_of_files = glob.glob(f"{prefix}*.json")
    existing_object_nrs = [
        file_name.split("/")[-1].strip(".json") for file_name in list_of_files
    ]
    return existing_object_nrs
