from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from src.libs.internet_gateways_mng import InternetGatewaysMng


@pytest.fixture
def mock_ec2_client():
    """Provides a mocked EC2 client and patches the client initialization."""
    with patch("boto3.client") as mock_boto_client:
        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client
        yield mock_client


def test_init_sets_region_and_client(mock_ec2_client):
    """Verifies instantiation configures state without calling AWS APIs."""
    mng = InternetGatewaysMng(region_name="eu-west-1")
    
    assert mng.region_name == "eu-west-1"
    assert mng.ec2_client == mock_ec2_client
    mock_ec2_client.describe_internet_gateways.assert_not_called()


def test_load_attached_populates_valid_gateways(mock_ec2_client):
    """Verifies load_attached targets specific VPCs and maps responses into internal arrays."""
    # Mock return values for two individual VPC iterations
    mock_ec2_client.describe_internet_gateways.side_effect = [
        {"InternetGateways": [{"InternetGatewayId": "igw-111"}]},  # First VPC matches
        {"InternetGateways": []}                                   # Second VPC has no IGW
    ]
    
    mng = InternetGatewaysMng(region_name="us-east-1")
    mng.load_attached(vpc_ids=["vpc-1", "vpc-2"])
    
    # Assert query iterations match target inputs
    assert mock_ec2_client.describe_internet_gateways.call_count == 2
    mock_ec2_client.describe_internet_gateways.assert_any_call(
        Filters=[{"Name": "attachment.vpc-id", "Values": ["vpc-1"]}]
    )
    
    # Assert structural dictionary building matches spec
    assert mng.attached_info == [
        {"gateway_id": "igw-111", "vpc_id": "vpc-1", "status": "attached"}
    ]


def test_load_detached_filters_unattached_gateways(mock_ec2_client):
    """Verifies load_detached filters out IGWs that have an active 'Attachments' block."""
    mock_ec2_client.describe_internet_gateways.return_value = {
        "InternetGateways": [
            {"InternetGatewayId": "igw-active", "Attachments": [{"VpcId": "vpc-1"}]},
            {"InternetGatewayId": "igw-lonely", "Attachments": []}
        ]
    }
    
    mng = InternetGatewaysMng(region_name="us-east-1")
    mng.load_detached()
    
    mock_ec2_client.describe_internet_gateways.assert_called_once_with()
    assert mng.detached_info == [
        {"gateway_id": "igw-lonely", "vpc_id": None, "status": "detached"}
    ]


def test_clean_orchestrates_detach_then_delete(mock_ec2_client):
    """Verifies clean() coordinates dependencies by running detaches prior to deletes."""
    mng = InternetGatewaysMng(region_name="us-east-1")
    mng.attached_info = [{"gateway_id": "igw-111", "vpc_id": "vpc-1", "status": "attached"}]
    mng.detached_info = [{"gateway_id": "igw-222", "vpc_id": None, "status": "detached"}]
    
    mng.clean(dry_run=False)
    
    # Verify detach executed with appropriate signature params
    mock_ec2_client.detach_internet_gateway.assert_called_once_with(
        DryRun=False, InternetGatewayId="igw-111", VpcId="vpc-1"
    )
    # Verify both got targeted for destruction
    assert mock_ec2_client.delete_internet_gateway.call_count == 2


def test_dry_run_exceptions_are_caught(mock_ec2_client):
    """Verifies that DryRunOperation blocks do not cause testing executions to fail."""
    error_response = {"Error": {"Code": "DryRunOperation", "Message": "DryRun call simulated"}}
    mock_ec2_client.detach_internet_gateway.side_effect = ClientError(error_response, "Detach")
    mock_ec2_client.delete_internet_gateway.side_effect = ClientError(error_response, "Delete")
    
    mng = InternetGatewaysMng(region_name="us-east-1")
    mng.attached_info = [{"gateway_id": "igw-111", "vpc_id": "vpc-1", "status": "attached"}]
    mng.detached_info = []
    
    # Execution shouldn't throw error
    mng.clean(dry_run=True)


def test_unexpected_client_errors_bubble_up(mock_ec2_client):
    """Verifies that standard infrastructure failures (e.g., AccessDenied) throw immediately."""
    error_response = {"Error": {"Code": "AuthFailure", "Message": "Invalid credentials"}}
    mock_ec2_client.detach_internet_gateway.side_effect = ClientError(error_response, "Detach")
    
    mng = InternetGatewaysMng(region_name="us-east-1")
    mng.attached_info = [{"gateway_id": "igw-111", "vpc_id": "vpc-1", "status": "attached"}]
    
    with pytest.raises(ClientError):
        mng.clean(dry_run=False)


def test_string_representation(mock_ec2_client):
    """Verifies string templates capture current property array length totals."""
    mng = InternetGatewaysMng(region_name="us-west-2")
    mng.attached_info = [{"gateway_id": "igw-1"}]
    mng.detached_info = [{"gateway_id": "igw-2"}, {"gateway_id": "igw-3"}]
    
    expected = (
        "INFO: us-west-2 - Default attached Internet Gateway Count: 1\n"
        "INFO: us-west-2 - Default detached Internet Gateways count: 2"
    )
    assert str(mng) == expected
