import time
import boto3
import os

from botocore.exceptions import ClientError

USER_NAME = 'ubuntu'
KEY_NAME = 'csc326_harsh'
KEY_PATH = os.path.join(os.path.dirname(__file__), 'key.pem')

SECURITY_GROUP_NAME = 'csc326-group-2-012'
SECURITY_GROUP_DESC = 'csc326 security group'

IMAGE_ID = 'ami-8caa1ce4'
INSTANCE_TYPE = 't1.micro'


def connect_to_aws():
    print('Connecting to AWS')
    session = boto3.Session(profile_name='csc326')
    ec2 = session.resource(service_name='ec2')

    return ec2


def create_key_pair(conn):
    print('Creating ssh key pair')
    try:
        key_pair = conn.create_key_pair(KeyName=KEY_NAME)
        key_pair_out = str(key_pair.key_material)
        os.remove(KEY_PATH)
        outfile = open(KEY_PATH, 'w')
        outfile.write(key_pair_out)
        os.chmod(KEY_PATH, 0400)
    except ClientError:
        print ('Key pair: ' + KEY_NAME + ' already exists')


def configure_security_group(conn):
    print('Creating security group')
    try:
        sg = conn.create_security_group(
            GroupName=SECURITY_GROUP_NAME,
            Description=SECURITY_GROUP_DESC,
        )
        print('Adding rules for security group')
        sg.authorize_ingress(
            IpProtocol='ICMP',
            FromPort=-1,
            ToPort=-1,
            CidrIp='0.0.0.0/0',
        )
        sg.authorize_ingress(
            IpProtocol='TCP',
            FromPort=22,
            ToPort=22,
            CidrIp='0.0.0.0/0',
        )
        sg.authorize_ingress(
            IpProtocol='TCP',
            FromPort=80,
            ToPort=80,
            CidrIp='0.0.0.0/0',
        )
        sg.authorize_ingress(
            IpProtocol='TCP',
            FromPort=8080,
            ToPort=8080,
            CidrIp='0.0.0.0/0',
        )
    except ClientError:
        print ('Security group: ' + SECURITY_GROUP_NAME + ' already exists')


def configure_elastic_ip_address(conn, instance):
    print('Creating Elastic IP, associating it to instance')

    client = conn.meta.client
    elastic_ip = client.allocate_address()
    client.associate_address(
        InstanceId=instance.id,
        PublicIp=elastic_ip['PublicIp'],
    )
    return elastic_ip['PublicIp']


def create_instance(conn):
    print('Creating instance')

    instances = conn.create_instances(
        ImageId=IMAGE_ID,
        MinCount=1,
        MaxCount=1,
        InstanceType=INSTANCE_TYPE,
        SecurityGroups=[SECURITY_GROUP_NAME],
        KeyName=KEY_NAME,
    )
    return instances[0]


def configure_aws():
    conn = connect_to_aws()

    create_key_pair(conn)

    configure_security_group(conn)

    instance = create_instance(conn)

    return conn, instance


def is_instance_up(conn, instance):
    client = conn.meta.client

    response = client.describe_instance_status(
        InstanceIds=[instance.id],
    )
    instance_statuses = response['InstanceStatuses']

    if instance_statuses:
        return instance_statuses[0]['SystemStatus']['Status'] == 'ok'
    return False


def get_elastic_ip(client, instance_id):
    response = client.describe_addresses(
        Filters=[
            {
                'Name': 'instance-id',
                'Values': [instance_id],
            },
        ]
    )
    public_ip, allocation_id = None, None
    if response['Addresses']:
        public_ip = response['Addresses'][0]['PublicIp']
        allocation_id = response['Addresses'][0]['AllocationId']

    return public_ip, allocation_id


def release_elastic_ip(conn, instance_id):
    client = conn.meta.client

    # Get elastic IP associated with instance
    public_ip, allocation_id = get_elastic_ip(client, instance_id)

    if public_ip:
        print ('Disassociating elastic IP')
        # Disassociate elastic IP from EC2 instance
        client.disassociate_address(PublicIp=public_ip)

    if allocation_id:
        print ('Releasing elastic IP')
        # Release elastic IP
        client.release_address(AllocationId=allocation_id)

        print ('elastic IP: ' + public_ip + ' successfully released')


def terminate_instance(conn, instance_id):
    client = conn.meta.client

    print ('Terminating instance: ' + instance_id)
    try:
        client.terminate_instances(InstanceIds=[instance_id])
        print ('Successfully terminated instance: ' + instance_id)
    except ClientError:
        print ('Failed to terminate instance. Please check instance id')


def setup():
    conn, instance = configure_aws()

    while not is_instance_up(conn, instance=instance):
        time.sleep(1)

    public_ip = configure_elastic_ip_address(conn, instance)

    print('Successfully created instance, associated Elastic IP address')
    return KEY_PATH, USER_NAME, public_ip


def teardown(instance_id):
    # connect to AWS
    conn = connect_to_aws()

    # disassociate and release elastic IP for instance
    release_elastic_ip(conn=conn, instance_id=instance_id)

    # terminate EC2 instance
    terminate_instance(conn=conn, instance_id=instance_id)
