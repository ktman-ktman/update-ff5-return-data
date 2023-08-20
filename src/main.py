#!/usr/bin/env python3

import datetime
import os
import zipfile
from urllib.parse import urljoin, urlparse
from urllib.request import urlopen, urlretrieve

import pandas as pd

from params import (
    ASIA_PACIFIC_EXCLUDE_JAPAN_5F,
    ASIA_PACIFIC_EXCLUDE_JAPAN_MOMF,
    BASE_URL,
    EMERGING_MARKETS_5F,
    EMERGING_MARKETS_MOMF,
    EU_5F,
    EU_MOMF,
    JAPAN_5F,
    JAPAN_MOMF,
    NORTH_AMERICA_5F,
    NORTH_AMERICA_MOMF,
)


def download_file(download_url, save_dirn: str) -> None:
    # ファイル名から
    data = urlopen(download_url).read()
    with open(save_dirn, mode="wb") as f:
        f.write(data)


def read_file_data(save_dirn: str) -> pd.DataFrame:
    if not os.path.isfile(save_dirn):
        raise FileExistsError(f"There is no file: {save_dirn}")

    header = save_dirn.split("/")[-1]
    header = header.split("_CSV")[0]
    csv_filename = f"{header}.csv"
    if "Mom" in header:
        csv_filename = csv_filename.replace("Mom", "MOM")
    with zipfile.ZipFile(save_dirn) as z:
        for filename_i in z.namelist():
            if filename_i == csv_filename:
                finished_flag = False
                data_l = list()
                with z.open(filename_i, mode="r") as f:
                    for line in f:
                        if finished_flag:
                            break

                        row = line.decode("utf-8").rstrip()
                        if row.startswith(",Mkt-RF") or row.startswith(",WML"):
                            data_start_flag = True
                            coln_l = [x.strip() for x in row.rstrip().split(",")]
                            coln_l[0] = "DATEYM"
                            for line in f:
                                row2 = line.decode("utf-8").rstrip()
                                if row2 == "":
                                    finished_flag = True
                                    break
                                else:
                                    data = [x.strip() for x in row2.split(",")]
                                    data_l.append(data)

    df = pd.DataFrame(data_l, columns=coln_l)
    df.set_index("DATEYM", inplace=True)
    return df


def download_all_data(output_directory_name: str) -> None:
    urls_5f = [
        NORTH_AMERICA_5F,
        EU_5F,
        JAPAN_5F,
        ASIA_PACIFIC_EXCLUDE_JAPAN_5F,
        EMERGING_MARKETS_5F,
    ]
    urls_momf = [
        NORTH_AMERICA_MOMF,
        EU_MOMF,
        JAPAN_MOMF,
        ASIA_PACIFIC_EXCLUDE_JAPAN_MOMF,
        EMERGING_MARKETS_MOMF,
    ]
    for file_i in urls_5f + urls_momf:
        print(file_i)
        url = f"{BASE_URL}/{file_i}"
        download_file(url, f"{output_directory_name}/{file_i}")


def read_downloaded_data(output_directory_name: str) -> dict:
    urls_5f = [
        NORTH_AMERICA_5F,
        EU_5F,
        JAPAN_5F,
        ASIA_PACIFIC_EXCLUDE_JAPAN_5F,
        EMERGING_MARKETS_5F,
    ]
    urls_momf = [
        NORTH_AMERICA_MOMF,
        EU_MOMF,
        JAPAN_MOMF,
        ASIA_PACIFIC_EXCLUDE_JAPAN_MOMF,
        EMERGING_MARKETS_MOMF,
    ]
    result_d = dict()
    for file_i in urls_5f + urls_momf:
        ifn = f"{output_directory_name}/{file_i}"
        if not os.path.isfile(ifn):
            raise FileExistsError("There is no file: {ifn}!")
        df = read_file_data(ifn)
        result_d.update({file_i: df.copy()})

    return result_d


def main():
    dateymd = int(datetime.datetime.strftime(datetime.datetime.now().date(), "%Y%m%d"))
    # download file
    # download_all_data(str(dateymd))
    # read zip data
    result_d = read_downloaded_data(str(dateymd))

    FACTOR_L = ["SMB", "HML", "RMW", "CMA", "WML"]
    with pd.ExcelWriter("./result.xlsx") as writer:
        for factor_i in FACTOR_L:
            result_l = list()
            for k, v in result_d.items():
                if factor_i in v.columns:
                    s = v[factor_i].copy()
                    s.name = k
                    result_l.append(s)

            df = pd.concat(result_l, axis="columns")
            df.sort_index(inplace=True)
            mask = df.index.astype(int) >= 199507
            df = df[mask]
            print(factor_i)
            df.to_excel(writer, sheet_name=factor_i)


if __name__ == "__main__":
    main()
