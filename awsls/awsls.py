import click
import boto3
import botocore
import pathlib
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sys
from tqdm import tqdm

from loguru import logger
logger.remove()
logger.add(sys.stdout, colorize=True, format="{message}")

ALL_STATES = ['running', 'stopped', 'terminated']

@click.group()
def cli():
    pass

@cli.command()
@click.option('-b', '--bucket', 'bucket_name', default=None, help='name of the bucket (default: process all buckets)')
@click.option('-H', '--human-readable', is_flag=True, default=False, help='print human readable units')
@click.option('-s', '--sort-by-size', is_flag=True, default=False, help='sort by size')
def s3(bucket_name, human_readable, sort_by_size):
    """Return bucket size in Go"""

    s3_ressource = boto3.resource('s3')
    if bucket_name is None:
        buckets =  s3_ressource.buckets.iterator()  # all buckets
    else:
        buckets = [s3_ressource.Bucket(bucket_name)]

    result = {}
    for bucket in tqdm(buckets, desc='Searching bucket...'):
        size = get_bucket_size(bucket)
        result[bucket.name] = size
        
    df = pd.Series(result).to_frame(name='size')
    if sort_by_size:
        df = df.sort_values(by='size', ascending=False)
    render_bucket_df(df, human_readable)


@cli.command()
@click.option('-s', '--state', default=ALL_STATES, help='running, stopped or terminated (default: return all states)')
@click.option('-r','--region', default=None, help='AWS region (default: search all regions)')
@click.option('-o', '--output', default=None, help='output csv file (default: print on stdout)')
def ec2(state, region, output):
    """List instances from AWS EC2"""

    if region is None:
        region = all_regions()
    else:
        region = [region]
    
    if type(state) is not list:
        state = [state]

    if output is not None:
        suffix = pathlib.Path(output).suffix
        if suffix != '.csv':
            raise ValueError(f'Ony .csv output is supported - got {suffix}')

    instances = pd.DataFrame()
    for r in tqdm(region, desc='Searching regions...'):
        region_instances = list_instances(r, state)
        instances = instances.append(region_instances)
    
    if instances.empty:
        print('Nothing found.')
        return

    if output is None:
        render_instance_df(instances)
        return
    
    instances.to_csv(output)


def all_regions():
    ec2_client = boto3.client('ec2', region_name='us-west-1')
    try:
        response = ec2_client.describe_regions()
    except botocore.exceptions.ClientError:
        logger.error('Credential invalid or not found')
        raise
    regions = [i['RegionName'] for i in response['Regions']]
    return regions


def list_instances(region_name='us-east-1', instance_states = ['running', 'stopped', 'terminated']):
    ec2_resource = boto3.resource('ec2', region_name=region_name)
    ec2_client = boto3.client('ec2', region_name=region_name)
    
    instances = ec2_resource.instances.filter(
        Filters=[{'Name': 'instance-state-name', 'Values': instance_states}])

    columns = ['id', 'type', 'state', 'nb_cores', 'memory_size', 'region']
    instances_df = pd.DataFrame(columns=columns)
    for i in instances:
        try:
            details = ec2_client.describe_instance_types(InstanceTypes=[i.instance_type])['InstanceTypes'][0]
            cores = details['VCpuInfo']['DefaultCores']
            memory = details['MemoryInfo']['SizeInMiB']
        except boto3.exceptions.botocore.client.ClientError:
            cores = 'N/A'
            memory = 'N/A'
        instance= pd.Series({'id': i.id, 
                             'type': i.instance_type, 
                             'state': i.state['Name'], 
                             'nb_cores': cores, 
                             'memory_size': memory, 
                             'region': region_name})
        instances_df = instances_df.append(instance, ignore_index=True)
    return instances_df.set_index('id')


def color_tags(color):
    return (f'<{color}>', f'</{color}>')


def render_instance_df(df):
    message = (f"{'instance id':20} {'type':15} {'cores':6} {'memory':10} "
                   f"{'region':12} {'state':15}")
    logger.opt(colors=True).info(message)
    for i in df.index:
        line = df.loc[i]
        if line['state'] == 'running':
            state_color = color_tags('green')
        elif line['state'] == 'stopped':
            state_color = color_tags('yellow')
        elif line['state'] == 'terminated':
            state_color = color_tags('blue')
        message = (f"{i:20} {line['type']:15} {line['nb_cores']:<6} {line['memory_size']:<10} "
                   f"{line['region']:12} {state_color[0]}{line['state']:15}{state_color[1]}")
        logger.opt(colors=True).info(message)
        

def get_bucket_size(bucket):
    total_size = 0
    for obj in bucket.objects.iterator():
        total_size += obj.size
    return total_size  # bytes


def render_bucket_df(df, human_readable=False):
    digits = 10
    if not human_readable:
        digits = max(len(str(df.max().values[0])) + 1, 10)
    logger.info(f"{'bucket name':30} {'size':<{digits}}")

    for name in df.index:
        size = df.loc[name]['size']
        if human_readable:
            size = make_human_readable(size)
        logger.info(f"{name:30} {size:<{digits}}")


def make_human_readable(size, suffix='B'):
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(size) < 1024.0:
            return f"{size:3.1f} {unit}{suffix}"
        size /= 1024.0
    return f"{size:3.1f} 'Yi'{suffix}"

if __name__ == '__main__':
    cli()