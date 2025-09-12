import './styles/simple-chat.css';

// Example message data structure
// const messages = [
//   { id: 1, 
//     sender: 'bot', 
//     text: 'Hello! How can I assist you today?',
//     intro: string, 
//     options: [{ title, reason, stock, url }]}
// ];
function SimpleChat({messages}) {
    return (
        <div className="chat-messages">
        {messages.map((msg) => (
          <div className="chat-message" key={msg.id}>
            <div className={`chat-bubble ${msg.sender}`}>
              {msg.text}
            </div>
          </div>
        ))}
      </div>
    );
}

export {SimpleChat};