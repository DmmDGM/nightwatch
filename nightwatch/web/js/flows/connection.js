// Copyright (c) 2024 iiPython

const CHARSET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";

export default class ConnectionManager {
    constructor(address, callbacks) {
        this.callbacks = callbacks;

        // Handle host and port
        const [ host, port ] = address.split(":");

        // Handle websocket connection
        this.websocket = new WebSocket(`ws${port === '443' ? 's' : ''}://${host}:${port || 443}/gateway`);
        this.websocket.addEventListener("open", () => {
            this.websocket.addEventListener("message", (e) => this.#on_message(e));
            this.callbacks.on_connect();
        });
        this.websocket.addEventListener("close", _ => console.warn("Connection closed"));
        this.websocket.addEventListener("error", e => console.error(e));
    }

    #on_message(event) {
        const data = JSON.parse(event.data);
        console.log("[E]", data);
        if (data.callback in this.callbacks) return this.callbacks[data.callback](data.data);
        switch (data.type) {
            case "message":
                this.callbacks.on_message(data.data);
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

    identify(username, color) {
        this.websocket.send(JSON.stringify({
            type: "identify",
            data: { name: username, color }
        }));
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
