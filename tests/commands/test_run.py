import pytest
from unittest.mock import Mock, patch
from ispawn.commands.run import parse_services, run_container
from ispawn.domain.container import Service, ContainerConfig
from ispawn.domain.exceptions import ConfigurationError

def test_parse_services_valid():
    """Test parsing valid service strings."""
    services = parse_services("jupyter,rstudio")
    assert len(services) == 2
    assert Service.JUPYTER in services
    assert Service.RSTUDIO in services

def test_parse_services_invalid():
    """Test parsing invalid service strings."""
    with pytest.raises(ValueError):
        parse_services("jupyter,invalid")

def test_parse_services_whitespace():
    """Test parsing service strings with whitespace."""
    services = parse_services(" jupyter  rstudio ")
    assert len(services) == 2
    assert Service.JUPYTER in services
    assert Service.RSTUDIO in services


@patch('ispawn.commands.run.Config')
@patch('ispawn.commands.run.DockerService')
def test_run_container_success(mock_docker_service, mock_config_class,
                             mock_args, mock_config, mock_docker, capsys):
    """Test successful container run."""
    # Setup mocks
    mock_config_class.return_value = mock_config
    mock_docker_service.return_value = mock_docker
    # Setup mock config
    mock_config.container_prefix = "ispawn"
    mock_config.network_name = "ispawn-network"
    mock_config.domain = "ispawn.test"
    mock_config.cert_mode.value = "provided"
    mock_config.log_dir = None
    mock_config.subnet = "172.30.0.0/24"

    # Setup mock args
    mock_args.services = "jupyter"
    mock_args.name = "test"
    mock_args.image = "test:latest"
    mock_args.username = None
    mock_args.password = None
    mock_args.uid = None
    mock_args.gid = None
    mock_args.dns = None
    mock_args.volumes = None
    mock_args.force = False

    # Run command
    run_container(mock_args)

    # Verify container was created and started
    mock_docker.run_container.assert_called_once()
    captured = capsys.readouterr()
    assert "Docker container 'ispawn-test' is running." in captured.out

@patch('ispawn.commands.run.Config')
@patch('ispawn.commands.run.DockerService')
def test_run_container_image_not_found(mock_docker_service, mock_config_class,
                                     mock_args, mock_config, mock_docker):
    """Test handling of missing image."""
    mock_config_class.return_value = mock_config
    mock_docker_service.return_value = mock_docker
    mock_docker.get_image.return_value = None
    # Setup mock config
    mock_config.container_prefix = "ispawn"
    mock_config.network_name = "ispawn-network"
    mock_config.domain = "ispawn.test"
    mock_config.cert_mode.value = "provided"
    mock_config.log_dir = None
    mock_config.subnet = "172.30.0.0/24"

    # Setup mock args
    mock_args.services = "jupyter"
    mock_args.name = "test"
    mock_args.image = "nonexistent:latest"
    mock_args.username = None
    mock_args.password = None
    mock_args.uid = None
    mock_args.gid = None
    mock_args.dns = None
    mock_args.volumes = None
    mock_args.force = False

    with pytest.raises(SystemExit):
        run_container(mock_args)

@patch('ispawn.commands.run.Config')
@patch('ispawn.commands.run.DockerService')
def test_run_container_with_volumes(mock_docker_service, mock_config_class,
                                  mock_args, mock_config, mock_docker):
    """Test container run with volume mounts."""
    mock_config_class.return_value = mock_config
    mock_docker_service.return_value = mock_docker
    # Setup mock config
    mock_config.container_prefix = "ispawn"
    mock_config.network_name = "ispawn-network"
    mock_config.domain = "ispawn.test"
    mock_config.cert_mode.value = "provided"
    mock_config.log_dir = None
    mock_config.subnet = "172.30.0.0/24"

    # Setup mock args
    mock_args.services = "jupyter"
    mock_args.name = "test"
    mock_args.image = "test:latest"
    mock_args.username = None
    mock_args.password = None
    mock_args.uid = None
    mock_args.gid = None
    mock_args.volumes = "/path1,/path2"
    mock_args.force = False

    run_container(mock_args)

    # Verify volumes were passed correctly
    call_args = mock_docker.run_container.call_args[1]
    config = call_args['config']
    assert len(config.get_volume_mounts()) == 2

