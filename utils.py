import pandas as pd
import json
from pathlib import Path


def make_df(json_dir: str) -> pd.DataFrame:
    file_list = list(Path(json_dir).glob("**/*.json"))
    dfs = []

    for fl in file_list:
        with open(fl) as f:
            data = pd.json_normalize(json.loads(f.read()))
        dfs.append(data)

    return pd.concat(dfs)
