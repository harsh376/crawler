import boto
import time

ACCESS_KEY = '###########'
SECRET_KEY = '###########'

KEY_NAME = 'csc326_harsh'
KEY_PATH = '/Users/harsh376/Desktop/Courses/Year4-Sem1/CSC326/backend326/aws'

SECURITY_GROUP_NAME = 'csc326-group-2-012'
SECURITY_GROUP_DESC = 'csc326 security group'

IMAGE_ID = 'ami-8caa1ce4'
INSTANCE_TYPE = 't1.micro'


def connect_to_aws():
    print('Connecting to AWS')
    return boto.connect_ec2(
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
    )


def create_key_pair(conn):
    print('Creating ssh key pair')
    key_pair = conn.create_key_pair(KEY_NAME)
    # change the path accordingly
    key_pair.save(KEY_PATH)


def configure_security_group(conn):
    print('Creating security group')
    sg = conn.create_security_group(
        name=SECURITY_GROUP_NAME,
        description=SECURITY_GROUP_DESC,
    )

    print('Adding rules for security group')
    sg.authorize('ICMP', -1, -1, '0.0.0.0/0')
    sg.authorize('TCP', 22, 22, '0.0.0.0/0')
    sg.authorize('TCP', 80, 80, '0.0.0.0/0')
    sg.authorize('TCP', 8080, 8080, '0.0.0.0/0')
    return sg


def configure_elastic_ip_address(conn, instance):
    print('Creating Elastic IP, associating it to instance')
    elastic_ip = conn.allocate_address()
    conn.associate_address(
        instance_id=instance.id,
        public_ip=elastic_ip.public_ip,
    )
    return elastic_ip.public_ip


def create_instance(conn):
    print('Creating instance')
    reservation_obj = conn.run_instances(
        image_id=IMAGE_ID,
        instance_type=INSTANCE_TYPE,
        security_groups=[SECURITY_GROUP_NAME],
        key_name=KEY_NAME,
    )
    instance = reservation_obj.instances[0]
    return instance


def configure_aws():
    conn = connect_to_aws()

    # Only need to do this once
    # create_key_pair(conn)

    # Create security group
    configure_security_group(conn)

    # Create instance
    instance = create_instance(conn)

    return conn, instance


def get_instance_status(conn, instance_ids=[]):
    instances = conn.get_all_instance_status(instance_ids=instance_ids)
    if not instances:
        return 'working on it'
    else:
        return instances[0].system_status.status


def setup():
    conn, instance = configure_aws()

    while get_instance_status(conn, instance_ids=[instance.id]) != 'ok':
        time.sleep(1)

    public_ip = configure_elastic_ip_address(conn, instance)

    print('Successfully created instance, associated Elastic IP address')
    print('Public IP address: ' + public_ip)


if __name__ == '__main__':
    setup()
