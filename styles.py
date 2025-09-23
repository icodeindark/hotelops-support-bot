"""
Modern Minimalist CSS Styles for HotelOpsAI
Clean, professional styling with better Streamlit compatibility
"""

def get_modern_css():
    return """
    <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
    
    /* CSS Variables - Minimalist Color Palette */
    :root {
        --primary: #0066FF;
        --primary-light: #3B82FF;
        --primary-dark: #0052CC;
        --success: #00C851;
        --warning: #FF8800;
        --error: #FF4444;
        --neutral-50: #FAFBFC;
        --neutral-100: #F4F5F7;
        --neutral-200: #E4E7EC;
        --neutral-300: #D0D5DD;
        --neutral-400: #98A2B3;
        --neutral-500: #667085;
        --neutral-600: #475467;
        --neutral-700: #344054;
        --neutral-800: #1D2939;
        --neutral-900: #101828;
        --white: #FFFFFF;
        --shadow-xs: 0 1px 2px 0 rgba(16, 24, 40, 0.05);
        --shadow-sm: 0 1px 3px 0 rgba(16, 24, 40, 0.1), 0 1px 2px 0 rgba(16, 24, 40, 0.06);
        --shadow-md: 0 4px 8px -2px rgba(16, 24, 40, 0.1), 0 2px 4px -2px rgba(16, 24, 40, 0.06);
        --shadow-lg: 0 10px 15px -3px rgba(16, 24, 40, 0.1), 0 4px 6px -2px rgba(16, 24, 40, 0.05);
        --radius: 8px;
        --radius-sm: 6px;
        --radius-lg: 12px;
        --spacing-xs: 4px;
        --spacing-sm: 8px;
        --spacing-md: 16px;
        --spacing-lg: 24px;
        --spacing-xl: 32px;
    }

    /* Reset Streamlit defaults */
    .stApp {
        background: var(--neutral-50);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }
    
    .main > .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }
    
    /* Hide Streamlit elements */
    #MainMenu, footer, .stDeployButton {
        visibility: hidden;
    }
    
    /* Header */
    .app-header {
        background: var(--white);
        border: 1px solid var(--neutral-200);
        border-radius: var(--radius-lg);
        padding: var(--spacing-xl);
        margin-bottom: var(--spacing-lg);
        box-shadow: var(--shadow-sm);
    }
    
    .header-top {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: var(--spacing-lg);
    }
    
    .header-brand {
        display: flex;
        align-items: center;
        gap: var(--spacing-md);
    }
    
    .brand-icon {
        width: 48px;
        height: 48px;
        background: linear-gradient(135deg, var(--primary), var(--primary-light));
        border-radius: var(--radius);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        color: var(--white);
    }
    
    .brand-text h1 {
        font-size: 24px;
        font-weight: 600;
        color: var(--neutral-900);
        margin: 0;
        line-height: 1.2;
    }
    
    .brand-text p {
        font-size: 14px;
        color: var(--neutral-500);
        margin: 0;
    }
    
    .status-pill {
        display: inline-flex;
        align-items: center;
        gap: var(--spacing-xs);
        padding: var(--spacing-xs) var(--spacing-sm);
        border-radius: 20px;
        font-size: 12px;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .status-active {
        background: rgba(0, 200, 81, 0.1);
        color: var(--success);
        border: 1px solid rgba(0, 200, 81, 0.2);
    }
    
    .status-idle {
        background: rgba(102, 112, 133, 0.1);
        color: var(--neutral-500);
        border: 1px solid rgba(102, 112, 133, 0.2);
    }
    
    .status-processing {
        background: rgba(255, 136, 0, 0.1);
        color: var(--warning);
        border: 1px solid rgba(255, 136, 0, 0.2);
    }
    
    .status-dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background: currentColor;
    }
    
    .status-active .status-dot {
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.4; }
    }
    
    .header-stats {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
        gap: var(--spacing-md);
        margin-top: var(--spacing-lg);
    }
    
    .stat-card {
        background: var(--neutral-50);
        border: 1px solid var(--neutral-200);
        border-radius: var(--radius);
        padding: var(--spacing-md);
        text-align: center;
    }
    
    .stat-value {
        font-size: 16px;
        font-weight: 600;
        color: var(--neutral-900);
        margin-bottom: var(--spacing-xs);
    }
    
    .stat-label {
        font-size: 12px;
        color: var(--neutral-500);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-weight: 500;
    }
    
    /* Chat Interface */
    .chat-container {
        background: var(--white);
        border: 1px solid var(--neutral-200);
        border-radius: var(--radius-lg);
        box-shadow: var(--shadow-sm);
        display: flex;
        flex-direction: column;
        height: 600px;
    }
    
    .chat-header {
        padding: var(--spacing-lg);
        border-bottom: 1px solid var(--neutral-200);
        background: var(--neutral-50);
        border-radius: var(--radius-lg) var(--radius-lg) 0 0;
    }
    
    .chat-header h3 {
        margin: 0;
        font-size: 18px;
        font-weight: 600;
        color: var(--neutral-900);
        display: flex;
        align-items: center;
        gap: var(--spacing-sm);
    }
    
    .chat-messages {
        flex: 1;
        overflow-y: auto;
        padding: var(--spacing-lg);
        scroll-behavior: smooth;
    }
    
    .chat-messages::-webkit-scrollbar {
        width: 4px;
    }
    
    .chat-messages::-webkit-scrollbar-track {
        background: transparent;
    }
    
    .chat-messages::-webkit-scrollbar-thumb {
        background: var(--neutral-300);
        border-radius: 2px;
    }
    
    .chat-messages::-webkit-scrollbar-thumb:hover {
        background: var(--neutral-400);
    }
    
    .message {
        margin-bottom: var(--spacing-lg);
        animation: slideUp 0.2s ease-out;
    }
    
    @keyframes slideUp {
        from {
            opacity: 0;
            transform: translateY(10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .message-user {
        display: flex;
        justify-content: flex-end;
    }
    
    .message-bot {
        display: flex;
        justify-content: flex-start;
        align-items: flex-start;
        gap: var(--spacing-sm);
    }
    
    .message-bubble {
        max-width: 70%;
        padding: var(--spacing-md);
        border-radius: var(--radius-lg);
        font-size: 14px;
        line-height: 1.5;
    }
    
    .message-user .message-bubble {
        background: var(--primary);
        color: var(--white);
        border-bottom-right-radius: var(--spacing-xs);
    }
    
    .message-bot .message-bubble {
        background: var(--neutral-100);
        color: var(--neutral-800);
        border-bottom-left-radius: var(--spacing-xs);
        border: 1px solid var(--neutral-200);
    }
    
    .bot-avatar {
        width: 32px;
        height: 32px;
        background: linear-gradient(135deg, var(--success), #00A142);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 16px;
        color: var(--white);
        flex-shrink: 0;
    }
    
    .agent-badge {
        background: var(--primary);
        color: var(--white);
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: var(--spacing-sm);
        display: inline-block;
    }
    
    .message-timestamp {
        font-size: 11px;
        opacity: 0.7;
        margin-top: var(--spacing-xs);
    }
    
    .welcome-message {
        text-align: center;
        padding: var(--spacing-xl);
        color: var(--neutral-500);
    }
    
    .welcome-icon {
        font-size: 48px;
        margin-bottom: var(--spacing-md);
        opacity: 0.6;
    }
    
    .welcome-text {
        font-size: 16px;
        line-height: 1.6;
        max-width: 400px;
        margin: 0 auto;
    }
    
    /* Quick Actions */
    .quick-actions {
        padding: var(--spacing-lg);
        border-top: 1px solid var(--neutral-200);
        background: var(--neutral-50);
        border-radius: 0 0 var(--radius-lg) var(--radius-lg);
    }
    
    .quick-actions h4 {
        margin: 0 0 var(--spacing-md) 0;
        font-size: 14px;
        font-weight: 600;
        color: var(--neutral-700);
        display: flex;
        align-items: center;
        gap: var(--spacing-sm);
    }
    
    .quick-actions-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: var(--spacing-sm);
    }
    
    /* Debug Panel */
    .debug-panel {
        background: var(--white);
        border: 1px solid var(--neutral-200);
        border-radius: var(--radius-lg);
        box-shadow: var(--shadow-sm);
        height: 600px;
        display: flex;
        flex-direction: column;
    }
    
    .debug-header {
        padding: var(--spacing-lg);
        border-bottom: 1px solid var(--neutral-200);
        background: var(--neutral-50);
        border-radius: var(--radius-lg) var(--radius-lg) 0 0;
    }
    
    .debug-header h3 {
        margin: 0;
        font-size: 18px;
        font-weight: 600;
        color: var(--neutral-900);
        display: flex;
        align-items: center;
        gap: var(--spacing-sm);
    }
    
    .debug-content {
        flex: 1;
        overflow-y: auto;
        padding: var(--spacing-lg);
    }
    
    .debug-content::-webkit-scrollbar {
        width: 4px;
    }
    
    .debug-content::-webkit-scrollbar-track {
        background: transparent;
    }
    
    .debug-content::-webkit-scrollbar-thumb {
        background: var(--neutral-300);
        border-radius: 2px;
    }
    
    .debug-section {
        margin-bottom: var(--spacing-xl);
    }
    
    .debug-section h4 {
        margin: 0 0 var(--spacing-md) 0;
        font-size: 14px;
        font-weight: 600;
        color: var(--neutral-700);
        padding: var(--spacing-sm) var(--spacing-md);
        background: var(--neutral-100);
        border-radius: var(--radius);
        border-left: 3px solid var(--primary);
        display: flex;
        align-items: center;
        gap: var(--spacing-sm);
    }
    
    /* Metrics */
    .metrics-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
        gap: var(--spacing-sm);
        margin-bottom: var(--spacing-md);
    }
    
    .metric-card {
        background: var(--neutral-50);
        border: 1px solid var(--neutral-200);
        border-radius: var(--radius);
        padding: var(--spacing-md);
        text-align: center;
    }
    
    .metric-card .value {
        font-size: 20px;
        font-weight: 600;
        color: var(--primary);
        margin-bottom: var(--spacing-xs);
    }
    
    .metric-card .label {
        font-size: 12px;
        color: var(--neutral-500);
        font-weight: 500;
    }
    
    /* Routing History */
    .route-item {
        display: flex;
        align-items: center;
        gap: var(--spacing-md);
        padding: var(--spacing-sm) var(--spacing-md);
        background: var(--neutral-50);
        border: 1px solid var(--neutral-200);
        border-radius: var(--radius);
        margin-bottom: var(--spacing-sm);
        font-size: 13px;
    }
    
    .route-time {
        color: var(--neutral-500);
        font-weight: 500;
        min-width: 50px;
        font-family: 'JetBrains Mono', monospace;
    }
    
    .route-agent {
        color: var(--primary);
        font-weight: 600;
        flex: 1;
    }
    
    .route-confidence {
        color: var(--neutral-600);
        font-size: 11px;
        padding: 2px 6px;
        background: var(--neutral-200);
        border-radius: 10px;
        font-family: 'JetBrains Mono', monospace;
    }
    
    /* Controls */
    .controls-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
        gap: var(--spacing-sm);
        margin-bottom: var(--spacing-md);
    }
    
    /* System Health */
    .health-item {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: var(--spacing-sm) var(--spacing-md);
        background: var(--neutral-50);
        border: 1px solid var(--neutral-200);
        border-radius: var(--radius);
        margin-bottom: var(--spacing-sm);
        font-size: 13px;
    }
    
    .health-label {
        color: var(--neutral-700);
        font-weight: 500;
    }
    
    .health-status {
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: var(--spacing-xs);
    }
    
    .health-excellent {
        color: var(--success);
    }
    
    .health-good {
        color: var(--warning);
    }
    
    .health-poor {
        color: var(--error);
    }
    
    /* Database Status */
    .db-status {
        display: flex;
        align-items: center;
        gap: var(--spacing-sm);
        padding: var(--spacing-md);
        background: rgba(0, 200, 81, 0.05);
        border: 1px solid rgba(0, 200, 81, 0.2);
        border-radius: var(--radius);
        margin-bottom: var(--spacing-md);
    }
    
    .db-status-text {
        color: var(--success);
        font-weight: 600;
        font-size: 14px;
    }
    
    /* Example Queries */
    .example-query {
        background: rgba(0, 102, 255, 0.05);
        color: var(--primary);
        border: 1px solid rgba(0, 102, 255, 0.2);
        padding: var(--spacing-sm) var(--spacing-md);
        border-radius: var(--radius);
        font-size: 13px;
        margin: var(--spacing-xs) var(--spacing-xs) var(--spacing-xs) 0;
        display: inline-block;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .example-query:hover {
        background: var(--primary);
        color: var(--white);
        transform: translateY(-1px);
    }
    
    /* Footer */
    .app-footer {
        text-align: center;
        padding: var(--spacing-xl);
        color: var(--neutral-500);
        font-size: 14px;
        background: var(--white);
        border: 1px solid var(--neutral-200);
        border-radius: var(--radius-lg);
        margin-top: var(--spacing-lg);
    }
    
    .app-footer strong {
        color: var(--neutral-700);
    }
    
    /* Toggle Button */
    .debug-toggle {
        margin-bottom: var(--spacing-lg);
    }
    
    /* Responsive Design */
    @media (max-width: 768px) {
        .main > .block-container {
            padding: 1rem;
        }
        
        .header-top {
            flex-direction: column;
            gap: var(--spacing-md);
            text-align: center;
        }
        
        .header-stats {
            grid-template-columns: repeat(2, 1fr);
        }
        
        .quick-actions-grid {
            grid-template-columns: 1fr;
        }
        
        .message-bubble {
            max-width: 85%;
        }
        
        .metrics-grid {
            grid-template-columns: repeat(2, 1fr);
        }
        
        .controls-grid {
            grid-template-columns: 1fr;
        }
    }
    
    @media (max-width: 480px) {
        .header-stats {
            grid-template-columns: 1fr;
        }
        
        .metrics-grid {
            grid-template-columns: 1fr;
        }
    }
    
    /* Focus states for accessibility */
    button:focus,
    .example-query:focus {
        outline: 2px solid var(--primary);
        outline-offset: 2px;
    }
    
    /* Loading animation */
    .loading {
        display: inline-block;
        animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    </style>
    """