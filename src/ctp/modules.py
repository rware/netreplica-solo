
import subprocess
import pandas as pd
from multiprocessing import Pool
import time, ipaddress, json, csv, ipaddress, random, datetime, sys, os
from scapy.all import rdpcap, wrpcap, Ether, IP
import subprocess
import os
import multiprocessing as mp
from create_trees import TreeNode
from load_trees import load_tree_from_json
from collections import defaultdict, deque
import random 
from scapy.all import rdpcap, wrpcap
import time
from scapy.all import rdpcap, wrpcap
from datetime import datetime, timedelta
import numpy as np


def createSlectionPool(root, startIndex, endIndex):
    nodesList = {}
    qu = deque([root])
    visited = set()

    while len(qu) != 0:
        node = qu.popleft()
        visited.add(node)
        throughputMbps = (node.downlink_bytes * 8) / (60* 1000000)
        nodesList[str(node.network)] = [throughputMbps, node.downlink_burstiness, node.asymmetry, startIndex, endIndex]
        
        for child in node.children:
            if child not in visited:
                qu.append(child)
    return nodesList



def onAndOffCalculator_wave(inputArray, burstSize):
    onAndOffs = np.full_like(inputArray, 0)
    if inputArray[0] >= burstSize:
        onAndOffs[0] = 1
    for i in range(1, len(inputArray)):
        if inputArray[i] >= burstSize and inputArray[i- 1] < burstSize:
            onAndOffs[i] = 1
    return onAndOffs


def createSlectionPool_OnAndOff(root, startIndex, endIndex, burst_size):
    nodesList = {}
    qu = deque([root])
    visited = set()
    while len(qu) != 0:
        node = qu.popleft()
        visited.add(node)
        Ons = onAndOffCalculator_wave(node.download_fragment.container , burst_size)
        onCount = int(np.sum(Ons ==  1.0))
        nodesList[str(node.network) + f'_{startIndex}'] = [onCount, node.downlink_burstiness, node.asymmetry, startIndex, endIndex, list(node.download_fragment.container)]
        
        for child in node.children:
            if child not in visited:
                qu.append(child)
    return nodesList

def createSlectionPool_OnAndOff1(root, startIndex, endIndex, burst_size):
    nodesList = {}
    qu = deque([root])
    visited = set()
    while len(qu) != 0:
        node = qu.popleft()
        visited.add(node)
        Ons = onAndOffCalculator_wave(node.download_fragment.container , burst_size)
        onCount = int(np.sum(Ons ==  1.0))
        nodesList[str(node.network) + f'_{startIndex}'] = [onCount, node.downlink_burstiness, node.asymmetry, startIndex, endIndex, list(node.download_fragment.container)]
        
        for child in node.children:
            if child not in visited:
                qu.append(child)
    return nodesList


# def bg_by_onAndOFF1(nodesList, numberofONs,  numberOfProfiles):
#     selectedNodes = defaultdict(list)
#     counter =0
#     name = f'on_{numberofONs}'
#     for network, bg_info in nodesList.items():
#         # print(bg_info)
#         if bg_info[0] == numberofONs:
#             print(numberofONs)
#             print(bg_info)
#             counter +=1 
#             profileName = f'{name}_profile{counter}'
#             selectedNodes[profileName] = [network, bg_info]
            
#             if counter == numberOfProfiles:
#                 break
#     return selectedNodes


def bg_by_onAndOFF(nodesList, numberofONs,  numberOfProfiles):
    selectedNodes = defaultdict(list)
    counter =0
    name = f'on_{numberofONs}'
    for network, bg_info in nodesList.items():
        if bg_info[0] == numberofONs:
            counter +=1 
            profileName = f'{name}_profile{counter}'
            selectedNodes[profileName] = [network, bg_info]
            
            if counter == numberOfProfiles:
                break
    return selectedNodes


def bg_by_onAndOFF1(nodesList, numberofONs,  numberOfProfiles):
    selectedNodes = defaultdict(list)
    counter =0
    name = f'on_{numberofONs}'
    for network, bg_info in nodesList.items():
        if bg_info[0] == numberofONs:
            counter +=1 
            profileName = f'{name}_profile{counter}'
            selectedNodes[profileName] = [network.split('_')[0], bg_info]
            
            if counter == numberOfProfiles:
                break
    return selectedNodes


