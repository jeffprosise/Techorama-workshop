// Credit: https://emma-delaney.medium.com/how-to-create-your-own-chatgpt-in-html-css-and-javascript-78e32b70b4be
// Support for streaming output added by JDP

const chatInput = document.querySelector("#chat-input");
const sendButton = document.querySelector("#send-btn");
const chatContainer = document.querySelector(".chat-container");
const themeButton = document.querySelector("#theme-btn");
const deleteButton = document.querySelector("#delete-btn");
const micButton = document.querySelector("#mic-btn");

let threadID = "";
let userText = null;

const init = () => {
    // Forget the thread ID
    threadID = "";
    
    // Load theme from local storage and apply to the page
    const themeColor = localStorage.getItem("themeColor");

    document.body.classList.toggle("light-mode", themeColor === "light_mode");
    themeButton.innerText = document.body.classList.contains("light-mode") ? "dark_mode" : "light_mode";

    const defaultText = `<div class="default-text">
                            <h1>Ask LISA</h1>
                            <p>I'm LISA, your AI-powered virtual assistant.<br />How can I help you today?</p>
                        </div>`

    chatContainer.innerHTML = defaultText;
    chatContainer.scrollTo(0, chatContainer.scrollHeight); // Scroll to bottom of the chat container
}

const createChatElement = (content, className) => {
    // Create new div and apply chat, specified class and set html content of div
    const chatDiv = document.createElement("div");
    chatDiv.classList.add("chat", className);
    chatDiv.innerHTML = content;
    return chatDiv; // Return the created chat div
}

const streamChatResponse = async (incomingChatDiv) => {
    // Create a container to show the response
    var pElement = document.createElement("p");
    incomingChatDiv.querySelector(".chat-details").appendChild(pElement);

    try {
        // Call back to the server for a chat response
        var url = `/assistant?input=${userText}`;
        response = await fetch(url, { headers: { "X-Thread-ID": threadID }});

        // Save the thread ID for subsequent requests
        threadID = response.headers.get("X-Thread-ID");

        // Display the streaming response
        var reader = response.body.getReader();
        var decoder = new TextDecoder("utf-8");

        while (true) {
            var animation = incomingChatDiv.querySelector(".typing-animation")
            if (animation != null)
                animation.remove();

            var { done, value } = await reader.read();
            if (done)
                break;

            var chunk = decoder.decode(value, { stream: true });

            // If the chunk contains an image ID, download and display
            // the image. Otherwise, append the latest chunk of text to
            // the output.
            if (chunk.startsWith("[[[IMAGEID]]]")) {
                var file_id = chunk.slice(13);
                var url = `/image?id=${file_id}`
                var response = await fetch(url);
                var imgElement = document.createElement("img");
                imgElement.src = await response.text();
                imgElement.setAttribute("class", "chart");
                imgElement.setAttribute("alt", "llm-generated chart")
                pElement.parentNode.parentNode.appendChild(imgElement); // Add image to chat-container DIV
            }
            else {
                pElement.textContent += chunk;
            }

            chatContainer.scrollTo(0, chatContainer.scrollHeight);
        }
    }
    catch(error) {
        var animation = incomingChatDiv.querySelector(".typing-animation")
        if (animation != null)
            animation.remove();

        if (pElement.textContent.length == 0)
            pElement.textContent = `I'm sorry, but something went wrong (${error.message}).`;
        else
            pElement.textContent += `...I'm sorry, but something went wrong (${error.message}).`
    }
}

const showTypingAnimation = () => {
    // Display the typing animation and call the streamChatResponse function
    const html = `<div class="chat-content">
                    <div class="chat-details">
                        <img src="/static/chatbot.jpg" alt="chatbot-img">
                        <div class="typing-animation">
                            <div class="typing-dot" style="--delay: 0.2s"></div>
                            <div class="typing-dot" style="--delay: 0.3s"></div>
                            <div class="typing-dot" style="--delay: 0.4s"></div>
                        </div>
                    </div>
                </div>`;

    // Create an incoming chat div with typing animation and append it to chat container
    const incomingChatDiv = createChatElement(html, "incoming");
    chatContainer.appendChild(incomingChatDiv);
    chatContainer.scrollTo(0, chatContainer.scrollHeight);
    streamChatResponse(incomingChatDiv);
}

const handleOutgoingChat = () => {
    userText = chatInput.value.trim(); // Get chatInput value and remove extra spaces
    if(!userText) return; // If chatInput is empty return from here

    // Clear the input field and reset its height
    chatInput.value = "";
    chatInput.style.height = `${initialInputHeight}px`;

    const html = `<div class="chat-content">
                    <div class="chat-details">
                        <img src="/static/user.jpg" alt="user-img">
                        <p>${userText}</p>
                    </div>
                </div>`;

    // Create an outgoing chat div with user's message and append it to chat container
    const outgoingChatDiv = createChatElement(html, "outgoing");
    chatContainer.querySelector(".default-text")?.remove();
    chatContainer.appendChild(outgoingChatDiv);
    chatContainer.scrollTo(0, chatContainer.scrollHeight);
    setTimeout(showTypingAnimation, 500);
}

deleteButton.addEventListener("click", () => {
    // Delete the conversation
    if(confirm("Are you sure you want to delete the conversation?")) {
        init();
    }
});

themeButton.addEventListener("click", () => {
    // Toggle body's class for the theme mode and save the updated theme to the local storage 
    document.body.classList.toggle("light-mode");
    localStorage.setItem("themeColor", themeButton.innerText);
    themeButton.innerText = document.body.classList.contains("light-mode") ? "dark_mode" : "light_mode";
});

const initialInputHeight = chatInput.scrollHeight;

chatInput.addEventListener("input", () => {   
    // Adjust the height of the input field dynamically based on its content
    chatInput.style.height =  `${initialInputHeight}px`;
    chatInput.style.height = `${chatInput.scrollHeight}px`;
});

chatInput.addEventListener("keydown", (e) => {
    // If the Enter key is pressed without Shift and the window width is larger 
    // than 800 pixels, handle the outgoing chat
    if (e.key === "Enter" && !e.shiftKey && window.innerWidth > 800) {
        e.preventDefault();
        handleOutgoingChat();
    }
});

async function typewriter(text, el, delay=5) {
    for (let i = 0; i < text.length; i++) {
        await new Promise(resolve => setTimeout(resolve, delay));
        el.value += text[i];
        el.style.height =  `${initialInputHeight}px`;
        el.style.height = `${el.scrollHeight}px`;
    }
}

micButton.addEventListener("click", () => {
    chatInput.value = ''; // Clear any existing text
    window.SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.interimResults = false;

    recognition.addEventListener("result", async (e) => {
        // Get the spoken input as a text string
        var query = Array.from(e.results)
            .map(result => result[0])
            .map(result => result.transcript)
            .join('')

        // Insert the text into the input control
        await typewriter(query, chatInput);

        // Pass the question to the server
        handleOutgoingChat();
    });

    recognition.start();
});

init();
sendButton.addEventListener("click", handleOutgoingChat);