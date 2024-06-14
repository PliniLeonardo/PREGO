import os
from typing import Dict, List

import pandas as pd
import torch
from torch.nn.utils.rnn import pad_sequence


def extract_user_toy_and_id_from_name(name: str):
    """
    Retrieves the user and toy ids from the name of the csv file.
    To Be Used for metadata.

    Args:
        name (str): name of the csv file
    Returns:
        user (str): user id
        toy (str): toy id
    """
    name = name.split(".")[0]
    name_parts = name.split("_")
    # Index of the part of the name containing the user and toy ids
    user_toy_idx = 3  # Subsequent "-" split= 0: user, 1: toy
    user, toy = name_parts[user_toy_idx].split("-")
    idx = name_parts[-1]
    return user, toy, idx


def is_correct_procedure(procedure: pd.DataFrame):
    """
    Checks if the procedure is correct.

    Args:
        procedure (pd.DataFrame): procedure to be checked
    Returns:
        is_correct (int): 1 if the procedure is correct, 0 otherwise
    """
    return int(
        (len(procedure["label"].unique()) == 1)
        and (procedure["label"].unique()[0] == "correct")
    )


def get_csv_files(path_to_csv: str, split: str = 'all'):
    """
    Retrieves the csv files in the given path.

    Args:
        path_to_csv: path to the csv folder
        split: 'all' for all the csv files, 'correct' for the correct ones, 'mistake' for the mistake ones
    Returns:
        csv_files: list of csv file_names (str) in the given path
    """
    filenames = 'None'
    assert split in ['all', 'correct', 'mistake'], "The split must be 'all', 'correct' or 'mistake'."
    if split == 'all':
        filenames = [f for f in os.listdir(path_to_csv) if f.endswith('.csv')]
    elif split == 'correct':
        filenames = correct_split
    elif split == 'mistake':
        filenames = mistake_split
    return filenames


def get_csv_data(path_to_csv: str, split: str = 'all', return_filenames: bool = False):
    """
    Retrieves the csv files in the given path.

    Args:
        path_to_csv: path to the csv folder
        split: 'all' for all the csv files, 'correct' for the correct ones, 'mistake' for the mistake ones
    Returns:
        csv_data: list of pandas dataframes (pd.DataFrame) for the csv file_names in the given path
        csv_files: list of csv file_names (str) in the given path (only if return_filenames=True)
    """
    csv_files = get_csv_files(path_to_csv, split)
    csv_data = []
    for csv_file in csv_files:
        csv_data.append(pd.read_csv(os.path.join(path_to_csv, csv_file)))
    if return_filenames:
        return csv_data, csv_files
    return csv_data


def verb2OH(verb: str):
    """
    Converts a verb to a one-hot vector.

    Args:
        verb (str): verb to be converted
    Returns:
        oh: one-hot vector (torch.tensor)
    """
    oh = torch.zeros(len(verbs_sorted))
    oh[verbs_sorted.index(verb)] = 1
    return oh


def part2OH(this: str, that: str):
    """
    Converts a part to a one-hot vector.
    To Be Done on "this" and "that" keys.
    Note: "this" and "that" don't need to be different, in this case only one part will be represented.

    Args:
        this (str): part1 to be converted
        that (str): part2 to be converted
    Returns:
        oh: one-hot vector (torch.tensor)
    """
    oh = torch.zeros(len(parts_sorted))
    if this == that:
        oh[parts_sorted.index(this)] = 2
        return oh
    oh[parts_sorted.index(this)] = 1
    oh[parts_sorted.index(that)] = 1
    return oh


def label2OH(label: str):
    """
    Converts a label to a one-hot vector.

    Args:
        label (str): label to be converted
    Returns:
        oh: one-hot vector (torch.tensor)
    """
    oh = torch.zeros(len(labels_sorted))
    oh[labels_sorted.index(label)] = 1
    return oh


def DF2OH(process_df: pd.DataFrame):
    """
    Converts a dataframe to a one-hot vector.

    Args:
        process_df (pd.DataFrame): dataframe to be converted
    Returns:
        oh_sample: one-hot vector (torch.tensor)
        oh_label: one-hot vector (torch.tensor)
        keysteps: list of keysteps (list of str)
    """
    all_rows_samples = []
    all_rows_labels = []
    keysteps = []
    for _, row in process_df.iterrows():
        oh_current_sample = torch.cat(
            (verb2OH(row["verb"]), part2OH(row["this"], row["that"]))
        )
        keysteps.append("{}-{}-{}".format(row["verb"], row["this"], row["that"]))
        oh_current_label = label2OH(row["label"])
        all_rows_samples.append(oh_current_sample)
        all_rows_labels.append(oh_current_label)
    oh_sample = torch.stack(all_rows_samples)
    oh_label = torch.stack(all_rows_labels)
    ### Padding ###
    assert oh_sample.shape[0] == len(process_df), "The number of rows in the dataframe and the one-hot vector don't match."

    end = 60 - oh_label.shape[0]

    # pad oh_sample & oh_label with all ones on first dimension to match 60 as shape
    # if oh_sample.shape[0] < 60:
    #     pad = torch.ones(end, oh_sample.shape[1])
    #     oh_sample = torch.cat((oh_sample, pad), dim=0)
    #     pad = torch.ones(end, oh_label.shape[1])
    #     oh_label = torch.cat((oh_label, pad), dim=0)
    #     keysteps = keysteps + ["end"] * (end)

    return oh_sample, oh_label, keysteps


