import hcloud
client = hcloud.Client(token=)
ips = [instance.public_net.ipv4.ip for instance in client.servers.get_all() if instance.status == instance.STATUS_RUNNING]

print(ips)

from paramiko import AutoAddPolicy, SSHClient

sshs = [None] * len(ips)
for i, ip in enumerate(ips):
	sshs[i] = SSHClient()
	sshs[i].load_system_host_keys()
	sshs[i].set_missing_host_key_policy(AutoAddPolicy())
	sshs[i].connect(ip)
	sshs[i].get_transport().set_keepalive(120)

from datetime import datetime
import numpy as np
import time

stdouts = [None] * len(ips)
usages = [[0]*10] * len(ips)
memorys = np.zeros(len(ips))
rx = np.zeros(len(ips))
tx = np.zeros(len(ips))
first = True
while True:
	for i, (ip, ssh) in enumerate(zip(ips, sshs)):
		assert ssh.get_transport().is_alive()
		_, stdouts[i], _ = ssh.exec_command("cat /proc/stat | grep 'cpu '; cat /proc/meminfo | grep MemTotal; cat /proc/meminfo | grep MemAvailable; cat /proc/net/dev | grep eth0; cat /proc/net/dev | grep eth0")
	total_delta_usages = np.zeros(len(ips))
	delta_rx = np.zeros(len(ips))
	delta_tx = np.zeros(len(ips))
	asdf = [[0]*10] * len(ips)
	for i, (ip, stdout) in enumerate(zip(ips, stdouts)):
		assert stdout.channel.recv_exit_status() == 0
		prev_usage = usages[i]
		usages[i] = np.array([int(s) / 100 for s in stdout.readline().split()[1:]])
		total = int(stdout.readline().split()[-2])
		avail = int(stdout.readline().split()[-2])
		memorys[i] = 100 * (total - avail) / total
		prev_rx, prev_tx = rx[i], tx[i]
		rx[i], tx[i] = int(stdout.readline().split()[1]), int(stdout.readline().split()[9])
		delta_rx[i] = rx[i] - prev_rx
		delta_tx[i] = tx[i] - prev_tx
		delta_usage = usages[i] - prev_usage
		total_delta_usages[i] = sum(delta_usage)
		asdf[i] = [100 * elem / total_delta_usages[i] for elem in delta_usage]
		total_delta_usages[i] = 100 * (total_delta_usages[i] - delta_usage[3]) / total_delta_usages[i]
	if first:
		delta_rx /= 2**10
		delta_tx /= 2**10
	from termcolor import colored
	print(datetime.now(), colored(f' {np.mean(total_delta_usages):5.2f}', 'green'), f'‾{np.max(total_delta_usages):6.2f} {np.min(total_delta_usages):5.2f}_'
			, colored(f' {np.mean(memorys):5.2f}', 'green'), f'‾{np.max(memorys):5.2f} {np.min(memorys):5.2f}_'
			, " →" + colored(f'{np.sum(delta_rx)/2**20:.2f}  {np.sum(delta_tx)/2**20:.2f}', 'green') + '→', ' ', [f'{elem:.1f}' for elem in np.average(asdf, 0)])
	time.sleep(1)
	first = False
