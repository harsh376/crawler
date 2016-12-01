import os

from aws.aws import setup
from paramiko import SSHClient, AutoAddPolicy


COPY_START_SCRIPT_CMD = 'scp -r -o StrictHostKeyChecking=no -i {key_filename} start.sh {user_name}@{hostname}:~/'


def deploy():
    # start instance
    key_filename, user_name, hostname = setup()

    # copy the the start script
    os.system(COPY_START_SCRIPT_CMD.format(
        key_filename=key_filename,
        user_name=user_name,
        hostname=hostname,
    ))

    # start app
    start_app(key_filename, user_name, hostname)
    print ('Public IP address: ' + hostname)


def start_app(key_filename, user_name, hostname):
    client = SSHClient()
    client.set_missing_host_key_policy(AutoAddPolicy())
    client.connect(
        hostname=hostname,
        username=user_name,
        key_filename=key_filename,
    )
    stdin, stdout, stderr = client.exec_command('./start.sh')
    stdin.flush()
    data = stdout.read().splitlines()
    for line in data:
        print line


if __name__ == '__main__':
    deploy()
