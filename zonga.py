#!/usr/local/bin/python3 -u
import boto3
import time
import socket
import json
from sys import argv


def create_instance(imageid='', instancetype='', securitygroups='',
                    nametag='', subnetid='', count='', keyname=''):
    response = ec2.run_instances(MinCount=count,
                                 MaxCount=count,
                                 ImageId=imageid,
                                 InstanceType=instancetype,
                                 KeyName=keyname,
                                 NetworkInterfaces=[
                                     {'DeviceIndex': 0,
                                      'AssociatePublicIpAddress': True,
                                      'SubnetId': subnetid,
                                      'Groups': securitygroups,
                                      },
                                 ],
                                 TagSpecifications=[
                                     {'ResourceType': 'instance',
                                      'Tags': [{'Key': 'Name',
                                                'Value': nametag}
                                               ]
                                      },
                                     {'ResourceType': 'volume',
                                      'Tags': [{'Key': 'Name',
                                                'Value': nametag}
                                               ]
                                      }
                                 ]
                                 )

    return response


def term_instances(ids):
    wait_timer = 10
    print('Waiting a bit before cleaning up.', end='')
    while wait_timer > 0:
        time.sleep(1)
        print('.', end='')
        wait_timer -= 1

    ec2.terminate_instances(InstanceIds=ids)
    print('\nYou have been terminated.')


def print_details(newinstanceidlist):
    wait_timer = 3
    print('Giving instances a couple seconds to have resources assigned.', end='')
    while wait_timer > 0:
        time.sleep(1)
        print('.', end='')
        wait_timer -= 1
    print('.')

    for count, InstanceId in enumerate(newinstanceidlist):
        # InstanceId = instance['InstanceId']
        iid = ec2.describe_instances(InstanceIds=[InstanceId])
        publicip = iid['Reservations'][0]['Instances'][0]['PublicIpAddress']
        privateip = iid['Reservations'][0]['Instances'][0]['PrivateIpAddress']
        publicipname = socket.getfqdn(publicip)
        print(
            f'Instance #{count + 1} has id: {InstanceId}, public IP: {publicip}, and private IP: {privateip}.'
            )

    return


def import_config():
    global secgrps
    global subid
    global numins
    global name
    global instype
    global image_id
    global key_name

    with open('zonga.config', 'r') as config_file:
        file = json.loads(config_file.read())
        secgrps = file['secgrps']
        subid = file['subid']
        numins = file['numinstances']
        name = file['nametag']
        instype = file['instype']
        image_id = file['image_id']
        key_name = file['key_name']

    print(f"--- Values from config file ---\n\n"
          f"Security Groups: {secgrps}\n"
          f"Subnet ID: {subid}\n"
          f"Instance Type: {instype}\n"
          f"Name tag value: {name}\n"
          f"Number of instances: {numins}\n"
          f"Image ID: {image_id}\n"
          f"Key Name: {key_name}\n"
          )

    yn = input('Do these values look good? [y|n]: ')
    if str.lower(yn) == 'y':
        return True
    else:
        return False


def ask_for_variables():
    global numins
    global name
    global instype
    global subid
    global secgrps
    global image_id
    global keyname

    numins_input = input(f"How many instances to spin up(default {numins})? ")
    if numins_input:
        numins = int(numins_input)

    name_input = input(f"What value to use for Name tag(default {name})? ")
    if name_input:
        name = name_input

    instype_input = input(f"What instance type(default {instype})? ")
    if instype_input:
        instype = instype_input

    secgrps_input = input(f"Security Groups(separate by comma with no spaces if more than one)(Default: {secgrps})?")
    if secgrps_input:
        secgrps = secgrps_input.split(',')

    subid_input = input(f"What Subnet ID to use(Default: {subid})? ")
    if subid_input:
        subid = subid_input

    image_id_input = input(f"What Image ID to use(Default: {image_id})?")
    if image_id_input:
        image_id = image_id_input

    key_name_input = input(f"What Image ID to use(Default: {image_id})?")
    if key_name_input:
        key_name = key_name_input


if __name__ == '__main__':

    if len(argv) < 2:
        exit('Must provide aws profile name from credentials file(type "default" if needed)')
        # You can also add a -t after the profile name to terminate instances after they are created
        # for debugging purposes
    else:
        session = boto3.Session(profile_name=argv[1])
        ec2 = session.client('ec2')

    if not import_config():
        ask_for_variables()

    print("Creating instance(s)")
    make_it_so = create_instance(count=numins,
                                 nametag=name,
                                 instancetype=instype,
                                 securitygroups=secgrps,
                                 subnetid=subid,
                                 imageid=image_id,
                                 keyname=key_name
                                 )

    if make_it_so['ResponseMetadata']['HTTPStatusCode'] == 200:
        newinstanceidlist = [x['InstanceId'] for x in make_it_so['Instances']]

        print_details(newinstanceidlist)

    try:
        if argv[2] == '-t':
            term_instances(newinstanceidlist)
    except IndexError:
        print("No terminate directive.  All done.")