def get_OH_data(path_to_csv: str, split: str = 'all'):
    """
    Retrieves the csv files in the given path and transform it to one-hot representation.

    Args:
        path_to_csv: path to the csv folder
        split: 'all' for all the csv files, 'correct' for the correct ones, 'mistake' for the mistake ones
    Returns:
        oh_samplelist: list of tensor (torch.tensor) from the csv file_names in the given path (verb, this, that)
        oh_labellist: list of tensor (torch.tensor) from the csv file_names in the given path (label)
        metadata: list of tuples (user, toy, is_correct) from the csv file_names in the given path
        all_keysteps: list of lists of keysteps (list of str) from the csv file_names in the given path
    """
    csv_data, csv_files = get_csv_data(path_to_csv, split, return_filenames=True)
    oh_samplelist = []
    oh_labellist = []
    all_keysteps = []
    metadata = []
    for csv, csv_name in zip(csv_data, csv_files):
        oh_sample, oh_label, keysteps = DF2OH(csv)
        oh_samplelist.append(oh_sample)
        oh_labellist.append(oh_label)
        all_keysteps.append(keysteps)
        user, toy, idx = extract_user_toy_and_id_from_name(csv_name)
        metadata.append((user, toy, idx, is_correct_procedure(csv)))
    return oh_samplelist, oh_labellist, metadata, all_keysteps

def collate_fn(data):
    out = {}

    oh_samples, oh_labels, metadatas = [], [], []
    for d in data:
        oh_samples.append(d["oh_sample"])
        oh_labels.append(d["oh_label"])
        metadatas.append(d["metadata"])

    # pad according to the max length
    padding_value = 0  # TODO check if 0 or 1 changes something
    out["oh_sample"] = pad_sequence(
        oh_samples, batch_first=True, padding_value=padding_value
    )
    out["oh_label"] = pad_sequence(
        oh_labels, batch_first=True, padding_value=padding_value
    )

    out["metadata"] = metadatas

    return out

verbs_sorted = ["attach", "detach"]

parts_sorted = [
    "arm",
    "arm connector",
    "back seat",
    "base",
    "basket",
    "battery",
    "blade",
    "body",
    "boom",
    "bucket",
    "bulldozer arm",
    "bumper",
    "cabin",
    "cabin back",
    "cabin window",
    "chassis",
    "clamp",
    "connector",
    "container",
    "crane arm",
    "cylinder",
    "dashboard",
    "door",
    "dump bed",
    "dumpbed",
    "engine",
    "engine cover",
    "excavator arm",
    "figurine",
    "fire equipment",
    "fire extinguisher",
    "grill",
    "hook",
    "interior",
    "jackhammer",
    "ladder",
    "ladder basket",
    "lid",
    "light",
    "mixer",
    "mixer stand",
    "nut",
    "push frame",
    "rear body",
    "rear bumper",
    "rear roof",
    "rocker panel",
    "roller",
    "roller arm",
    "roof",
    "side ladder",
    "sound module",
    "spoiler",
    "step",
    "strap",
    "tilter",
    "track",
    "transport cabin",
    "turnplate",
    "turntable base",
    "turntable top",
    "water tank",
    "wheel",
    "window",
    "windshield",
]

labels_sorted = ["correct", "correction", "mistake"]

remarks_sorted = [
    "previous one is mistake",
    "shouldn't have happened",
    "wrong order",
    "wrong position",
]

