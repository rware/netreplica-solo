import os 
import subprocess

def run_sudo(cmd, password):
    subprocess.run(
        f"sudo -S sh -c '{cmd}'",
        shell=True,
        input=password + "\n",
        text=True,
        check=True,
    )

def shaping(download_mbps, upload_mbps, qdisc, password):
    """
    HTB-based shaping with AQM.
    Rates are in Mbps.

    Supported queuing disciplines:
      pfifo, bfifo, red, gred, pie, codel, fq_codel, fq, cake
    """
    run_sudo(
        f"tc qdisc del dev veth2 root 2>/dev/null || true && "
        f"tc qdisc add dev veth2 root handle 1: htb default 10 && "
        f"tc class add dev veth2 parent 1: classid 1:10 htb "
        f"rate {download_mbps}Mbit ceil {download_mbps}Mbit && "
        f"tc qdisc add dev veth2 parent 1:10 {qdisc}",
        password,
    )

    run_sudo(
        f"tc qdisc del dev veth4 root 2>/dev/null || true && "
        f"tc qdisc add dev veth4 root handle 1: htb default 10 && "
        f"tc class add dev veth4 parent 1: classid 1:10 htb "
        f"rate {upload_mbps}Mbit ceil {upload_mbps}Mbit && "
        f"tc qdisc add dev veth4 parent 1:10 {qdisc}",
        password,
    )
