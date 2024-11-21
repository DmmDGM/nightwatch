// Copyright (c) 2024 iiPython

export const main = document.querySelector("main");
    
// Handle fetching info
async function fetch_item(prompt, input_id, placeholder, allow_default) {
    main.innerHTML = `
        <h3>Nightwatch</h3>
        <hr>
        <p>${prompt}</p>
        <input type = "text" id = "${input_id}" placeholder = "${placeholder}" autocomplete = "no">
        <button>Connect</button>
    `;
    return new Promise((resolve) => {
        document.querySelector("button").addEventListener("click", () => {
            const value = document.getElementById(input_id).value;
            if (!value && !allow_default) return alert("Missing input.");
            resolve(value || placeholder);
        });
    });
}

export async function grab_data(DEFAULT_SERVER) {
    const username = localStorage.getItem("username") ||
        await fetch_item("Please, select a username:", "username", "John Wick", false);

    localStorage.setItem("username", username);

    const address = localStorage.getItem("address") ||
        await fetch_item("Enter a server address to connect to:", "address", DEFAULT_SERVER, true);

    localStorage.setItem("address", address);
    return { username, address };
}
