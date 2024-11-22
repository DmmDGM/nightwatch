// Copyright (c) 2024 iiPython

export const main = document.querySelector("main");
    
// Handle fetching info
class WelcomeHandler {
    constructor() {
        this.items = {
            username: {
                prompt: "Please, select a username:",
                placeholder: "John Wick"
            },
            color: {
                prompt: "Please, pick a user color:",
                placeholder: "126bf1"
            },
            address: {
                prompt: "Enter a server address to connect to:",
                placeholder: "nightwatch.iipython.dev"
            }
        };
        this.current_item = "username";
    }
    
    render_item(item) {
        const input = main.querySelector("input");

        // Save old data
        localStorage.setItem(this.current_item, input.value);
        this.current_item = item;

        // Handle input color immediately
        input.style.borderColor = this.current_item === "color" ? `#${localStorage.getItem("color")}` : "white";

        // Handle actual stuff
        main.querySelector("p").innerText = this.items[item].prompt;
        input.value = localStorage.getItem(item);
        input.placeholder = this.items[item].placeholder;
        main.querySelector("button:not([data-item])").innerText = item === "address" ? "Connect" : "Next";

        // Handle fancy animations for color
        if (this.current_item === "color") {
            input.addEventListener("keyup", (e) => {
                const hex_code = e.currentTarget.value;
                e.currentTarget.style.borderColor = `#${hex_code}`;
            });
        }
    }

    async menu() {
        main.innerHTML = `
            <h3>Nightwatch</h3>
            <div class = "tabs">
                <button data-item = "username">Username</button>
                <button data-item = "color">Color</button>
                <button data-item = "address">Address</button>
            </div>
            <hr>
            <p></p>
            <input type = "text" autocomplete = "no">
            <button>Connect</button>
        `;
        main.querySelector("input").value = localStorage.getItem("username");
        main.querySelector("button:not([data-item])").addEventListener("click", () => {
            localStorage.setItem(this.current_item, main.querySelector("input").value);
            if (this.current_item === "address") return this.resolve(localStorage);
            const buttons = Array.from(main.querySelectorAll("[data-item]"));
            const index = buttons.indexOf(main.querySelector(`[data-item = "${this.current_item}"]`));
            this.render_item(buttons[index + 1].getAttribute("data-item"));
        });
        for (const item of main.querySelectorAll("[data-item]")) item.addEventListener("click", () => {
            this.render_item(item.getAttribute("data-item"));
        });
        this.render_item(this.current_item);
        return new Promise((resolve) => { this.resolve = resolve; });
    }
}

export async function grab_data() {
    const handler = new WelcomeHandler();
    return handler.menu();
}
