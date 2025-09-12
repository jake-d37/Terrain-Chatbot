//bubble for chat
import '.styles/chat-wrapper.css';
import { SimpleChat } from './simple-chat';
import { Item } from './item';
import { Recommendation } from './recommendation';

//content must be an object
//chattype must match object values or error
function ChatWrapper({ chatType, messages }) {
    let content = null;
    if (chatType === 'simple-text') {
        content = <SimpleChat messages={messages} />;
    } else if (chatType === 'item') {
        content = <Item messages={messages} />;
    } else if (chatType === 'recommendation') {
        content = <Recommendation messages={messages} />;
    }
    return (
        <div className="chat-wrapper">
            {content}
        </div>
    );
}

export {ChatWrapper}