def bg_by_throughput(nodesList, numberOfProfiles ,MinThroughput, MaxThroughput):
    selectedNodes = defaultdict(list)
    counter =0
    name = f'tp_{MinThroughput}_{MaxThroughput}'
    for network, bg_info in nodesList.items():
        if bg_info[0] >= MinThroughput and bg_info[0] <= MaxThroughput:
            counter +=1 
            profileName = f'{name}_profile{counter}'
            selectedNodes[profileName] = [network, bg_info]
            
            if counter == numberOfProfiles:
                break
    return selectedNodes

def bg_by_throughput_burstiness(nodesList, numberOfProfiles , MinThroughput, MaxThroughput, MinBurstiness, MaxBurstiness):
    selectedNodes = defaultdict(list)
    counter =0
    name = f'tp_{MinThroughput}_{MaxThroughput}'
    for network, bg_info in nodesList.items():
        if bg_info[0] >= MinThroughput and bg_info[0] <= MaxThroughput and bg_info[1] >= MinBurstiness and bg_info[1] <= MaxBurstiness:
            counter +=1 
            profileName = f'{name}_profile{counter}'
            selectedNodes[profileName] = [network, bg_info]
            
            if counter == numberOfProfiles:
                break
    return selectedNodes

def bg_by_throughput_asymmetry(nodesList, numberOfProfiles ,MinThroughput, MaxThroughput, MinAsymmetry, MaxAsymmetry):
    selectedNodes = defaultdict(list)
    counter =0
    name = f'tp_{MinThroughput}_{MaxThroughput}'
    for network, bg_info in nodesList.items():
        if bg_info[0] >= MinThroughput and bg_info[0] <= MaxThroughput and bg_info[2] >= MinAsymmetry and bg_info[2] <= MaxAsymmetry:
            counter +=1 
            profileName = f'{name}_profile{counter}'
            selectedNodes[profileName] = [network, bg_info]
            
            if counter == numberOfProfiles:
                break
    return selectedNodes


def getUsersOfProfile(rootNode , subnetIP):

    # Find the subnet node based on address
    profileNode = rootNode.find_subnet(target_subnet = ipaddress.ip_network(str(subnetIP)))
    # Find the leaf nodes of the subnet (individual users)
    leafChilren = profileNode.get_leaf_nodes(profileNode)
    # Get the IP address of the users 
    userIPs = [str(user.network.network_address) for user in leafChilren]   
    return userIPs

def get_all_profiles_users(rootNode, profiles, outputFile):
    for prof , info in profiles.items():
        print(prof)
        users = getUsersOfProfile(rootNode , info[0])
        # append the users to the profile
        profiles[prof].append(users)
    # store the profiles in a json file
    with open(outputFile, 'w') as f:
        json.dump(profiles, f)
        
def get_all_profiles_users1(rootNode, profiles, outputFile):
    for prof , info in profiles.items():
        try:
            print(prof)
            users = getUsersOfProfile(rootNode , info[0])
            # append the users to the profile
            profiles[prof].append(users)
        except:
            print('error')
            print(f'The profile {prof} is not valid')
            continue
    # store the profiles in a json file
    with open(outputFile, 'w') as f:
        json.dump(profiles, f)

