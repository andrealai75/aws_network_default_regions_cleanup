import boto3
from botocore.config import Config
from botocore.exceptions import ClientError


class InternetGatewaysMng:
    def __init__(self, region_name: str):
        self.region_name = region_name
        self.ec2_client = self.get_ec2_client()

    def get_ec2_client(self):
        ec2_config = Config(region_name=self.region_name)
        return boto3.client("ec2", config=ec2_config)

    def get_info(self, gateway_id: str, vpc_id: str, status: str):
        return {"gateway_id": gateway_id, "vpc_id": vpc_id, "status": status}

    def load_attached(self, vpc_ids: list):
        self.attached_info = []
        for vpc_id in vpc_ids:
            filters = [{"Name": "attachment.vpc-id", "Values": [vpc_id]}]
            gateways = self.ec2_client.describe_internet_gateways(Filters=filters)[
                "InternetGateways"
            ]
            if len(gateways) > 0:
                self.attached_info.append(
                    self.get_info(gateways[0]["InternetGatewayId"], vpc_id, "attached")
                )

    def load_detached(self):
        gateways = self.ec2_client.describe_internet_gateways()["InternetGateways"]
        self.detached_info = [
            self.get_info(gateway["InternetGatewayId"], None, "detached")
            for gateway in gateways
            if not gateway["Attachments"]
        ]

    def clean(self, dry_run: bool):
        self.detach(dry_run=dry_run)
        self.delete(dry_run=dry_run)

    def detach(self, dry_run: bool):
        for gateway_info in self.attached_info:
            try:
                print(
                    f"Detaching Gateway: {gateway_info['gateway_id']} - Dry Run ({dry_run})"
                )
                self.ec2_client.detach_internet_gateway(
                    DryRun=dry_run,
                    InternetGatewayId=gateway_info["gateway_id"],
                    VpcId=gateway_info["vpc_id"],
                )
            except ClientError as e:
                if e.response["Error"]["Code"] == "DryRunOperation":
                    print(
                        f"INFO: [DRY RUN SUCCESS] Request verified. {gateway_info['gateway_id']} would be detached in a live run."
                    )
                else:
                    print(
                        f"ERROR: Failed to detach {gateway_info['gateway_id']}: {e.response['Error']['Message']}"
                    )
                    raise

    def delete(self, dry_run: bool):
        for gateway_info in self.attached_info + self.detached_info:
            try:
                print(f"Deleting : {gateway_info['gateway_id']} - Dry Run ({dry_run})")
                self.ec2_client.delete_internet_gateway(
                    DryRun=dry_run, InternetGatewayId=gateway_info["gateway_id"]
                )
            except ClientError as e:
                if e.response["Error"]["Code"] == "DryRunOperation":
                    print(
                        f"INFO: [DRY RUN SUCCESS] Request verified. {gateway_info['gateway_id']} would be deleted in a live run."
                    )
                else:
                    print(
                        f"ERROR: Failed to delete {gateway_info['gateway_id']}: {e.response['Error']['Message']}"
                    )
                    raise

    def __str__(self):
        ret_value = f"INFO: {self.region_name} - Default attached Internet Gateway Count: {len(self.attached_info)}\n"
        ret_value += f"INFO: {self.region_name} - Default detached Internet Gateways count: {len(self.detached_info)}"
        return ret_value
