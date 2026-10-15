import boto3
from botocore.config import Config
from botocore.exceptions import ClientError


class VPCsMng:
    def __init__(self, region_name: str):
        self.region_name = region_name
        self.ec2_client = self.get_ec2_client()
        self.default_vpc_ids = self.get_default_vpc_ids()

    def get_ec2_client(self):
        ec2_config = Config(region_name=self.region_name)
        return boto3.client("ec2", config=ec2_config)

    def get_default_vpc_ids(self):
        filters = [{"Name": "is-default", "Values": ["true"]}]
        response = self.ec2_client.describe_vpcs(Filters=filters)
        return [vpc["VpcId"] for vpc in response["Vpcs"]]

    def delete(self, vpc_id: str, dry_run: str):
        try:
            print(f"INFO: Deleting VPC: {vpc_id}")
            self.ec2_client.delete_vpc(VpcId=vpc_id, DryRun=dry_run)
        except ClientError as e:
            if e.response["Error"]["Code"] == "DryRunOperation":
                print(
                    f"INFO: [DRY RUN SUCCESS] Request verified. {vpc_id} would be deleted in a live run."
                )
            else:
                print(
                    f"ERROR: Failed to detach {vpc_id}: {e.response['Error']['Message']}"
                )
                raise

    def clean(self, dry_run: str):
        print(f"INFO: VPCs to be deleted count: {len(self.default_vpc_ids)}")
        [self.delete(vpc_id=vpc_id, dry_run=dry_run) for vpc_id in self.default_vpc_ids]

    def __str__(self):
        return f"INFO: {self.region_name} - default VPCs count: {len(self.default_vpc_ids)}"
