# ispawn

ispawn is a command line tool to spawn docker containers holding mutltiple services with a single command.

## About

0. Setup your system
- with `ispawn setup`, you can setup your system to access the services from your browser.
- It will start a reverse proxy traefik as a docker container.
- By default it will redirect your services from the container to URL for you to access all your services from your browser.
1. Build services 
- with `ispawn image`, you can build a docker image with multiple services (rstudio, jupyter, vscode)
- Basically it enrich any container image with 3 services: rstudio, jupyter and vscode.
- You can use any debian-based or ubuntu-based container image.
2. Run services
- with `ispawn run`, you can run a container with all services with a single command.
- Host volumes are automatically created, user is also mapped your your UID and GID.
- A password token can be specified or is generated.
- It also provides a reverse proxy to access the services from your browser.

## Example

```
pip install .
ispawn setup
ispawn image build --image quay.io/nexomis/r-nexoverse:4.4.1-08.24
ispawn run --name test --image quay.io/nexomis/r-nexoverse:4.4.1-08.24
```

Output:
```
Docker container 'ispawn-test' is running.
Access services at:
---
 - rstudio: https://rstudio-test.ispawn.localhost
   - Username: jfouret
   - Password: ZHZjILbD
---
 - jupyter: https://jupyter-test.ispawn.localhost?token=ZHZjILbD
---
 - vscode: https://vscode-test.ispawn.localhost?tkn=ZHZjILbD
---
```
