import sys

from aws.aws import teardown


def terminate(instance_id):
    if not instance_id:
        print ('Instance id required!')
    else:
        teardown(instance_id=instance_id)


if __name__ == '__main__':
    if len(sys.argv) == 2:
        terminate(sys.argv[1])
    else:
        terminate(None)
