import hcloud
client = hcloud.Client(token='wEyrrJ2SUDhUfmpSEKwFMZtBb4ww2W3wkmeLI6a6xCx59E3WOyY6YqTool9pVqor')
ips = [instance.public_net.ipv4.ip for instance in client.servers.get_all() if instance.status == instance.STATUS_RUNNING]

from cluster_monitor import ClusterMonitor
ClusterMonitor(ips)