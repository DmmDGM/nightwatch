// Copyright (c) 2024 iiPython

const CHARSET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";

export default class ConnectionManager {
    constructor(address, callbacks) {
        this.callbacks = callbacks;

        // Handle host and port
        let [ host, port ] = address.split(":");
        port = port ? Number(port) : 443;

        // Handle websocket connection
        this.websocket = new WebSocket(`ws${port === 443 ? 's' : ''}://${host}:${port}/gateway`);
        this.websocket.addEventListener("open", () => {
            this.websocket.addEventListener("message", (e) => this.#on_message(e));
            this.callbacks.on_connect();
        });
        this.websocket.addEventListener("close", _ => console.warn("Connection closed"));
        this.websocket.addEventListener("error", e => console.error(e));
    }

    #on_message(event) {
        const data = JSON.parse(event.data);
        if (data.callback in this.callbacks) {
            this.callbacks[data.callback](data.data);
            delete this.callbacks[data.callback];
            return;
        };
        switch (data.type) {
            case "message":
                this.callbacks.on_message(data.data);
                break

            case "server":
                document.getElementById("server-name").innerText = data.data.name;
                break;

            case "join":
            case "leave":
                this.callbacks.handle_member(data.type, data.data.name);
                break

            case "error":
                console.error(data);
                break;
        }
    }

    #generate_callback = () => {
        let result = "";
        for (let i = 0; i < 10; i++) {
            const randomIndex = Math.floor(Math.random() * CHARSET.length);
            result += CHARSET[randomIndex];
        }
        return result;
    };

    async identify(username, color) {
        this.websocket.send(JSON.stringify({
            type: "identify",
            data: { name: username, color }
        }));

        // Handle initial member list
        for (const member of (await this.send({ type: "members" }, true)).list) this.callbacks.handle_member("join", member);
    }

    async send(payload, is_callback) {
        if (is_callback) {
            payload.callback = this.#generate_callback();
            this.websocket.send(JSON.stringify(payload));
            return new Promise((resolve) => { this.callbacks[payload.callback] = resolve; });
        };
        this.websocket.send(JSON.stringify(payload));
    }
}
