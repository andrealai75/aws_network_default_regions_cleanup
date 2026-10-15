import boto3
from botocore.config import Config
from botocore.exceptions import ClientError


class SubnetsMng:
    def __init__(self, region_name: str):
        self.region_name = region_name
        self.ec2_client = self.get_ec2_client()

    def get_ec2_client(self):
        ec2_config = Config(region_name=self.region_name)
        return boto3.client("ec2", config=ec2_config)

    def load(self, vpc_ids: list):
        filters = [{"Name": "vpc-id", "Values": vpc_ids}]
        subnets = self.ec2_client.describe_subnets(Filters=filters)["Subnets"]
        self.subnet_ids = [subnet["SubnetId"] for subnet in subnets]

    def delete(self, subnet_id: str, dry_run: str):
        try:
            print(f"INFO: Deleting Subnet: {subnet_id}")
            self.ec2_client.delete_subnet(SubnetId=subnet_id, DryRun=dry_run)
        except ClientError as e:
            if e.response["Error"]["Code"] == "DryRunOperation":
                print(
                    f"INFO: [DRY RUN SUCCESS] Request verified. {subnet_id} would be deleted in a live run."
                )
            else:
                print(
                    f"ERROR: Failed to detach {subnet_id}: {e.response['Error']['Message']}"
                )
                raise

    def clean(self, dry_run: str):
        print(f"INFO: Subnets to be delete: {len(self.subnet_ids)}")
        [self.delete(subnet_id=subnet_id, dry_run=dry_run) for subnet_id in self.subnet_ids]

    def __str__(self):
        return (
            f"INFO: {self.region_name} - default Subnets count: {len(self.subnet_ids)}"
        )
