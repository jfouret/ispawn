from command_runner import command_runner
import platform
import os
import sys
import yaml
from jinja2 import Template
from tempfile import TemporaryDirectory, NamedTemporaryFile

def input_yn(prompt):
  while True:
    response = input(prompt).lower()[0]
    if response in ["y","n"]:
      break
    else:
      print("Please answer with 'y' or 'n'.")
  return response == "y"

# Get OS information for package management
OS_ID = platform.freedesktop_os_release()["ID_LIKE"].lower()
COMPOSE_TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), '..',
  'templates', 'traefik_compose.yml.j2')
SHARED_PROVIDERS_DYNAMIC_PATH = os.path.join(os.path.dirname(__file__), '..',
  'files', 'shared_providers_dynamic.yml')
TRAEFIK_PATH = os.path.join(os.path.dirname(__file__), '..',
  'files', 'traefik.yml')
CARGS= {"shell":True, "live_output":True}

def run_commands(commands, as_sudo = False, work_dir = None):
  if not (type(commands) is list or type(commands) is tuple):
    commands = [commands]
  for command in commands:
    if work_dir:
      command = f"cd {work_dir} && {command}"
    if as_sudo:
      command = command.replace("'", "'\\''")
      command = f"sudo bash -c '{command}'"
    print("### Running command ###")
    print(command)
    print("### --- ###")
    rc,_ = command_runner(command, **CARGS)
    if rc != 0:
      print("### Error running command", file=sys.stderr)
      sys.exit(1)

