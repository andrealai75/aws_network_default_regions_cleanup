import boto3
from botocore.config import Config

from libs.internet_gateways_mng import InternetGatewaysMng
from libs.subnets_mng import SubnetsMng
from libs.vpcs_mng import VPCsMng


class RegionsMng:
    def __init__(self, name: str):
        self.name = name
        self.ec2_client = self.get_ec2_client()
        self.vpcs_mng = VPCsMng(name)
        self.internet_gateways_mng = InternetGatewaysMng(name)
        self.internet_gateways_mng.load_attached(vpc_ids=self.vpcs_mng.default_vpc_ids)
        self.internet_gateways_mng.load_detached()
        self.subnets_mng = SubnetsMng(name)
        self.subnets_mng.load(vpc_ids=self.vpcs_mng.default_vpc_ids)

    def get_ec2_client(self):
        ec2_config = Config(region_name=self.name)
        return boto3.client("ec2", config=ec2_config)

    def clean(self, dry_run: bool):
        print(f"\nINFO: Cleaning: {self.name}")
        self.internet_gateways_mng.clean(dry_run=dry_run)
        self.subnets_mng.clean(dry_run=dry_run)
        self.vpcs_mng.clean(dry_run=dry_run)

    def __str__(self):
        ret_value = "--------\n"
        ret_value += f"{self.vpcs_mng}\n"
        ret_value += f"{self.internet_gateways_mng}\n"
        ret_value += f"{self.subnets_mng}"
        return ret_value
