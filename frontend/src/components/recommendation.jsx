import React from 'react';
import './styles/recommendation.css';

// Example message data structure
// const messages = [
//   { id: 1,  
//     sender: 'bot', 
//     text: 'Hello! How can I assist you today?',
//     intro: string, 
//     options: [{ title, reason, stock, url }]}
// ];
function Recommendation({ messages }) {
	if (!messages) return null;
	const { intro, options } = messages;
	return (
		<div className="recommendation-wrapper">
			{intro && (
				<div className="recommendation-intro">{intro}</div>
			)}
			<div className="recommendation-options">
				{options && options.map((opt, idx) => (
					<div className="recommendation-bubble" key={idx}>
						<div className="recommendation-info">
							<div className="recommendation-title">{opt.title}</div>
							<div className="recommendation-reason">{opt.reason} <span className="recommendation-stock">| {opt.stock} in stock</span></div>
						</div>
						<a className="recommendation-link" href={opt.url} target="_blank" rel="noopener noreferrer" aria-label="Open">
							<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#444" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="18" height="18" rx="4"/><path d="M9 15l6-6M9 9h6v6"/></svg>
						</a>
					</div>
				))}
			</div>
		</div>
	);
}

export { Recommendation };