class ISpawnSetup:
  def __init__(self, args):
    if args.mode == "remote":
      if not args.cert or not args.key:
        print("--cert and --key are required when --mode is 'remote'",
          file=sys.stderr)
        sys.exit(1)
    elif args.mode == "local":
      if not args.domain.endswith(".localhost"):
        print("--domain must not end with '.localhost' when --mode is 'local'",
          file=sys.stderr)
        sys.exit(1)
    self.args = args
    self.sys_config_dir = f"/etc/ispawn"
    commands = []
    if not os.path.exists(self.sys_config_dir):
      commands.append(f"mkdir -p {self.sys_config_dir}")
      commands.append(f"chmod 755 {self.sys_config_dir}")
    self.sys_config_file = f"{self.sys_config_dir}/config.yml"
    self.sys_cert_dir = f"{self.sys_config_dir}/certs"
    if not os.path.exists(self.sys_cert_dir):
      commands.append(f"mkdir -p {self.sys_cert_dir}")
      commands.append(f"chmod 700 {self.sys_cert_dir}")
    # compose file for traefik
    run_commands(commands, as_sudo=True)
    self.sys_compose_file = f"{self.sys_config_dir}/compose.yml"
    self.check_root()
    self.config_web()

  def check_root(self):
    """Ensure script is not run as root"""
    if os.geteuid() == 0:
      print(
        "This script shall not be ran as root, please run it as a normal user.",
        file=sys.stderr)
      sys.exit(1)
    run_commands(["sudo true"], as_sudo=True)

  def install_mkcert(self):
    """Install mkcert if not present"""
    if os.path.isfile("/usr/local/bin/mkcert"):
      print("mkcert is already installed.")
      return

    if not input_yn(
        "mkcert is not installed, do you want to install it? [y/n]"
      ):
      print("mkcert is required for ispawn to work in local mode.",
        file=sys.stderr)
      sys.exit(1)

    if "debian" in OS_ID:
      run_commands(["apt-get install libnss3-tools"], as_sudo = True)
    elif "fedora" in OS_ID or "rhel" in OS_ID:
      run_commands(["yum install nss-tools"], as_sudo = True)
    else:
      print("Unsupported OS", file=sys.stderr)
      sys.exit(1)

    with TemporaryDirectory() as tmp_dir:
      commands = [
        "curl -JLO \"https://dl.filippo.io/mkcert/v1.4.4?for=linux/amd64\"",
        "chmod 777 mkcert-v1.4.4-linux-amd64",
        "cp mkcert-v1.4.4-linux-amd64 /usr/local/bin/mkcert"
      ]
      run_commands(commands, as_sudo=True, work_dir=tmp_dir)
  
  def config_web(self):
    """Configure web access settings"""

    config_dict = {}
    if os.path.exists(self.sys_config_file):
      with open(self.sys_config_file, "r") as f:
        config_dict = yaml.safe_load(f) or {}

    web_config = {
      "domain": self.args.domain,
      "mode": self.args.mode
    }

    if web_config["mode"] == "remote":
      print("Important: Make sure you DNS setting is correct.")
      cert_path = self.args.cert
      key_path = self.args.key
      if not os.path.exists(cert_path) or not os.path.exists(key_path):
        print("Invalid certificate or key path.", file=sys.stderr)
        sys.exit(1)
    else:
      cert_path = os.path.join(self.sys_cert_dir, "cert.pem")
      key_path = os.path.join(self.sys_cert_dir, "key.pem")

    web_config.update({"cert_path": cert_path, "key_path": key_path})
    config_dict["web"] = web_config

    if web_config["mode"] == "local":
      self.setup_certificates(config_dict)

    config_dict["name"] = self.args.name_prefix
    config_dict["subnet"] =  self.args.subnet

    with NamedTemporaryFile(mode='w+') as tmp_file:
      yaml.dump(config_dict, tmp_file)
      tmp_file.flush()
      run_commands(
        [f"cp {tmp_file.name} {self.sys_config_file}",
        f"chmod 644 {self.sys_config_file}"],
        as_sudo=True)
    
    run_commands(
      [
        " ".join([
          f"cp {SHARED_PROVIDERS_DYNAMIC_PATH}",
          f"{self.sys_config_dir}/shared_providers_dynamic.yml"
        ]),
        f"chmod 644 {self.sys_config_dir}/shared_providers_dynamic.yml",
        " ".join([
          f"cp {TRAEFIK_PATH}",
          f"{self.sys_config_dir}/traefik.yml"
        ]),
        f"chmod 644 {self.sys_config_dir}/traefik.yml"
      ],
      as_sudo=True
    )

    if self.args.env_file is not None:
      env_abspath = os.path.abspath(self.args.env_file)
      run_commands(
        [
          " ".join([
            f"cp {env_abspath}",
            f"{self.sys_config_dir}/environment"
          ]),
          f"chmod 644 {self.sys_config_dir}/environment"
        ],
        as_sudo=True
      )
    if self.args.setup_file is not None:
      setup_abspath = os.path.abspath(self.args.setup_file)
      run_commands(
        [
          " ".join([
            f"cp {setup_abspath}",
            f"{self.sys_config_dir}/setup"
          ]),
          f"chmod 600 {self.sys_config_dir}/setup"
        ],
        as_sudo=True
      )
    self.start_traefik(config_dict)

  def setup_certificates(self, config):
    """Setup SSL certificates using mkcert"""
    if config["web"]["mode"] != "local":
      return

    self.install_mkcert()

    domain = config["web"]["domain"]
    with TemporaryDirectory() as tmp_dir:
      commands = [
        f"mkcert -install",
        " ".join([
          f"mkcert",
          f"-cert-file {tmp_dir}/cert.pem",
          f"-key-file {tmp_dir}/key.pem",
          f"\"*.{domain}\" \"{domain}\""
        ])
      ]
      run_commands(commands, work_dir=tmp_dir)
      commands = [
        f"mkdir -p {self.sys_cert_dir}",
        f"cp {tmp_dir}/cert.pem {self.sys_cert_dir}/cert.pem",
        f"cp {tmp_dir}/key.pem {self.sys_cert_dir}/key.pem",
        f"chown -R root:root {self.sys_cert_dir}",
        f"chmod 644 {self.sys_cert_dir}/cert.pem",
        f"chmod 600 {self.sys_cert_dir}/key.pem"
      ]
      run_commands(commands, as_sudo=True)

    return True

  def start_traefik(self, config):
    """Start Traefik reverse proxy"""
    with open(COMPOSE_TEMPLATE_PATH, 'r') as file:
      dockerfile_template = Template(file.read())
    rendered_compose = dockerfile_template.render(**config)

    with NamedTemporaryFile(mode='w+') as tmp_file:
      tmp_file.write(rendered_compose)
      tmp_file.flush()
      run_commands(
        [f"cp {tmp_file.name} {self.sys_compose_file}",
        f"chmod 644 {self.sys_compose_file}"],
        as_sudo=True
      )

    run_commands(
      ["docker compose -f {} up -d".format(self.sys_compose_file)],
      as_sudo=True,
      work_dir=self.sys_config_dir
    )
