from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from src.libs.subnets_mng import SubnetsMng


@pytest.fixture
def mock_ec2_client():
    """Provides a mocked EC2 client and patches the client initialization."""
    with patch("boto3.client") as mock_boto_client:
        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client
        yield mock_client


def test_init_sets_region_and_client(mock_ec2_client):
    """Verifies instantiation sets the correct attributes without calling AWS."""
    mng = SubnetsMng(region_name="eu-west-1")
    
    assert mng.region_name == "eu-west-1"
    assert mng.ec2_client == mock_ec2_client
    mock_ec2_client.describe_subnets.assert_not_called()


def test_load_fetches_subnets_by_vpc_ids(mock_ec2_client):
    """Verifies load() queries AWS using the provided VPC list filter."""
    mock_ec2_client.describe_subnets.return_value = {
        "Subnets": [{"SubnetId": "subnet-111"}, {"SubnetId": "subnet-222"}]
    }
    
    mng = SubnetsMng(region_name="us-east-1")
    mng.load(vpc_ids=["vpc-abc", "vpc-xyz"])
    
    # Assert correct filter format was passed to AWS
    mock_ec2_client.describe_subnets.assert_called_once_with(
        Filters=[{"Name": "vpc-id", "Values": ["vpc-abc", "vpc-xyz"]}]
    )
    # Assert ids are correctly extracted into the property list
    assert mng.subnet_ids == ["subnet-111", "subnet-222"]


def test_delete_success(mock_ec2_client):
    """Verifies a live (non-dry-run) delete executes successfully."""
    mng = SubnetsMng(region_name="us-east-1")
    
    mng.delete(subnet_id="subnet-111", dry_run="false")
    
    mock_ec2_client.delete_subnet.assert_called_once_with(
        SubnetId="subnet-111", DryRun="false"
    )


def test_delete_dry_run_success(mock_ec2_client):
    """Verifies that a DryRunOperation exception is caught and handled safely."""
    error_response = {"Error": {"Code": "DryRunOperation", "Message": "Request would succeed"}}
    mock_ec2_client.delete_subnet.side_effect = ClientError(error_response, "DeleteSubnet")
    
    mng = SubnetsMng(region_name="us-east-1")
    mng.delete(subnet_id="subnet-111", dry_run="true")
    
    mock_ec2_client.delete_subnet.assert_called_once_with(
        SubnetId="subnet-111", DryRun="true"
    )


def test_delete_other_client_error_raises(mock_ec2_client):
    """Verifies that unexpected exceptions (e.g. DependencyViolation) are re-raised."""
    error_response = {"Error": {"Code": "DependencyViolation", "Message": "Subnet has active interfaces"}}
    mock_ec2_client.delete_subnet.side_effect = ClientError(error_response, "DeleteSubnet")
    
    mng = SubnetsMng(region_name="us-east-1")
    
    with pytest.raises(ClientError):
        mng.delete(subnet_id="subnet-111", dry_run="false")


def test_clean_triggers_all_deletions(mock_ec2_client):
    """Verifies that calling clean() iterates through all loaded Subnet IDs."""
    mock_ec2_client.describe_subnets.return_value = {
        "Subnets": [{"SubnetId": "subnet-1"}, {"SubnetId": "subnet-2"}]
    }
    
    mng = SubnetsMng(region_name="us-east-1")
    mng.load(vpc_ids=["vpc-123"])
    mng.clean(dry_run="false")
    
    # Assert delete_subnet was called for every item in self.subnet_ids
    assert mock_ec2_client.delete_subnet.call_count == 2
    mock_ec2_client.delete_subnet.assert_any_call(SubnetId="subnet-1", DryRun="false")
    mock_ec2_client.delete_subnet.assert_any_call(SubnetId="subnet-2", DryRun="false")


def test_clean_without_load_raises_attribute_error(mock_ec2_client):
    """Verifies that calling clean() before load() raises an AttributeError."""
    mng = SubnetsMng(region_name="us-east-1")
    
    with pytest.raises(AttributeError):
        mng.clean(dry_run="false")


def test_string_representation(mock_ec2_client):
    """Verifies the custom __str__ formatting behaves correctly post-load."""
    mock_ec2_client.describe_subnets.return_value = {
        "Subnets": [{"SubnetId": "subnet-1"}]
    }
    
    mng = SubnetsMng(region_name="us-west-2")
    mng.load(vpc_ids=["vpc-123"])
    
    assert str(mng) == "INFO: us-west-2 - default Subnets count: 1"
