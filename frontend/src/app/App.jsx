
import { InputBar } from '../components/input-bar';
import './styles/App.css';

function App() {
  const [input, setInput] = useState("");
  // May want to keep messages in state for a real chat
  const simpleContent = { text: "Hello, this is a simple chat message." };

  const handleInputChange = (e) => setInput(e.target.value);
  const handleSend = () => {
    if (input.trim() === "") return;
    // Add send logic here (e.g., update messages state)
    setInput("");
  };

  return (
    <div className="App">
      <h1>TERRAIN Chatbot</h1>
      <InputBar value={input} onChange={handleInputChange} onSend={handleSend} />
    </div>
  );
}

export default App;