def JoinPcapsBasedOnIndex(outputFileName, chosenIPs, StartIndex, EndIndex , pcapDir, outputDir):
    # This function joins the pcaps in the folder for each user in chosenIPs based on the index
    # Running the joincap for smaller number of files to avoid the "Argument list too long" error
    # Reduce batch size if the error occurs
    batch_size = 30 
    print(f'Number of IPs: {len(chosenIPs)}')
    # Choosing pcap files based on the index
    pcapNames = [f'/pcap_{i}.pcap' for i in range(StartIndex, EndIndex+1)]
    # Iterate through the batches
    for i in range(0, len(chosenIPs), batch_size):
        currentIPs = chosenIPs[i:i+batch_size]
        # Creating the list of argument for joincap
        
        joincapArg = ' '.join(pcapDir + ip + pcapName for ip in currentIPs for pcapName in pcapNames)
        command = f'joincap -w {outputDir + outputFileName + ".pcap"} ' + joincapArg

        # Merging the result of the previous batch of joincap with the current joincap
        ########### IMPORTANT: Do not merge(join) a file with itself, it will result in unexpected behavior
        ### One thing that was observed is getting into infinite loop of merging the same file with itself and getting very huge files as output
        # To solve this issue, we use tmpFile to store the result of the previous batch and then merge it with the current batch
        tmpFile = outputDir + outputFileName + "tmp.pcap"
        if i != 0:
            moveCommand = f'mv {outputDir + outputFileName + ".pcap"} {tmpFile}'
            moveResult = subprocess.run(moveCommand, shell=True)
            command += " " + tmpFile
        print(command)
        # Using PIPE to get the error of shesll 
    
        result = subprocess.run(command,  stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
        print(result.stdout)
        if result.stderr != None:
            if "joincap: Argument list too long" in result.stderr:
                print("The phrase 'Argument too long' was found in the output, try reducing the batch size")
                return
        deleteTmp = subprocess.run(f'rm -rf {tmpFile}', shell=True)

def MergePcapsOfProfiles(profilesInfoFile ,pcapDir, outputDir):
    # go through the files in experiments_dir and read the selected users and then merge the pcaps for the selected users
    with open (profilesInfoFile, 'r') as f:
        profiles = json.load(f) 
    for prof , info in profiles.items():
        chosenIPs = info[2]
        startIndex = info[1][3]
        endIndex = info[1][4]
        print(prof)
        print(chosenIPs)
        print(startIndex)
        print(endIndex)
        JoinPcapsBasedOnIndex( prof, chosenIPs, startIndex, endIndex, pcapDir, outputDir)
        
        
def MergePcapsOfProfiles1(profilesInfoFile ,pcapDir, outputDir):
    # go through the files in experiments_dir and read the selected users and then merge the pcaps for the selected users
    with open (profilesInfoFile, 'r') as f:
        profiles = json.load(f) 
    for prof , info in profiles.items():
        try:
            print(prof)
            chosenIPs = info[2]
            # TODO: Make sure about this issue
            if len(chosenIPs) > 2800:
                continue
            startIndex = info[1][3]
            endIndex = info[1][4]
            JoinPcapsBasedOnIndex( prof, chosenIPs, startIndex, endIndex, pcapDir, outputDir)
        except:
            print(f'The profile {prof} is not valid')
            
            print(chosenIPs)
            print(startIndex)
            print(endIndex)
            continue

def reorder_pcap_files(input_dir):
    # Create the output directory if it doesn't exist
    output_dir = f'{input_dir[:-1]}_reordered_temp'
    subprocess.run(f'mkdir -p {output_dir}', shell=True, check=True)
    # Define the bash script to process files
    script = f"""
    #!/bin/bash
    input_dir="{input_dir}"
    output_dir="{output_dir}"

    # Loop over all files in the input directory
    for file in "$input_dir"*; do
      if [ -f "$file" ]; then
        # Extract the filename from the path
        filename=$(basename "$file")

        # Define the output file path
        output_file="$output_dir/$filename"

        # Run reordercap command
        reordercap "$file" "$output_file"

        echo "Processed $file and saved to $output_file"
      fi
    done

    echo "All files processed."
    """

    # Run the script
    subprocess.run(script, shell=True, check=True, executable='/bin/bash')
    subprocess.run(f'rm -rf {input_dir}', shell=True, check=True)
    subprocess.run(f'mv {output_dir} {input_dir}', shell=True, check=True)


def PcapPadding(input_pcap, output_pcap):
    packets = rdpcap(input_pcap)
    modified_packets = []

    for pkt in packets:
        if pkt.haslayer(IP):
            # Read the packet length from the IP layer header and add 14 to consider the Ethernet header
            original_frame_len = pkt[IP].len + 14
            if pkt.wirelen != original_frame_len:
                pkt.wirelen = original_frame_len
        modified_packets.append(pkt)
    # Write the modified packets to a new pcap file
    wrpcap(output_pcap, modified_packets)
    
    # Pad the packets
    command = f'tcprewrite -F pad --infile={output_pcap} --outfile={input_pcap}'
    subprocess.run(command, shell=True, check=True)
    
    # Remove the temporary pcap file
    os.remove(output_pcap)
    print(f'Processed file: {input_pcap}')

def parallel_process(func, input_args, cores=0):
    if cores == 0:
        cores = max(1, int(mp.cpu_count() * 0.8))
    with mp.Pool(cores) as pool:
        pool.starmap(func, input_args)

def feed_pcap_files_for_padding(input_dir):
    arg_list = []
    for file in os.listdir(input_dir):
        if file.endswith('.pcap'):
            input_pcap_file = os.path.join(input_dir, file)
            output_pcap_file = f'{input_pcap_file}.temp'
            arg_list.append((input_pcap_file, output_pcap_file))
    print(arg_list)
    parallel_process(PcapPadding, arg_list, 40)
    
def parallel_process1(func, input_args, cores=0):
    if cores == 0:
        cores = max(1, int(mp.cpu_count() * 0.8))
    with mp.Pool(cores) as pool:
        pool.starmap(func, input_args)

# def feed_pcap_files_for_padding1(input_dir):
#     arg_list = []
#     for file in os.listdir(input_dir):
#         if file.endswith('.pcap'):
#             input_pcap_file = os.path.join(input_dir, file)
#             output_pcap_file = f'{input_pcap_file}.temp'
#             arg_list.append((input_pcap_file, output_pcap_file))
#     print(arg_list)
#     parallel_process1(PcapPadding, arg_list)
def feed_pcap_files_for_padding2(input_dir, index):
    arg_list = []
    for file in os.listdir(input_dir):
        if file.endswith('.pcap') and file.startswith(f'on_{index}_'):
            input_pcap_file = os.path.join(input_dir, file)
            output_pcap_file = f'{input_pcap_file}.temp'
            arg_list.append((input_pcap_file, output_pcap_file))
    print(arg_list)
    parallel_process1(PcapPadding, arg_list, 40)
    
    


# Trimming both incoming and outgoing pcap files to the defined threshold
def feed_pcap_files_for_trimming(input_dir, output_dir, threshold):
    arg_list = []
    for file in os.listdir(input_dir):
        if file.endswith('.pcap'):
            input_pcap_file = os.path.join(input_dir, file)
            output_pcap_file = os.path.join(output_dir, file)
            arg_list.append((input_pcap_file, output_pcap_file, threshold))
    parallel_process(Pcap_Trimmer, arg_list)
    
def feed_pcap_files_for_trimming1(input_dir, output_dir, threshold, index):
    arg_list = []
    for file in os.listdir(input_dir):
        if file.endswith('.pcap') and file.startswith(f'on_{index}_'):
            input_pcap_file = os.path.join(input_dir, file)
            output_pcap_file = os.path.join(output_dir, file)
            arg_list.append((input_pcap_file, output_pcap_file, threshold))
    parallel_process(Pcap_Trimmer, arg_list, 40)

def Pcap_Trimmer(pcap_file, outputFile , threshold, interval_ms=100):
    
    
    print('Analyzing pcap file:', pcap_file)
    packets = rdpcap(pcap_file)

    # Initialize variables to store throughput data
    interval_duration = 0.1  # 100ms intervals
    # interval_duration = 1 
    time_intervals = []
    throughput_data = []
    total_bytes = 0
    start_time = None
    current_interval_start = None
    outputPackets = []

    # Calculate throughput in 100ms intervals
    for packet in packets:
        if packet.haslayer('IP'):
            packet_size = packet['IP'].len
            packet_time = datetime.fromtimestamp(float(packet.time))  # Ensure packet.time is a float

            if start_time is None:
                start_time = packet_time
                current_interval_start = start_time

            # Check if the packet belongs to the current interval
            if (packet_time - current_interval_start).total_seconds() < interval_duration:
                if total_bytes <= threshold:
                    outputPackets.append(packet)
                total_bytes += packet_size
            
            else:
                # Calculate throughput for the current interval
                throughput_mbps = (total_bytes * 8) / (1e5)  # Convert bytes to bits, then to Mbps
                throughput_mbps = total_bytes 
                time_intervals.append(current_interval_start)
                throughput_data.append(throughput_mbps)

                # Reset for the next interval
                current_interval_start += timedelta(seconds=interval_duration)
                total_bytes = packet_size
                outputPackets.append(packet)
    # Save the modified pcap
    # Delete the input pcap file
    # os.remove(pcap_file)
    wrpcap(outputFile, outputPackets)
    

def feed_pcap_files_for_checking(input_dir):
    arg_list = []
    for file in os.listdir(input_dir):
        if file.endswith('.pcap'):
            input_pcap_file = os.path.join(input_dir, file)
            arg_list.append((input_pcap_file, 'alaki'))
    print(arg_list)
    parallel_process(checkPcap, arg_list)
    
def checkPcap(fileName, alaki):
    command = f'tshark -r {fileName} -T fields -e frame.len -e ip.len > temp.txt'
    # check if the frame length is larger than the ip length
    subprocess.call(command, shell=True)
    data = pd.read_csv('temp.txt', sep='\t')
    if not all(data.iloc[:, 0] > data.iloc[:, 1]):
        print("Error in file: ", fileName)