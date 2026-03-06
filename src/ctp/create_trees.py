from __future__ import annotations
import ipaddress
import json
import os
import pickle
from collections import defaultdict
from tree_node import TreeNode
import numpy as np
from pyspark.sql import SparkSession
import json
from tree_node import TreeNode
from time_series_modules import TimeSeries, Fragment
import multiprocessing as mp


def filter_users(mask: str, path: str) -> list[ipaddress.IPv4Network]:
    ipaddresses = [ipaddress.IPv4Network(name) for name in os.listdir(path) if
                   os.path.isdir(os.path.join(path, name))]
    return ipaddresses


def group_by_upper_subnet(tree_nodes: list[TreeNode], new_prefix) -> dict[ipaddress.IPv4Network, list[TreeNode]]:
    groups = defaultdict(list)

    for tree_node in tree_nodes:
        # Convert IP to an IPv4Address object and get the upper-level subnet]
        ip_network = ipaddress.ip_network(tree_node.network)
        upper_subnet = ip_network.supernet(new_prefix=new_prefix)

        # Group IPs by their upper subnet
        groups[upper_subnet].append(tree_node)

    return groups


def create_user_tree_nodes(user_ips, time_series_dict, time: int) -> list[TreeNode]:
    tree_node_list = []

    for user_ip in user_ips:
        # print(len(time_series_dict[str(user_ip.network_address)].download_fragments), len(time_series_dict[str(user_ip.network_address)].upload_fragments))
        df = Fragment() if len(time_series_dict[str(user_ip.network_address)].download_fragments) == 0 or len(
            time_series_dict[str(user_ip.network_address)].download_fragments) - 1 < time else \
            time_series_dict[str(user_ip.network_address)].download_fragments[time]
        uf = Fragment() if len(time_series_dict[str(user_ip.network_address)].upload_fragments) == 0 or len(
            time_series_dict[str(user_ip.network_address)].upload_fragments) - 1 < time else \
            time_series_dict[str(user_ip.network_address)].upload_fragments[time]
        tree_node = TreeNode.from_parameters(user_ip, df, uf,
                                             time_series_dict[str(user_ip.network_address)].total_fwd_packets,
                                             time_series_dict[str(user_ip.network_address)].total_bwd_packets)
        tree_node_list.append(tree_node)

    return tree_node_list


def extract_time_series(user_ips, directory) -> dict[str:TimeSeries]:
    time_series_dict = {}

    for user_ip in user_ips:
        address = user_ip.network_address

        path = os.path.join(directory, str(address), "timeseries.pkl")

        with open(path, "rb") as f:
            time_series_dict[str(address)] = pickle.load(f)
            f.close()

    return time_series_dict


def convert_to_tree_nodes(groups) -> list[TreeNode]:
    new_tree_nodes = []

    for key, value in groups.items():

        # Better to use numpy for the fragments
        download_fragment = Fragment()
        upload_fragment = Fragment()
        df = download_fragment.container
        uf = upload_fragment.container
        fwd_packets = 0
        bwd_packets = 0
        for tree_node in value:
            df = np.add(df, tree_node.download_fragment.container)
            uf = np.add(uf, tree_node.upload_fragment.container)
            fwd_packets += tree_node.fwd_packets
            bwd_packets += tree_node.bwd_packets

        download_fragment.container = df
        upload_fragment.container = uf
        new_tree_nodes.append(
            TreeNode.from_parameters(key, download_fragment, upload_fragment, fwd_packets, bwd_packets, value))

    return new_tree_nodes


def save_tree_to_json(tree, output_file):
    # Save the tree to a JSON file.
    tree_dict = tree.to_dict()
    with open(output_file, 'w') as f:
        json.dump(tree_dict, f, indent=2)
    print(f"Saved Tree - {output_file}")


def load_tree_from_json(input_file):
    # Load the tree from a JSON file.
    with open(input_file, 'r') as f:
        tree_dict = json.load(f)
    return TreeNode.from_dict(tree_dict)


def calculate_users(root):
    if len(root.children) == 0:
        return 1

    for child in root.children:
        root.num_users += calculate_users(child)

    return root.num_users


def construct_trees(user_ips, time_series_dict, segmented_tree_folder, t: int):
    try:

        print(f"Constructing Tree for time slice: {t}")
        prefix = 31

        tree_nodes = create_user_tree_nodes(user_ips, time_series_dict, t)

        for i in range(prefix, 15, -1):
            groups = group_by_upper_subnet(tree_nodes, i)
            tree_nodes = convert_to_tree_nodes(groups)

        ip_network = ipaddress.ip_network('0.0.0.0/0')
        final_group = {}
        final_group[ip_network] = tree_nodes
        tree_nodes = convert_to_tree_nodes(final_group)
        if len(tree_nodes) == 1:
            calculate_users(tree_nodes[0])
            path = os.path.join(segmented_tree_folder, f"tree_nodes_{t}_min.json")
            save_tree_to_json(tree_nodes[0], path)
            del tree_nodes
            del groups
        else:
            print("Did not allocate tree nodes properly")

    except Exception as e:
        raise (e)



def load_tree_from_json(input_file):
    # Load the tree from a JSON file.
    with open(input_file, 'r') as f:
        tree_dict = json.load(f)
    return TreeNode.from_dict(tree_dict)

def dfs(root, visited):

    if root.network in visited:
        return

    visited.add(root.network)

    root.compute_median()

    for child in root.children:
        dfs(child, visited)

def save_tree_to_json(tree, output_file):
    # Save the tree to a JSON file.
    tree_dict = tree.to_dict()
    with open(output_file, 'w') as f:
        json.dump(tree_dict, f, indent=2)
    print(f"Saved Tree - {output_file}")


if __name__ == "__main__":
    # start_time = time.time()

    subnet_mask = '169.231'
    directory = "/mnt/md0/vamsi/pcap_data/"
    segmented_trees = '/mnt/md0/vamsi/fixed_segmented_trees/'
    time_limit = 15

    user_ips = filter_users(subnet_mask, directory)
    time_series_dict = extract_time_series(user_ips, directory)
    os.makedirs(segmented_trees, exist_ok=True)

    # args = [(user_ips, time_series_dict, segmented_trees, t) for t in range(time_limit)]

    # with mp.Pool(processes=mp.cpu_count()) as pool:
    #     results = pool.starmap(construct_trees, args)

    # for t in range(time_limit):
    # construct_trees(user_ips, time_series_dict, segmented_trees, 0)
    # end_time = time.time()
    #
    # elapsed_time = end_time - start_time
    # print(f"Elapsed time: {elapsed_time} seconds")

    # print("Completed processing all files")

    spark = SparkSession.builder \
        .appName("Parallel PCAP Processing") \
        .config("spark.executor.memory", "100g") \
        .config("spark.driver.memory", "100g") \
        .config("spark.driver.maxResultSize", "100g") \
        .getOrCreate()

    # pcap_folders = [pcap_dir]
    # List all subdirectories (each containing one pcap file named merged.pcap)
    time_range = [t for t in range(time_limit)]
    # print(f"Found {len(pcap_folders)} folders")
    # print(pcap_folders)

    # Create an RDD to parallelize the pcap folder processing
    rdd = spark.sparkContext.parallelize(time_range)

    # Process each folder in parallel
    packets_rdd = rdd.map(lambda t: construct_trees(user_ips, time_series_dict, segmented_trees, t))

    # Trigger the parallel processing
    packets_rdd.collect()  # This starts the execution of the parallel tasks

    print("Processing complete for all folders.")