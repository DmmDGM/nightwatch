// Copyright (c) 2024 iiPython

const CHARSET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";

export default class ConnectionManager {
    constructor(payload, callbacks) {
        this.callbacks = callbacks;
        const { username, hex, address } = payload;

        // Handle host and port
        let [ host, port ] = address.split(":");
        port = port ? Number(port) : 443;

        this.url = `${host}:${port}`
        this.protocol = port === 443 ? "s" : "";

        // Perform token authentication
        this.#authenticate(username, hex);
    }
    
    async #connect(authorization) {
        this.websocket = new WebSocket(`ws${this.protocol}://${this.url}/api/ws?authorization=${authorization}`);
        this.websocket.addEventListener("open", async () => {
            this.websocket.addEventListener("message", (e) => this.#on_message(e));
            this.callbacks.on_connect();

            // Reload user list
            const users = (await this.send({ type: "user-list" }, true))["user-list"];
            for (const user of users) this.callbacks.handle_member("join", user);
        });
        this.websocket.addEventListener("close", _ => console.warn("Connection closed"));
        this.websocket.addEventListener("error", e => console.error(e));
    }

    async #authenticate(username, hex) {
        const response = await (await fetch(
            `http${this.protocol}://${this.url}/api/join`,
            {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ username, hex })
            }
        )).json();
        console.log(`[Connection] Authorization code is ${response.authorization}`);
        
        // Establish websocket connection
        this.#connect(response.authorization);
    }

    #on_message(event) {
        const { type, data } = JSON.parse(event.data);
        console.log(`[!]`, { type, data });
        if (data.callback in this.callbacks) {
            this.callbacks[data.callback](data);
            delete this.callbacks[data.callback];
            return;
        };
        switch (type) {
            case "message":
                this.callbacks.on_message(data);
                break

            case "rics-info":
                document.getElementById("server-name").innerText = data.name;
                break;

            case "join":
            case "leave":
                this.callbacks.handle_member(type, data.user);
                break

            case "message-log":
                for (const message of data) this.callbacks.on_message(message);
                break;

            case "problem":
                console.warn({ type, data });
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

    async send(payload, is_callback) {
        if (is_callback) {
            if (!payload.data) payload.data = {};
            payload.data.callback = this.#generate_callback();
            this.websocket.send(JSON.stringify(payload));
            return new Promise((resolve) => { this.callbacks[payload.data.callback] = resolve; });
        };
        this.websocket.send(JSON.stringify(payload));
    }
}
