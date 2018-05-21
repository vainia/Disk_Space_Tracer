#!/usr/bin/env python3

CONF = {
   'TTU':1, # Time to update in seconds
   'HIP':'185.52.193.84', # Remote host ip
   'USN':'eouser', # Username for SSH connection to remote host
   'PAS':'', # Password for SSH connection to remote host [if you have no .SSH key in ~/.ssh/id_rsa.pub]
   'LOC':['/dev','/run','/','/dev/shm','/run/lock'] # Paths to trace where filesystems mounted on
}

import json
import pygal
import datetime
from pexpect import pxssh

json_stack = {'server_name':'','time':[],'mounts':[]}
for mount_name in CONF['LOC']:
    json_stack['mounts'].append({'mount_name':mount_name,'used':[],'avail':[]})
#if __name__ == '__main__':
for i in range(5):

    json_make = {'server_name':'','time':[],'mounts':[]}
    for mount_name in CONF['LOC']:
        json_make['mounts'].append({'mount_name':mount_name,'used':[],'avail':[]})

    s = pxssh.pxssh()
    try:
        s.login(CONF['HIP'], CONF['USN'], CONF['PAS'])
        print('SSH session login successful')
        s.sendline('hostname')
        s.prompt()
        host_name = s.before.decode('utf-8').splitlines()[1]
        json_make['server_name'] = host_name
        s.sendline('df -k')
        s.prompt()
        json_make['time'].append(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        mount_list = s.before.decode('utf-8').splitlines()[2:]
        for path in mount_list:
            fields = path.strip().split()
            for mount in json_make['mounts']:
                if mount['mount_name']==fields[-1]:
                    mount['used'].append(int(fields[2]))
                    mount['avail'].append(int(fields[3]))

        # print(json.dumps(json_make, indent=4, sort_keys=True))

        # Send json_make like JSON into queue.

        s.logout()
    except Exception as e:
        print('SSH session failed on login.')

    # Get data from queue and make chart(s)
    json_recieved = json_make

    # Copying recieved JSON into data stack of traced statistic
    json_stack['server_name'] = json_recieved['server_name']
    json_stack['time'].append(''.join(json_recieved['time']))

    for mount in json_recieved['mounts']:
        i = json_recieved['mounts'].index(mount)
        try:
            json_stack['mounts'][i]['used'].append(mount['used'][0])
            json_stack['mounts'][i]['avail'].append(mount['avail'][0])
        except Exception as e:
            pass

    chart = pygal.Line(x_label_rotation=20)
    chart.title = f'Storage usage on "{host_name}" in Kbytes \n U - used. \t A - available.'
    chart.x_labels = json_stack['time']

    for mount in json_stack['mounts']:
        name = mount['mount_name']
        chart.add(f'U: {name}', mount['used'])
        chart.add(f'A: {name}', mount['avail'])


    chart.render_to_file(f'/Users/napolsky/Downloads/chart.svg')