correct_split = [
    'nusar-2021_action_both_9081-a21_9081_user_id_2021-02-12_155024.csv',
    'nusar-2021_action_both_9021-c03d_9021_user_id_2021-02-23_100036.csv',
    'nusar-2021_action_both_9025-b08d_9025_user_id_2021-02-18_101512.csv',
    'nusar-2021_action_both_9046-a29_9046_user_id_2021-02-22_105358.csv',
    'nusar-2021_action_both_9056-c12d_9056_user_id_2021-02-22_144251.csv',
    'nusar-2021_action_both_9032-a03_9032_user_id_2021-02-25_155323.csv',
    'nusar-2021_action_both_9066-a16_9066_user_id_2021-02-17_152811.csv',
    'nusar-2021_action_both_9086-c03d_9086_user_id_2021-02-16_153418.csv',
    'nusar-2021_action_both_9011-b08c_9011_user_id_2021-02-01_154736.csv',
    'nusar-2021_action_both_9074-a29_9074_user_id_2021-02-11_154856.csv',
    'nusar-2021_action_both_9084-b05c_9084_user_id_2021-02-25_152453.csv',
    'nusar-2021_action_both_9014-a23_9014_user_id_2021-02-02_142800.csv',
    'nusar-2021_action_both_9056-a19_9056_user_id_2021-02-22_141312.csv',
    'nusar-2021_action_both_9033-a30_9033_user_id_2021-02-18_141254.csv',
    'nusar-2021_action_both_9043-c03c_9043_user_id_2021-02-05_141851.csv',
    'nusar-2021_action_both_9054-a18_9054_user_id_2021-02-08_153620.csv',
    'nusar-2021_action_both_9081-a30_9081_user_id_2021-02-12_155525.csv',
    'nusar-2021_action_both_9014-a12_9014_user_id_2021-02-02_141945.csv',
    'nusar-2021_action_both_9046-a14_9046_user_id_2021-02-22_104013.csv',
    'nusar-2021_action_both_9036-a01_9036_user_id_2021-02-17_162038.csv',
    'nusar-2021_action_both_9052-c03d_9052_user_id_2021-02-25_170244.csv',
    'nusar-2021_action_both_9052-c14a_9052_user_id_2021-02-25_170706.csv',
    'nusar-2021_action_both_9025-a20_9025_user_id_2021-02-03_150504.csv',
    'nusar-2021_action_both_9071-c14a_9071_user_id_2021-02-11_092353.csv',
    'nusar-2021_action_both_9026-c06e_9026_user_id_2021-02-03_170116.csv',
    'nusar-2021_action_both_9024-c13b_9024_user_id_2021-02-23_150503.csv',
    'nusar-2021_action_both_9031-c11b_9031_user_id_2021-02-23_165714.csv',
    'nusar-2021_action_both_9023-a19_9023_user_id_2021-02-23_133654.csv',
    'nusar-2021_action_both_9016-b03a_9016_user_id_2021-02-17_140509.csv',
    'nusar-2021_action_both_9024-c09b_9024_user_id_2021-02-23_152108.csv',
    'nusar-2021_action_both_9052-b06a_9052_user_id_2021-02-08_110734.csv',
    'nusar-2021_action_both_9046-b06b_9046_user_id_2021-02-22_105953.csv',
    'nusar-2021_action_both_9055-b08b_9055_user_id_2021-02-24_104106.csv',
    'nusar-2021_action_both_9022-a15_9022_user_id_2021-02-03_111237.csv',
    'nusar-2021_action_both_9032-a21_9032_user_id_2021-02-04_112105.csv',
    'nusar-2021_action_both_9044-b05b_9044_user_id_2021-02-05_163057.csv',
    'nusar-2021_action_both_9042-a02_9042_user_id_2021-02-05_111642.csv',
    'nusar-2021_action_both_9036-c01c_9036_user_id_2021-02-18_092539.csv',
    'nusar-2021_action_both_9055-b04c_9055_user_id_2021-02-24_103545.csv',
    'nusar-2021_action_both_9031-c04d_9031_user_id_2021-02-23_163320.csv',
    'nusar-2021_action_both_9036-c03f_9036_user_id_2021-02-18_093646.csv',
    'nusar-2021_action_both_9061-b08d_9061_user_id_2021-02-09_141038.csv',
    'nusar-2021_action_both_9071-b06b_9071_user_id_2021-02-11_100739.csv',
    'nusar-2021_action_both_9075-a07_9075_user_id_2021-02-12_093237.csv',
    'nusar-2021_action_both_9062-c08c_9062_user_id_2021-02-09_160823.csv',
    'nusar-2021_action_both_9065-b06d_9095_user_id_2021-02-17_123817.csv',
    'nusar-2021_action_both_9064-c09a_9064_user_id_2021-02-22_165525.csv',
    'nusar-2021_action_both_9025-a20_9025_user_id_2021-02-18_095735.csv',
    'nusar-2021_action_both_9021-a29_9021_user_id_2021-02-23_094113.csv',
    'nusar-2021_action_both_9064-a20_9064_user_id_2021-02-22_161628.csv',
    'nusar-2021_action_both_9014-c13e_9014_user_id_2021-02-02_151834.csv',
    'nusar-2021_action_both_9014-b02a_9014_user_id_2021-02-02_143628.csv',
    'nusar-2021_action_both_9086-c14a_9086_user_id_2021-02-16_153910.csv',
    'nusar-2021_action_both_9022-c01a_9022_user_id_2021-02-23_111001.csv',
    'nusar-2021_action_both_9051-c08a_9051_user_id_2021-02-22_115717.csv',
    'nusar-2021_action_both_9042-c03b_9042_user_id_2021-02-05_120824.csv',
    'nusar-2021_action_both_9044-c03a_9044_user_id_2021-02-19_093447.csv',
    'nusar-2021_action_both_9065-a24_9095_user_id_2021-02-17_121359.csv',
    'nusar-2021_action_both_9085-c03d_9085_user_id_2021-02-22_174243.csv',
    'nusar-2021_action_both_9085-c10a_9085_user_id_2021-02-22_174720.csv',
    'nusar-2021_action_both_9082-c13f_9082_user_id_2021-02-16_140937.csv',
    'nusar-2021_action_both_9045-b05d_9045_user_id_2021-02-05_171423.csv',
    'nusar-2021_action_both_9041-b06d_9041_user_id_2021-02-05_102410.csv',
    'nusar-2021_action_both_9084-b02b_9084_user_id_2021-02-25_141202.csv',
    'nusar-2021_action_both_9066-a09_9066_user_id_2021-02-17_152039.csv',
    'nusar-2021_action_both_9051-b03a_9051_user_id_2021-02-22_114140.csv',
    'nusar-2021_action_both_9073-a18_9073_user_id_2021-02-11_140513.csv',
    'nusar-2021_action_both_9074-a03_9074_user_id_2021-02-11_151600.csv',
    'nusar-2021_action_both_9022-b03b_9022_user_id_2021-02-03_113201.csv',
    'nusar-2021_action_both_9041-c13f_9041_user_id_2021-02-05_103116.csv',
    'nusar-2021_action_both_9086-c04c_9086_user_id_2021-02-16_154811.csv',
    'nusar-2021_action_both_9022-b03b_9022_user_id_2021-02-23_105258.csv',
    'nusar-2021_action_both_9084-b04c_9084_user_id_2021-02-25_144254.csv',
    'nusar-2021_action_both_9045-b06c_9045_user_id_2021-02-05_173118.csv',
    'nusar-2021_action_both_9025-c12a_9025_user_id_2021-02-18_111731.csv',
    'nusar-2021_action_both_9036-b02a_9036_user_id_2021-02-17_162715.csv',
    'nusar-2021_action_both_9054-c01a_9054_user_id_2021-02-08_160424.csv',
    'nusar-2021_action_both_9072-c10a_9072_user_id_2021-02-11_112415.csv',
    'nusar-2021_action_both_9025-c06b_9025_user_id_2021-02-03_160657.csv',
    'nusar-2021_action_both_9082-c09b_9082_user_id_2021-02-16_134010.csv',
    'nusar-2021_action_both_9014-c01b_9014_user_id_2021-02-02_150612.csv',
    'nusar-2021_action_both_9031-c10b_9031_user_id_2021-02-04_101552.csv',
    'nusar-2021_action_both_9022-a18_9022_user_id_2021-02-23_104757.csv',
    'nusar-2021_action_both_9016-c03c_9016_user_id_2021-02-17_142449.csv',
    'nusar-2021_action_both_9023-c04b_9023_user_id_2021-02-23_144136.csv',
    'nusar-2021_action_both_9011-c03f_9011_user_id_2021-02-01_160239.csv',
    'nusar-2021_action_both_9045-b05d_9045_user_id_2021-02-19_103439.csv',
    'nusar-2021_action_both_9015-a08_9015_user_id_2021-02-02_155549.csv',
    'nusar-2021_action_both_9081-c08a_9081_user_id_2021-02-12_160626.csv',
    'nusar-2021_action_both_9033-b04d_9033_user_id_2021-02-04_135802.csv',
    'nusar-2021_action_both_9012-c07c_9012_user_id_2021-02-01_164345.csv',
    'nusar-2021_action_both_9053-c08b_9053_user_id_2021-02-08_140757.csv',
    'nusar-2021_action_both_9031-b01b_9031_user_id_2021-02-23_164014.csv',
    'nusar-2021_action_both_9026-a07_9026_user_id_2021-02-03_162446.csv',
    'nusar-2021_action_both_9012-b06d_9012_user_id_2021-02-01_163713.csv',
    'nusar-2021_action_both_9022-a15_9022_user_id_2021-02-23_104138.csv',
    'nusar-2021_action_both_9073-b08a_9073_user_id_2021-02-11_145217.csv',
    'nusar-2021_action_both_9025-a26_9025_user_id_2021-02-03_152505.csv',
    'nusar-2021_action_both_9033-c06a_9033_user_id_2021-02-18_144743.csv',
    'nusar-2021_action_both_9046-c01d_9046_user_id_2021-02-22_110733.csv',
    'nusar-2021_action_both_9083-a19_9083_user_id_2021-02-16_111909.csv',
    'nusar-2021_action_both_9022-b06c_9022_user_id_2021-02-03_114112.csv',
    'nusar-2021_action_both_9035-c09a_9035_user_id_2021-02-18_163930.csv',
    'nusar-2021_action_both_9035-c02c_9035_user_id_2021-02-04_170431.csv',
    'nusar-2021_action_both_9023-a19_9023_user_id_2021-02-03_132936.csv',
    'nusar-2021_action_both_9025-c05a_9025_user_id_2021-02-03_155604.csv',
    'nusar-2021_action_both_9062-c06b_9062_user_id_2021-02-09_154158.csv',
    'nusar-2021_action_both_9022-c03e_9022_user_id_2021-02-23_111647.csv',
    'nusar-2021_action_both_9011-b06b_9011_user_id_2021-02-01_154253.csv',
    'nusar-2021_action_both_9025-c06b_9025_user_id_2021-02-18_105233.csv',
    'nusar-2021_action_both_9021-a14_9021_user_id_2021-02-23_092806.csv',
    'nusar-2021_action_both_9042-b05c_9042_user_id_2021-02-05_115957.csv',
    'nusar-2021_action_both_9072-a15_9072_user_id_2021-02-11_110655.csv',
    'nusar-2021_action_both_9026-b08a_9026_user_id_2021-02-03_165029.csv',
    'nusar-2021_action_both_9062-b02b_9062_user_id_2021-02-09_152026.csv',
    'nusar-2021_action_both_9062-a21_9062_user_id_2021-02-09_151231.csv',
    'nusar-2021_action_both_9025-a26_9025_user_id_2021-02-18_101010.csv',
    'nusar-2021_action_both_9085-c01d_9085_user_id_2021-02-22_172144.csv',
    'nusar-2021_action_both_9035-c08c_9035_user_id_2021-02-18_163203.csv',
    'nusar-2021_action_both_9056-b08a_9056_user_id_2021-02-09_114053.csv',
    'nusar-2021_action_both_9022-b06c_9022_user_id_2021-02-23_112257.csv',
    'nusar-2021_action_both_9034-c13f_9034_user_id_2021-02-23_180813.csv',
    'nusar-2021_action_both_9043-a12_9043_user_id_2021-02-05_130910.csv',
    'nusar-2021_action_both_9023-c09c_9023_user_id_2021-02-23_134459.csv',
    'nusar-2021_action_both_9066-b06a_9066_user_id_2021-02-17_155256.csv',
    'nusar-2021_action_both_9043-b03b_9043_user_id_2021-02-05_133926.csv',
    'nusar-2021_action_both_9081-c11b_9081_user_id_2021-02-12_161433.csv',
    'nusar-2021_action_both_9026-c13c_9026_user_id_2021-02-03_172406.csv',
    'nusar-2021_action_both_9071-b05d_9071_user_id_2021-02-11_094129.csv',
    'nusar-2021_action_both_9016-b06a_9016_user_id_2021-02-17_141229.csv',
    'nusar-2021_action_both_9022-a18_9022_user_id_2021-02-03_112259.csv',
    'nusar-2021_action_both_9034-c02b_9034_user_id_2021-02-23_173828.csv',
    'nusar-2021_action_both_9061-c09b_9061_user_id_2021-02-09_143132.csv',
    'nusar-2021_action_both_9065-a28_9095_user_id_2021-02-17_122244.csv',
    'nusar-2021_action_both_9021-a29_9021_user_id_2021-02-03_105247.csv',
    'nusar-2021_action_both_9083-a26_9083_user_id_2021-02-16_112714.csv',
    'nusar-2021_action_both_9013-c03b_9013_user_id_2021-02-24_113410.csv',
    'nusar-2021_action_both_9021-c10a_9021_user_id_2021-02-23_100458.csv'
]

