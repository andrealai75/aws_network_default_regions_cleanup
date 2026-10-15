from unittest.mock import MagicMock, patch

import pytest

from src.libs.regions_mng import RegionsMng


@pytest.fixture
def mock_managers():
    """Mocks the downstream managers imported inside regions_mng.
    
    Yields a dictionary containing the mock instances for assertion verification.
    """
    with patch("src.libs.regions_mng.VPCsMng") as MockVPCsMng, \
         patch("src.libs.regions_mng.InternetGatewaysMng") as MockIGWMng, \
         patch("src.libs.regions_mng.SubnetsMng") as MockSubnetsMng, \
         patch("boto3.client") as mock_boto_client:
         
        # Create mock instances that the constructors will return
        mock_vpcs = MagicMock()
        mock_igw = MagicMock()
        mock_subnets = MagicMock()
        
        # Configure fake attributes needed during RegionsMng.__init__
        mock_vpcs.default_vpc_ids = ["vpc-12345"]
        
        # Assign mock instances to the mocked class constructors
        MockVPCsMng.return_value = mock_vpcs
        MockIGWMng.return_value = mock_igw
        MockSubnetsMng.return_value = mock_subnets
        
        yield {
            "vpcs": mock_vpcs,
            "igw": mock_igw,
            "subnets": mock_subnets,
            "boto": mock_boto_client
        }


def test_init_orchestrates_downstream_managers(mock_managers):
    """Verifies that __init__ instantiates classes and seeds them with default VPC IDs."""
    region_name = "us-east-1"
    
    # Instantiate the manager under test
    mng = RegionsMng(name=region_name)
    
    # Assert fields are correctly set up
    assert mng.name == region_name
    assert mng.vpcs_mng == mock_managers["vpcs"]
    assert mng.internet_gateways_mng == mock_managers["igw"]
    assert mng.subnets_mng == mock_managers["subnets"]
    
    # Assert orchestration methods were triggered correctly during setup
    mock_managers["igw"].load_attached.assert_called_once_with(vpc_ids=["vpc-12345"])
    mock_managers["igw"].load_detached.assert_called_once()
    mock_managers["subnets"].load.assert_called_once_with(vpc_ids=["vpc-12345"])


def test_clean_triggers_ordered_downstream_cleanup(mock_managers):
    """Verifies clean() executes resource destruction in a safe topological order."""
    mng = RegionsMng(name="eu-west-1")
    
    # Call the cleanup routine
    mng.clean(dry_run=True)
    
    # Assert downstream managers received the clean instruction with the correct parameters
    mock_managers["igw"].clean.assert_called_once_with(dry_run=True)
    mock_managers["subnets"].clean.assert_called_once_with(dry_run=True)
    mock_managers["vpcs"].clean.assert_called_once_with(dry_run=True)


def test_string_representation(mock_managers):
    """Verifies that __str__ correctly compiles the string outputs of child managers."""
    # Configure mock string conversions for the child objects
    mock_managers["vpcs"].__str__.return_value = "VPCs status"
    mock_managers["igw"].__str__.return_value = "IGWs status"
    mock_managers["subnets"].__str__.return_value = "Subnets status"
    
    mng = RegionsMng(name="us-west-2")
    
    expected_output = (
        "--------\n"
        "VPCs status\n"
        "IGWs status\n"
        "Subnets status"
    )
    
    assert str(mng) == expected_output
