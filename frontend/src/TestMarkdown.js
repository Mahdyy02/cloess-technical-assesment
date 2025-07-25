import React from 'react';
import ReactMarkdown from 'react-markdown';

// Test markdown rendering
const testMessage = "Good news! We have **40 Fouta Towel** in stock for 45.0 TND each. Plenty available for your order! 🎉";

function TestMarkdown() {
  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <h2>Markdown Rendering Test</h2>
      
      <div style={{ marginBottom: '20px' }}>
        <h3>Raw text:</h3>
        <div style={{ background: '#f5f5f5', padding: '10px', borderRadius: '5px' }}>
          {testMessage}
        </div>
      </div>
      
      <div>
        <h3>Rendered with ReactMarkdown:</h3>
        <div style={{ background: '#e3f2fd', padding: '10px', borderRadius: '5px' }}>
          <ReactMarkdown 
            components={{
              p: ({node, ...props}) => <span {...props} />,
              strong: ({node, ...props}) => <strong style={{fontWeight: '600', color: '#1976d2'}} {...props} />,
            }}
          >
            {testMessage}
          </ReactMarkdown>
        </div>
      </div>
      
      <div style={{ marginTop: '20px' }}>
        <h3>More complex markdown:</h3>
        <div style={{ background: '#f1f8e9', padding: '10px', borderRadius: '5px' }}>
          <ReactMarkdown 
            components={{
              p: ({node, ...props}) => <div {...props} />,
              strong: ({node, ...props}) => <strong style={{fontWeight: '600', color: '#388e3c'}} {...props} />,
              ul: ({node, ...props}) => <ul style={{margin: '0.5rem 0', paddingLeft: '1.2rem'}} {...props} />,
              li: ({node, ...props}) => <li style={{marginBottom: '0.25rem'}} {...props} />,
            }}
          >
            {`I found these products related to your search:

• **Carthagean Robe** - 120.0 TND (Stock: 15)
• **Artisan Shawl** - 80.0 TND (Stock: 25)  
• **Handmade Bag** - 95.0 TND (Stock: 12)

Would you like more details about any of these items?`}
          </ReactMarkdown>
        </div>
      </div>
    </div>
  );
}

export default TestMarkdown;
