<h1 align = "center">Nightwatch</h1>
<div align = "center">

![Python](https://img.shields.io/badge/Python-%3E=%203.10-4b8bbe?style=for-the-badge&logo=python&logoColor=white)
![Rust](https://img.shields.io/badge/Rust-%3E=%201.60-221f1e?style=for-the-badge&logo=rust&logoColor=white)

The chatting application to end all chatting applications. 

</div>

# Installation

As an end-user, you have multiple clients to pick from when it comes to accessing Nightwatch.  
Here are two of the standard clients for you to choose from:
- Terminal Client ([based on urwid](https://urwid.org/index.html))
    - Installation is as simple as `pip install nightwatch-chat`.
    - The client can be started by running `nightwatch` in your terminal.

- Full Desktop App ([based on tauri](https://tauri.app/))
    - Download the latest release for your system from [here](https://github.com/iiPythonx/nightwatch/releases/latest).
    - Alternatively, run it manually:
        - Follow the instructions from [Tauri prerequisites](https://tauri.app/v1/guides/getting-started/prerequisites) (including installing [Rust](https://rust-lang.org)).
        - Install the Tauri CLI: `cargo install tauri-cli`.
        - Launch via `cargo tauri dev` inside the `nightwatch/desktop/` folder.

# Server Installation

Running a Nightwatch server can be a bit trickier then running the client, but follow along:

```sh
git clone https://github.com/iiPythonx/nightwatch && cd nightwatch
git checkout release
uv venv
uv pip install -e .
HOST=0.0.0.0 python3 -m nightwatch.server
```

An example NGINX configuration:

```conf
server {

    # SSL
    listen			    443 ssl;
    ssl_certificate		/etc/ssl/nightwatch.pem;
    ssl_certificate_key	/etc/ssl/nightwatch.key;

    # Setup location
    server_name nightwatch.iipython.dev;
    location /gateway {
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection upgrade;
        proxy_pass http://192.168.0.1:8000/gateway;
        proxy_http_version 1.1;
    }
}
```

# Configuration

Configuration is available at:
- ***nix systems**: ~/.config/nightwatch/config.json
- **Windows**: %LocalAppData%\Nightwatch\config.json

The Nightwatch client uses the JSON for username, coloring, and more. Check the `/config` command for more information. 
The backend chat server uses the config file for the server name, although more is sure to come.
