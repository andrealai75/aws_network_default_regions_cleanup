from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from src.libs.vpcs_mng import VPCsMng


@pytest.fixture
def mock_ec2_client():
    """Provides a mocked EC2 client and patches the client initialization."""
    with patch("boto3.client") as mock_boto_client:
        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client
        
        # Default mock response for describe_vpcs to avoid crashing during __init__
        mock_client.describe_vpcs.return_value = {"Vpcs": []}
        yield mock_client


def test_init_fetches_default_vpcs(mock_ec2_client):
    """Verifies that initialization calls describe_vpcs with correct true-filters."""
    mock_ec2_client.describe_vpcs.return_value = {
        "Vpcs": [{"VpcId": "vpc-12345"}, {"VpcId": "vpc-67890"}]
    }

    mng = VPCsMng(region_name="us-east-1")

    # Assert correct filters were sent to AWS
    mock_ec2_client.describe_vpcs.assert_called_once_with(
        Filters=[{"Name": "is-default", "Values": ["true"]}]
    )
    # Assert the list properties mapped correctly
    assert mng.default_vpc_ids == ["vpc-12345", "vpc-67890"]


def test_delete_success(mock_ec2_client):
    """Verifies a live (non-dry-run) delete executes successfully."""
    mng = VPCsMng(region_name="us-east-1")
    
    mng.delete(vpc_id="vpc-12345", dry_run="false")
    
    mock_ec2_client.delete_vpc.assert_called_once_with(
        VpcId="vpc-12345", DryRun="false"
    )


def test_delete_dry_run_success(mock_ec2_client):
    """Verifies that a DryRunOperation exception is caught and treated as a success."""
    # Build a simulated ClientError payload matching AWS structures
    error_response = {"Error": {"Code": "DryRunOperation", "Message": "Request would succeed"}}
    mock_ec2_client.delete_vpc.side_effect = ClientError(error_response, "DeleteVpc")
    
    mng = VPCsMng(region_name="us-east-1")
    
    # This shouldn't raise an exception because the class safely handles "DryRunOperation"
    mng.delete(vpc_id="vpc-12345", dry_run="true")
    
    mock_ec2_client.delete_vpc.assert_called_once_with(
        VpcId="vpc-12345", DryRun="true"
    )


def test_delete_other_client_error_raises(mock_ec2_client):
    """Verifies that other client errors (like missing permissions) are re-raised."""
    error_response = {"Error": {"Code": "UnauthorizedOperation", "Message": "Access Denied"}}
    mock_ec2_client.delete_vpc.side_effect = ClientError(error_response, "DeleteVpc")
    
    mng = VPCsMng(region_name="us-east-1")
    
    # Assert that this unhandled AWS exception cascades up the stack
    with pytest.raises(ClientError):
        mng.delete(vpc_id="vpc-12345", dry_run="false")


def test_clean_triggers_all_deletions(mock_ec2_client):
    """Verifies that calling clean() iterates through all discovered default VPCs."""
    mock_ec2_client.describe_vpcs.return_value = {
        "Vpcs": [{"VpcId": "vpc-1"}, {"VpcId": "vpc-2"}]
    }
    
    mng = VPCsMng(region_name="us-east-1")
    mng.clean(dry_run="false")
    
    # Assert delete_vpc was triggered for every ID in the list
    assert mock_ec2_client.delete_vpc.call_count == 2
    mock_ec2_client.delete_vpc.assert_any_call(VpcId="vpc-1", DryRun="false")
    mock_ec2_client.delete_vpc.assert_any_call(VpcId="vpc-2", DryRun="false")


def test_string_representation(mock_ec2_client):
    """Verifies the custom __str__ method formats text correctly."""
    mock_ec2_client.describe_vpcs.return_value = {"Vpcs": [{"VpcId": "vpc-1"}]}
    
    mng = VPCsMng(region_name="eu-west-1")
    
    assert str(mng) == "INFO: eu-west-1 - default VPCs count: 1"
