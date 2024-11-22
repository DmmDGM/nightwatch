// Copyright (c) 2024 iiPython

import ConnectionManager from "./flows/connection.js";
import { main, grab_data } from "./flows/welcome.js";

// Couple constants
const TIME_FORMATTER = new Intl.DateTimeFormat("en-US", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: true
});

(async () => {
    const { username, color, address } = await grab_data();

    // Keep track of the last message
    let last_author, last_time;

    // Connection screen
    const connection = new ConnectionManager(address, {
        on_connect: () => {
            connection.identify(username, color);

            // Remove loading and setup UI
            main.classList.remove("loading");
            main.classList.add("full-layout");
            main.innerHTML = `
                <div class = "chat-input">
                    <div class = "chat"></div>
                    <div class = "input-box">
                        <input type = "text" id = "actual-input" placeholder = "Share some thoughts...">
                        <button>Send</button>
                    </div>
                </div>
                <div class = "member-list">
                    <button id = "leave">LEAVE SERVER</button>
                    <p>Current member list:</p>
                </div>
            `;

            // Handle sending
            const input = document.getElementById("actual-input");
            function send_message() {
                if (!input.value.trim()) return;
                connection.send({ type: "message", data: { text: input.value } });
                input.value = "";
            }
            input.addEventListener("keydown", (e) => { if (e.key === "Enter") send_message(); });
            document.querySelector(".chat-input button").addEventListener("click", send_message);

            // Handle leaving
            document.getElementById("leave").addEventListener("click", () => {
                window.location.reload();  // Fight me.
            });
        },
        on_message: (message) => {
            const current_time = TIME_FORMATTER.format(new Date(message.time * 1000));

            // Check for anything hidden
            const hide_author = message.user.name === last_author;
            const hide_time = !hide_author ? false : current_time === last_time;
            last_author = message.user.name, last_time = current_time;

            // Construct text/attachment
            let attachment = message.text, classlist = "message-content";
            if (attachment.match(/^https:\/\/[\w\d./-]+.(?:avif|png|jpg|jpeg|webp|ico)$/)) {
                attachment = `<img src = "${attachment}">`;
                classlist += " has-image";
            } else {

                // Clean attachment for the love of god
                attachment = attachment.replace(/&/g, "&amp;")
                                .replace(/</g, "&lt;")
                                .replace(/>/g, "&gt;")
                                .replace(/"/g, "&quot;")
                                .replace(/"/g, "&#039;");
            };

            // Construct message
            const element = document.createElement("div");
            element.classList.add("message");
            element.innerHTML = `
                <span style = "color: #${message.user.color};${hide_author ? 'color: transparent;' : ''}">${message.user.name}</span>
                <span class = "${classlist}">${attachment}</span>
                <span class = "timestamp"${hide_time ? ' style="color: transparent;"' : ''}>${current_time}</span>
            `;

            // Push message and autoscroll
            const chat = document.querySelector(".chat");
            chat.appendChild(element);
            chat.scrollTop = chat.scrollHeight; 
        },
        handle_member: (event_type, member_name) => {
            const member_list = document.querySelector(".member-list");
            const existing_member = document.querySelector(`[data-member = "${member_name}"]`);
            if (event_type === "leave") {
                if (existing_member) existing_member.remove();
                return;
            }
            if (existing_member) return;

            // Handle element
            const element = document.createElement("span");
            element.innerText = `→ ${member_name}`;
            element.setAttribute("data-member", member_name);
            member_list.appendChild(element);
        }
    });

    // Handle loading spinner
    main.classList.add("loading");
    main.innerHTML = `<span class = "loader"></span> Connecting to ${address}...`;
})();