mistake_split = [
    'nusar-2021_action_both_9044-a08_9044_user_id_2021-02-05_154403.csv',
    'nusar-2021_action_both_9025-b08d_9025_user_id_2021-02-03_153246.csv',
    'nusar-2021_action_both_9053-c12e_9053_user_id_2021-02-08_142744.csv',
    'nusar-2021_action_both_9054-a14_9054_user_id_2021-02-08_152449.csv',
    'nusar-2021_action_both_9016-a24_9016_user_id_2021-02-17_135905.csv',
    'nusar-2021_action_both_9063-c02b_9063_user_id_2021-02-17_094025.csv',
    'nusar-2021_action_both_9045-a23_9045_user_id_2021-02-05_165228.csv',
    'nusar-2021_action_both_9076-c13d_9076_user_id_2021-02-12_115510.csv',
    'nusar-2021_action_both_9052-c12c_9052_user_id_2021-02-08_114847.csv',
    'nusar-2021_action_both_9076-a20_9076_user_id_2021-02-12_110652.csv',
    'nusar-2021_action_both_9033-a30_9033_user_id_2021-02-04_132852.csv',
    'nusar-2021_action_both_9085-c01c_9085_user_id_2021-02-22_175419.csv',
    'nusar-2021_action_both_9071-c03e_9071_user_id_2021-02-11_101746.csv',
    'nusar-2021_action_both_9055-a07_9055_user_id_2021-02-24_102820.csv',
    'nusar-2021_action_both_9052-c04c_9052_user_id_2021-02-08_112641.csv',
    'nusar-2021_action_both_9032-b04a_9032_user_id_2021-02-04_113248.csv',
    'nusar-2021_action_both_9052-c13d_9052_user_id_2021-02-08_111738.csv',
    'nusar-2021_action_both_9026-b04b_9026_user_id_2021-02-03_163855.csv',
    'nusar-2021_action_both_9024-c09b_9024_user_id_2021-02-03_143716.csv',
    'nusar-2021_action_both_9072-c12d_9072_user_id_2021-02-11_114038.csv',
    'nusar-2021_action_both_9073-c12a_9073_user_id_2021-02-11_141222.csv',
    'nusar-2021_action_both_9025-c05a_9025_user_id_2021-02-18_102043.csv',
    'nusar-2021_action_both_9076-c08c_9076_user_id_2021-02-12_111652.csv',
    'nusar-2021_action_both_9034-a31_9034_user_id_2021-02-23_171931.csv',
    'nusar-2021_action_both_9044-b05b_9044_user_id_2021-02-19_091348.csv',
    'nusar-2021_action_both_9015-c03a_9015_user_id_2021-02-02_163503.csv',
    'nusar-2021_action_both_9041-a16_9041_user_id_2021-02-05_095801.csv',
    'nusar-2021_action_both_9021-a14_9021_user_id_2021-02-03_100733.csv',
    'nusar-2021_action_both_9073-c04a_9073_user_id_2021-02-11_142611.csv',
    'nusar-2021_action_both_9054-c05a_9054_user_id_2021-02-08_160931.csv',
    'nusar-2021_action_both_9063-a31_9063_user_id_2021-02-17_091930.csv',
    'nusar-2021_action_both_9055-c12b_9055_user_id_2021-02-24_111107.csv',
    'nusar-2021_action_both_9066-b05b_9066_user_id_2021-02-17_154153.csv',
    'nusar-2021_action_both_9061-c13d_9061_user_id_2021-02-09_143830.csv',
    'nusar-2021_action_both_9024-c11a_9024_user_id_2021-02-03_144917.csv',
    'nusar-2021_action_both_9021-a27_9021_user_id_2021-02-03_103039.csv',
    'nusar-2021_action_both_9045-b06c_9045_user_id_2021-02-19_121606.csv',
    'nusar-2021_action_both_9023-c04b_9023_user_id_2021-02-03_135504.csv',
    'nusar-2021_action_both_9013-c09c_9013_user_id_2021-02-24_113951.csv',
    'nusar-2021_action_both_9045-c03e_9045_user_id_2021-02-19_122426.csv',
    'nusar-2021_action_both_9012-c14b_9012_user_id_2021-02-01_164944.csv',
    'nusar-2021_action_both_9016-c01d_9016_user_id_2021-02-17_141821.csv',
    'nusar-2021_action_both_9065-b05a_9095_user_id_2021-02-17_122813.csv',
    'nusar-2021_action_both_9064-c02c_9064_user_id_2021-02-22_163357.csv',
    'nusar-2021_action_both_9046-c10b_9046_user_id_2021-02-22_111419.csv',
    'nusar-2021_action_both_9061-c02a_9061_user_id_2021-02-09_141537.csv',
    'nusar-2021_action_both_9035-a06_9035_user_id_2021-02-18_152536.csv',
    'nusar-2021_action_both_9055-b08b_9055_user_id_2021-02-09_100238.csv',
    'nusar-2021_action_both_9035-c07b_9035_user_id_2021-02-18_154148.csv',
    'nusar-2021_action_both_9021-a27_9021_user_id_2021-02-23_093522.csv',
    'nusar-2021_action_both_9043-b05a_9043_user_id_2021-02-05_134455.csv',
    'nusar-2021_action_both_9035-c08c_9035_user_id_2021-02-04_172543.csv',
    'nusar-2021_action_both_9011-c01c_9011_user_id_2021-02-01_155620.csv',
    'nusar-2021_action_both_9083-c08c_9083_user_id_2021-02-16_110837.csv',
    'nusar-2021_action_both_9035-a06_9035_user_id_2021-02-04_163525.csv',
    'nusar-2021_action_both_9023-b05d_9023_user_id_2021-02-03_134815.csv',
    'nusar-2021_action_both_9044-a08_9044_user_id_2021-02-19_083738.csv',
    'nusar-2021_action_both_9076-a13_9076_user_id_2021-02-12_104816.csv',
    'nusar-2021_action_both_9041-c14b_9041_user_id_2021-02-05_104936.csv',
    'nusar-2021_action_both_9033-c12e_9033_user_id_2021-02-18_150129.csv',
    'nusar-2021_action_both_9075-a06_9075_user_id_2021-02-12_092222.csv',
    'nusar-2021_action_both_9084-c02a_9084_user_id_2021-02-25_140008.csv',
    'nusar-2021_action_both_9076-c12c_9076_user_id_2021-02-12_113921.csv',
    'nusar-2021_action_both_9065-a17_9095_user_id_2021-02-17_114124.csv',
    'nusar-2021_action_both_9086-c09b_9086_user_id_2021-02-16_155556.csv',
    'nusar-2021_action_both_9056-b08a_9056_user_id_2021-02-22_141934.csv',
    'nusar-2021_action_both_9082-c07b_9082_user_id_2021-02-16_133255.csv',
    'nusar-2021_action_both_9013-a02_9013_user_id_2021-02-02_130807.csv',
    'nusar-2021_action_both_9032-c06f_9032_user_id_2021-02-04_114322.csv',
    'nusar-2021_action_both_9031-c06c_9031_user_id_2021-02-23_164844.csv',
    'nusar-2021_action_both_9073-a10_9073_user_id_2021-02-25_150711.csv',
    'nusar-2021_action_both_9034-b04c_9034_user_id_2021-02-04_155013.csv',
    'nusar-2021_action_both_9036-b08c_9036_user_id_2021-02-17_163111.csv',
    'nusar-2021_action_both_9055-c06e_9055_user_id_2021-02-09_100939.csv',
    'nusar-2021_action_both_9071-c13a_9071_user_id_2021-02-11_090900.csv',
    'nusar-2021_action_both_9014-b05a_9014_user_id_2021-02-02_144248.csv',
    'nusar-2021_action_both_9021-b05c_9021_user_id_2021-02-23_094649.csv',
    'nusar-2021_action_both_9082-a10_9082_user_id_2021-02-16_134840.csv',
    'nusar-2021_action_both_9044-a09_9044_user_id_2021-02-05_155544.csv',
    'nusar-2021_action_both_9064-a30_9064_user_id_2021-02-22_162122.csv',
    'nusar-2021_action_both_9075-c08b_9075_user_id_2021-02-12_101609.csv',
    'nusar-2021_action_both_9015-a09_9015_user_id_2021-02-02_160807.csv',
    'nusar-2021_action_both_9034-c08b_9034_user_id_2021-02-23_175357.csv',
    'nusar-2021_action_both_9084-c09b_9084_user_id_2021-02-25_140624.csv',
    'nusar-2021_action_both_9024-c04c_9024_user_id_2021-02-23_151613.csv',
    'nusar-2021_action_both_9061-b04a_9061_user_id_2021-02-09_135722.csv',
    'nusar-2021_action_both_9033-c02a_9033_user_id_2021-02-18_143949.csv',
    'nusar-2021_action_both_9085-b05c_9085_user_id_2021-02-22_173439.csv',
    'nusar-2021_action_both_9055-c04b_9055_user_id_2021-02-09_102558.csv',
    'nusar-2021_action_both_9024-b08b_9024_user_id_2021-02-23_150955.csv',
    'nusar-2021_action_both_9054-c11a_9054_user_id_2021-02-08_162610.csv',
    'nusar-2021_action_both_9012-c06d_9012_user_id_2021-02-18_121034.csv',
    'nusar-2021_action_both_9042-a28_9042_user_id_2021-02-05_113759.csv',
    'nusar-2021_action_both_9031-c11b_9031_user_id_2021-02-04_104944.csv',
    'nusar-2021_action_both_9043-c01b_9043_user_id_2021-02-05_140432.csv',
    'nusar-2021_action_both_9054-c01a_9054_user_id_2021-02-08_154802.csv',
    'nusar-2021_action_both_9016-c10b_9016_user_id_2021-02-17_143201.csv',
    'nusar-2021_action_both_9041-a17_9041_user_id_2021-02-05_101033.csv',
    'nusar-2021_action_both_9066-a08_9066_user_id_2021-02-17_151541.csv',
    'nusar-2021_action_both_9081-b04d_9081_user_id_2021-02-12_160020.csv',
    'nusar-2021_action_both_9056-c10b_9056_user_id_2021-02-09_105117.csv',
    'nusar-2021_action_both_9024-c12c_9024_user_id_2021-02-23_153804.csv',
    'nusar-2021_action_both_9083-b06a_9083_user_id_2021-02-16_113603.csv',
    'nusar-2021_action_both_9044-b01a_9044_user_id_2021-02-19_085343.csv',
    'nusar-2021_action_both_9033-b04d_9033_user_id_2021-02-18_141950.csv',
    'nusar-2021_action_both_9031-c12d_9031_user_id_2021-02-04_105807.csv',
    'nusar-2021_action_both_9031-c04d_9031_user_id_2021-02-04_104130.csv',
    'nusar-2021_action_both_9045-c13e_9045_user_id_2021-02-19_134158.csv',
    'nusar-2021_action_both_9053-c10b_9053_user_id_2021-02-08_143830.csv',
    'nusar-2021_action_both_9034-c08b_9034_user_id_2021-02-04_161726.csv',
    'nusar-2021_action_both_9075-c10c_9075_user_id_2021-02-12_100519.csv',
    'nusar-2021_action_both_9024-c11a_9024_user_id_2021-02-23_153251.csv',
    'nusar-2021_action_both_9032-c07a_9032_user_id_2021-02-04_115644.csv',
    'nusar-2021_action_both_9031-a13_9031_user_id_2021-02-23_160001.csv',
    'nusar-2021_action_both_9062-b04d_9062_user_id_2021-02-09_152854.csv',
    'nusar-2021_action_both_9051-c13a_9051_user_id_2021-02-22_121941.csv',
    'nusar-2021_action_both_9011-c13b_9011_user_id_2021-02-01_160915.csv',
    'nusar-2021_action_both_9073-b06c_9073_user_id_2021-02-11_135342.csv',
    'nusar-2021_action_both_9065-c09c_9095_user_id_2021-02-17_124439.csv',
    'nusar-2021_action_both_9055-c04b_9055_user_id_2021-02-24_110239.csv',
    'nusar-2021_action_both_9023-a03_9023_user_id_2021-02-23_133018.csv',
    'nusar-2021_action_both_9051-c10a_9051_user_id_2021-02-22_120421.csv',
    'nusar-2021_action_both_9056-c13a_9056_user_id_2021-02-22_145733.csv',
    'nusar-2021_action_both_9056-c09a_9056_user_id_2021-02-22_140419.csv',
    'nusar-2021_action_both_9026-c12b_9026_user_id_2021-02-03_171236.csv',
    'nusar-2021_action_both_9074-a14_9074_user_id_2021-02-11_152306.csv',
    'nusar-2021_action_both_9033-c02a_9033_user_id_2021-02-04_140532.csv',
    'nusar-2021_action_both_9034-a31_9034_user_id_2021-02-04_152413.csv',
    'nusar-2021_action_both_9086-c13a_9086_user_id_2021-02-16_152408.csv',
    'nusar-2021_action_both_9074-c06b_9074_user_id_2021-02-11_160509.csv',
    'nusar-2021_action_both_9015-b05b_9015_user_id_2021-02-02_161800.csv',
    'nusar-2021_action_both_9056-c01c_9056_user_id_2021-02-22_143138.csv',
    'nusar-2021_action_both_9035-c02c_9035_user_id_2021-02-18_153533.csv',
    'nusar-2021_action_both_9024-c04c_9024_user_id_2021-02-03_142724.csv',
    'nusar-2021_action_both_9064-c08a_9064_user_id_2021-02-22_164245.csv',
    'nusar-2021_action_both_9012-a17_9012_user_id_2021-02-01_162209.csv',
    'nusar-2021_action_both_9013-b01a_9013_user_id_2021-02-02_135446.csv',
    'nusar-2021_action_both_9055-c06e_9055_user_id_2021-02-24_105542.csv',
    'nusar-2021_action_both_9023-c05b_9023_user_id_2021-02-23_144552.csv',
    'nusar-2021_action_both_9056-a19_9056_user_id_2021-02-09_112504.csv',
    'nusar-2021_action_both_9075-b01b_9075_user_id_2021-02-12_102823.csv',
    'nusar-2021_action_both_9064-c13a_9064_user_id_2021-02-22_170304.csv',
    'nusar-2021_action_both_9082-c08c_9082_user_id_2021-02-16_094651.csv',
    'nusar-2021_action_both_9033-c13a_9033_user_id_2021-02-18_151004.csv',
    'nusar-2021_action_both_9044-a09_9044_user_id_2021-02-19_084540.csv',
    'nusar-2021_action_both_9012-a16_9012_user_id_2021-02-01_162904.csv',
    'nusar-2021_action_both_9031-c12d_9031_user_id_2021-02-23_170320.csv',
    'nusar-2021_action_both_9041-c07c_9041_user_id_2021-02-05_104114.csv',
    'nusar-2021_action_both_9032-c08a_9032_user_id_2021-02-25_154353.csv',
    'nusar-2021_action_both_9054-c06a_9054_user_id_2021-02-08_150948.csv',
    'nusar-2021_action_both_9072-c04d_9072_user_id_2021-02-11_113148.csv',
    'nusar-2021_action_both_9042-a11_9042_user_id_2021-02-05_112612.csv',
    'nusar-2021_action_both_9024-b08b_9024_user_id_2021-02-03_141607.csv',
    'nusar-2021_action_both_9072-a14_9071_user_id_2021-02-11_104901.csv',
    'nusar-2021_action_both_9034-b02b_9034_user_id_2021-02-23_172457.csv',
    'nusar-2021_action_both_9043-a24_9043_user_id_2021-02-05_133010.csv',
    'nusar-2021_action_both_9063-c14a_9063_user_id_2021-02-17_101116.csv',
    'nusar-2021_action_both_9061-a01_9061_user_id_2021-02-09_134524.csv',
    'nusar-2021_action_both_9036-c13b_9036_user_id_2021-02-18_094212.csv',
    'nusar-2021_action_both_9062-c07a_9062_user_id_2021-02-09_155212.csv',
    'nusar-2021_action_both_9083-c03a_9083_user_id_2021-02-16_114344.csv',
    'nusar-2021_action_both_9044-b01a_9044_user_id_2021-02-05_160818.csv',
    'nusar-2021_action_both_9074-c12e_9074_user_id_2021-02-11_155839.csv',
    'nusar-2021_action_both_9034-b02b_9034_user_id_2021-02-04_153734.csv',
    'nusar-2021_action_both_9044-b06a_9044_user_id_2021-02-19_092710.csv',
    'nusar-2021_action_both_9046-a27_9046_user_id_2021-02-22_104709.csv',
    'nusar-2021_action_both_9035-c14a_9035_user_id_2021-02-18_164650.csv',
    'nusar-2021_action_both_9023-c09c_9023_user_id_2021-02-03_133550.csv',
    'nusar-2021_action_both_9076-c06a_9076_user_id_2021-02-12_112908.csv',
    'nusar-2021_action_both_9013-a28_9013_user_id_2021-02-02_134923.csv',
    'nusar-2021_action_both_9081-c13a_9081_user_id_2021-02-12_162453.csv',
    'nusar-2021_action_both_9053-c03e_9053_user_id_2021-02-08_135619.csv',
    'nusar-2021_action_both_9066-b03b_9066_user_id_2021-02-17_153607.csv',
    'nusar-2021_action_both_9071-c12c_9071_user_id_2021-02-11_102615.csv',
    'nusar-2021_action_both_9051-c12a_9051_user_id_2021-02-22_121059.csv',
    'nusar-2021_action_both_9015-c04a_9015_user_id_2021-02-02_164257.csv',
    'nusar-2021_action_both_9034-b04c_9034_user_id_2021-02-23_173159.csv',
    'nusar-2021_action_both_9031-b01b_9031_user_id_2021-02-04_102950.csv',
    'nusar-2021_action_both_9053-c09a_9053_user_id_2021-02-08_134120.csv',
    'nusar-2021_action_both_9045-a23_9045_user_id_2021-02-19_102455.csv',
    'nusar-2021_action_both_9015-c10c_9015_user_id_2021-02-02_165955.csv',
    'nusar-2021_action_both_9063-b01b_9063_user_id_2021-02-17_092512.csv',
    'nusar-2021_action_both_9023-a03_9023_user_id_2021-02-03_131031.csv',
    'nusar-2021_action_both_9063-c13f_9063_user_id_2021-02-17_100446.csv',
    'nusar-2021_action_both_9072-b03a_9072_user_id_2021-02-11_111335.csv',
    'nusar-2021_action_both_9035-c07b_9035_user_id_2021-02-04_171214.csv',
    'nusar-2021_action_both_9063-c07b_9063_user_id_2021-02-17_095115.csv',
    'nusar-2021_action_both_9042-c09c_9042_user_id_2021-02-17_102611.csv',
    'nusar-2021_action_both_9082-a31_9082_user_id_2021-02-16_132731.csv',
    'nusar-2021_action_both_9053-c01d_9053_user_id_2021-02-08_141432.csv'
]

