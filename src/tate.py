def tate_find_results(data, query, columns=None):
    if columns:
        return data[
            data[[*columns]].apply(
                lambda row: row.astype(str).str.contains(query, case=False).any(),
                axis=1,
            )
        ]
    res = data[
        data.apply(
            lambda row: row.astype(str).str.contains(query, case=False).any(), axis=1
        )
    ]
    print(f"Found {res.shape[0]} results.")
    return res
