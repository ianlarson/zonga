#!/usr/local/bin/python3 -u
import boto3
import time
import socket
import json

from sys import argv

import pprint
pp = pprint.PrettyPrinter()


class AccountRepresentation:
    def __init__(self):
        # self.ec2 = ec2
        # self.sts = sts
        self.vpcs = ec2.describe_vpcs()['Vpcs']
        self.vpcs_organized = {}
        for vpc in self.vpcs:
            self.vpcs_organized[vpc['VpcId']] = vpc
            self.vpcs_organized[vpc['VpcId']]['Subnets'] = {}
            self.vpcs_organized[vpc['VpcId']]['SecurityGroups'] = {}
        self.subnets = ec2.describe_subnets()['Subnets']
        for subnet in self.subnets:
            subnet_id = subnet['SubnetId']
            self.vpcs_organized[subnet['VpcId']]['Subnets'][subnet_id] = subnet
        self.security_groups = ec2.describe_security_groups()['SecurityGroups']
        for sg in self.security_groups:
            self.vpcs_organized[sg['VpcId']]['SecurityGroups'][sg['GroupId']] = sg
        self.keypairs = ec2.describe_key_pairs()['KeyPairs']
        self.account_id = sts.get_caller_identity()['Account']
        self.selections = {}

    def ask_for_vpc(self):
        choices = {}
        for count, vpc in enumerate(self.vpcs_organized, 1):
            vpc_dump = self.vpcs_organized[vpc]
            choices[count] = {'vpcid': vpc}
            try:
                for tag in vpc_dump['Tags']:
                    if tag['Key'] == 'Name':
                        choices[count]['Name'] = tag['Value']
            except KeyError:
                pass
            finally:
                if 'Name' not in choices[count].keys():
                    choices[count]['Name'] = "No 'Name' tag"
        print("\n")
        for choice in choices:
            print(f"{choice}: {choices[choice]['vpcid']}  -  {choices[choice]['Name']}")
        user_choice = int(input('Choose VPC: '))
        self.selections['vpc'] = choices[user_choice]['vpcid']
        return choices[user_choice]['vpcid']

    def ask_for_subnet(self, user_chosen_vpcid):
        choices = {}
        for count, subnet in enumerate(self.vpcs_organized[user_chosen_vpcid]['Subnets'], 1):
            # print(subnet)
            # print(type(subnet))
            choices[count] = {
                'subnetid': subnet,
                'az': self.vpcs_organized[user_chosen_vpcid]['Subnets'][subnet]['AvailabilityZone'],
                'cidr': self.vpcs_organized[user_chosen_vpcid]['Subnets'][subnet]['CidrBlock']
            }
            try:
                if self.vpcs_organized[user_chosen_vpcid]['Subnets'][subnet]['Tags'][0]['Name']:
                    choices[count]['Name'] = self.vpcs_organized[user_chosen_vpcid]['Subnets'][subnet]['Tags'][0]['Name']
            except KeyError:
                choices[count]['Name'] = "No 'Name' tag"
        print("\n")
        for choice in choices:
            print(f"{choice}: {choices[choice]['subnetid']}  -  {choices[choice]['cidr']}  -  {choices[choice]['az']}")
        user_choice = int(input('Choose subnet: '))
        self.selections['subnet'] = choices[user_choice]['subnetid']
        return choices[user_choice]['subnetid']

    def ask_for_keys(self):
        choices = {}
        for count, key in enumerate(self.keypairs, 1):
            choices[count] = {
                'keyid': key['KeyPairId'],
                'name': key['KeyName']
            }
        print("\n")
        for choice in choices:
            print(f"{choice}: {choices[choice]['keyid']}  -  {choices[choice]['name']}")
        user_choice = int(input('Choose keypair: '))
        self.selections['keypair'] = choices[user_choice]['name']
        return choices[choice]['name']

    def ask_for_securitygroups(self, user_chosen_vpcid):
        choices = {}
        for count, sg in enumerate(self.vpcs_organized[user_chosen_vpcid]['SecurityGroups'], 1):
            sg_dump = self.vpcs_organized[user_chosen_vpcid]['SecurityGroups'][sg]
            choices[count] = {
                'sgid': sg_dump['GroupId'],
                'name': sg_dump['GroupName'],
            }
        print("\n")
        for choice in choices:
            print(f"{choice}: {choices[choice]['sgid']}  -  {choices[choice]['name']}")
        user_choice = int(input('??  '))
        self.selections['securitygroup'] = choices[user_choice]['sgid']
        chosen = [choices[user_choice]['sgid']]
        return chosen

    def ask_for_instance_type(self):
        choices = {
            1: 't3a.nano',
            2: 't3a.small',
            3: 'm5a.large',
            4: 'c5.large',
            5: 'r5a.large'
        }
        print("\n")
        for choice in choices:
            print(f"{choice}: {choices[choice]}")
        user_choice = int(input('Choose instance type: '))
        self.selections['instype'] = choices[user_choice]
        chosen = choices[user_choice]
        return chosen

    def get_variables(self):
        values = {}
        values['vpc'] = self.ask_for_vpc()
        values['subnet'] = self.ask_for_subnet(values['vpc'])
        values['sg'] = self.ask_for_securitygroups(values['vpc'])
        values['key'] = self.ask_for_keys()
        values['instype'] = self.ask_for_instance_type()
        values['count'] = int(input('How many to build(default 1): ') or 1)
        values['nameinst'] = input('What should we use for the Name tag (default ZongaInstance): ') or 'ZongaInstance'
        values['imageid'] = input('What Image ID to use(Default ami-0323c3dd2da7fb37d): ') or 'ami-0323c3dd2da7fb37d'
        return values


def create_instance(imageid, instancetype, securitygroups,
                    nametag, subnetid, count, keyname):
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
        iid = ec2.describe_instances(InstanceIds=[InstanceId])
        publicip = iid['Reservations'][0]['Instances'][0]['PublicIpAddress']
        privateip = iid['Reservations'][0]['Instances'][0]['PrivateIpAddress']
        publicipname = socket.getfqdn(publicip)
        print(
            f'Instance #{count + 1} has id: {InstanceId}, public IP: {publicip}, and private IP: {privateip}.'
            )

    return


def import_config():
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
        values = {
            'subnet': subid,
            'sg': secgrps,
            'key': key_name,
            'instype': instype,
            'count': 1,
            'nameinst': name,
            'imageid': image_id
        }
        return values
    else:
        return False


if __name__ == '__main__':

    if len(argv) < 2:
        exit('Must provide aws profile name from credentials file(use "default" if needed)')
        # You can also add a -t after the profile name to terminate instances after they are created
        # for debugging purposes
    else:
        session = boto3.Session(profile_name=argv[1])
        ec2 = session.client('ec2')
        sts = session.client('sts')
        account = AccountRepresentation()

    build_details = import_config()
    if build_details is False:
        build_details = account.get_variables()

    print("Creating instance(s)")
    make_it_so = create_instance(count=build_details['count'],
                                 nametag=build_details['nameinst'],
                                 instancetype=build_details['instype'],
                                 securitygroups=build_details['sg'],
                                 subnetid=build_details['subnet'],
                                 imageid=build_details['imageid'],
                                 keyname=build_details['key']
                                 )

    if make_it_so['ResponseMetadata']['HTTPStatusCode'] == 200:
        newinstanceidlist = [x['InstanceId'] for x in make_it_so['Instances']]

        print_details(newinstanceidlist)

    try:
        if argv[2] == '-t':
            term_instances(newinstanceidlist)
    except IndexError:
        print("No terminate directive.  All done.")