@patch('ispawn.commands.run.Config')
@patch('ispawn.commands.run.DockerService')
def test_run_container_with_custom_user(mock_docker_service, mock_config_class,
                                      mock_args, mock_config, mock_docker):
    """Test container run with custom user settings."""
    mock_config_class.return_value = mock_config
    mock_docker_service.return_value = mock_docker
    # Setup mock config
    mock_config.container_prefix = "ispawn"
    mock_config.network_name = "ispawn-network"
    mock_config.domain = "ispawn.test"
    mock_config.cert_mode.value = "provided"
    mock_config.log_dir = None
    mock_config.subnet = "172.30.0.0/24"

    # Setup mock args
    mock_args.services = "jupyter"
    mock_args.name = "test"
    mock_args.image = "test:latest"
    mock_args.username = "testuser"
    mock_args.password = "testpass"
    mock_args.uid = 1001
    mock_args.gid = 1001
    mock_args.dns = None
    mock_args.volumes = None
    mock_args.force = False

    run_container(mock_args)

    # Verify user settings were passed correctly
    call_args = mock_docker.run_container.call_args[1]
    config = call_args['config']
    env = config.get_environment()
    assert env['USERNAME'] == "testuser"
    assert env['PASSWORD'] == "testpass"
    assert env['UID'] == "1001"
    assert env['GID'] == "1001"

@patch('ispawn.commands.run.Config')
@patch('ispawn.commands.run.DockerService')
def test_run_container_error_handling(mock_docker_service, mock_config_class,
                                    mock_args, mock_config, mock_docker):
    """Test error handling during container run."""
    mock_config_class.return_value = mock_config
    mock_docker_service.return_value = mock_docker
    mock_docker.run_container.side_effect = Exception("Test error")
    # Setup mock config
    mock_config.container_prefix = "ispawn"
    mock_config.network_name = "ispawn-network"
    mock_config.domain = "ispawn.test"
    mock_config.cert_mode.value = "provided"
    mock_config.log_dir = None
    mock_config.subnet = "172.30.0.0/24"

    # Setup mock args
    mock_args.services = "jupyter"
    mock_args.name = "test"
    mock_args.image = "test:latest"
    mock_args.username = None
    mock_args.password = None
    mock_args.uid = None
    mock_args.gid = None
    mock_args.dns = None
    mock_args.volumes = None
    mock_args.force = False

    with pytest.raises(SystemExit):
        run_container(mock_args)

@patch('ispawn.commands.run.Config')
@patch('ispawn.commands.run.DockerService')
def test_run_container_force_replace(mock_docker_service, mock_config_class,
                                   mock_args, mock_config, mock_docker):
    """Test force replacing an existing container."""
    mock_config_class.return_value = mock_config
    mock_docker_service.return_value = mock_docker
    # Setup mock config
    mock_config.container_prefix = "ispawn"
    mock_config.network_name = "ispawn-network"
    mock_config.domain = "ispawn.test"
    mock_config.cert_mode.value = "provided"
    mock_config.log_dir = None
    mock_config.subnet = "172.30.0.0/24"

    # Setup mock args
    mock_args.services = "jupyter"
    mock_args.name = "test"
    mock_args.image = "test:latest"
    mock_args.username = None
    mock_args.password = None
    mock_args.uid = None
    mock_args.gid = None
    mock_args.dns = None
    mock_args.volumes = None
    mock_args.force = True

    run_container(mock_args)

    # Verify force flag was passed
    call_args = mock_docker.run_container.call_args[1]
    assert call_args['force'] is True
