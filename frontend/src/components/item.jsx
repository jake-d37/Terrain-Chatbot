import React from 'react';
import './styles/item.css';

// Example message data structure
// const messages = [
//   { id: 1, 
//     sender: 'bot', 
//     text: 'Hello! How can I assist you today?',
//     intro: string, 
//     options: [{ title, author, issue, reason, stock, imageUrl, url }]}
// ];
// messages: { intro: string, item: { title, author, issue, stock, imageUrl, url } }
function Item({ messages }) {
	if (!messages) return null;
	const { intro, item } = messages;
	return (
		<div className="item-wrapper">
			{intro && <div className="item-intro">{intro}</div>}
			{item && (
				<div className="item-bubble">
					<div className="item-info">
						<div className="item-title">{item.title}</div>
						<div className="item-meta">{item.author}, {item.issue}, <span className="item-stock">{item.stock} in stock</span></div>
						<div className="item-image-row">
							<div className="item-image">
								{item.imageUrl ? (
									<img src={item.imageUrl} alt={item.title} />
								) : (
									<div className="item-image-placeholder" />
								)}
							</div>
							<a className="item-link" href={item.url} target="_blank" rel="noopener noreferrer" aria-label="Open">
								<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#444" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="18" height="18" rx="4"/><path d="M9 15l6-6M9 9h6v6"/></svg>
							</a>
						</div>
					</div>
				</div>
			)}
		</div>
	);
};

export { Item };
