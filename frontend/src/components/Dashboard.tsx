import React, { useState, useEffect } from 'react';
import { Send, Plus } from 'lucide-react';
import axios from 'axios';
import AgentResponse, { type AgentBlocks } from './AgentResponse';

// FinanceAgents backend. Any of the four implementations works; they expose the
// same POST /query contract. Override with NEXT_PUBLIC_API_URL (see .env.example).
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

interface Message {
  id: string;
  content: AgentBlocks;
  isUser: boolean;
  timestamp: Date | null;
}

interface ChatHistory {
  id: string;
  title: string;
  lastMessage: string;
  timestamp: Date;
}

const Dashboard: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    // {
    //     id: '1',
    //     content: 'Hello! I am BankerAI, your intelligent financial assistant. How can I help you today?',
    //     isUser: false,
    //     timestamp: new Date(),
    // },
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isClient, setIsClient] = useState(false);
  const [chatHistory, setChatHistory] = useState<ChatHistory[]>([
    {
      id: '1',
      title: 'Current Chat',
      lastMessage: 'Hello! I am BankerAI...',
      timestamp: new Date(),
    },
    {
      id: '2',
      title: 'Stock Analysis Discussion',
      lastMessage: 'Please analyze Apple stock for me...',
      timestamp: new Date(Date.now() - 86400000),
    },
    {
      id: '3',
      title: 'Portfolio Consultation',
      lastMessage: 'I want to know about risk diversification...',
      timestamp: new Date(Date.now() - 172800000),
    },
  ]);
  const [activeChat, setActiveChat] = useState('1');

  const recommendedPrompts = [
    "Analyze the current market trend",
    "Recommend a suitable investment portfolio",
    "Explain what risk management is",
    "Compare different investment strategies",
    "Analyze the prospects of tech stocks",
    "How to do value investing",
  ];

  useEffect(() => {
    setIsClient(true);
    setMessages(prev => 
      prev.map(msg => 
        msg.id === '1' && msg.timestamp === null 
          ? { ...msg, timestamp: new Date() }
          : msg
      )
    );
  }, []);

  const handleSendMessage = async (messageContent?: string) => {
    const content = messageContent || inputValue;
    if (!content.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: { userMessage: { summary: content } },
      isUser: true,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      const response = await axios.post(`${API_URL}/query`, {
        query: content,
      });

      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: response.data.response,
        isUser: false,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      console.error(error);
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: { error: { summary: 'Request failed, please try again later' } },
        isUser: false,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, aiMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const formatTime = (timestamp: Date | null) => {
    if (!timestamp || !isClient) return '';
    return timestamp.toLocaleTimeString();
  };

  const formatDate = (timestamp: Date) => {
    if (!isClient) return '';
    const now = new Date();
    const diff = now.getTime() - timestamp.getTime();
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    
    if (days === 0) return 'Today';
    if (days === 1) return 'Yesterday';
    if (days < 7) return `${days} days ago`;
    return timestamp.toLocaleDateString();
  };

  const createNewChat = () => {
    const newChatId = Date.now().toString();
    const newChat: ChatHistory = {
      id: newChatId,
      title: 'New Chat',
      lastMessage: '',
      timestamp: new Date(),
    };
    setChatHistory(prev => [newChat, ...prev]);
    setActiveChat(newChatId);
    // setMessages([{
    //   id: '1',
    //   content: '',
    //   isUser: false,
    //   timestamp: new Date(),
    // }]);
  };

  return (
    <div className="flex h-screen bg-white">
      {/* Chat History List */}
      <div className="w-56 border-r border-gray-200 bg-gray-50 flex flex-col">
        <div className="p-3 border-b border-gray-200">
          <button
            onClick={createNewChat}
            className="w-full flex items-center justify-center space-x-2 p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm"
          >
            <Plus size={14} />
            <span>New Chat</span>
          </button>
        </div>
        
        <div className="flex-1 overflow-y-auto">
          <div className="p-2 space-y-1">
            {chatHistory.map((chat) => (
              <button
                key={chat.id}
                onClick={() => setActiveChat(chat.id)}
                className={`w-full text-left p-2 rounded-lg transition-colors ${
                  activeChat === chat.id
                    ? 'bg-blue-100 border-blue-300'
                    : 'hover:bg-gray-100'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h3 className="font-medium text-gray-800 text-xs truncate">
                      {chat.title}
                    </h3>
                    <p className="text-xs text-gray-500 mt-0.5 truncate overflow-hidden text-ellipsis">
                      {chat.lastMessage}
                    </p>
                    {isClient && (
                      <p className="text-xs text-gray-400 mt-0.5">
                        {formatDate(chat.timestamp)}
                      </p>
                    )}
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Message List */}
        <div className="flex-1 overflow-y-auto p-3 space-y-3">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.isUser ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={
                  message.isUser
                    ? 'max-w-[85%] px-3 py-2 rounded-lg bg-blue-600 text-white'
                    : 'w-full max-w-3xl'
                }
              >
                {message.isUser ? (
                  <p className="text-sm break-words">{message.content.userMessage.summary}</p>
                ) : (
                  <AgentResponse blocks={message.content} />
                )}
                {isClient && (
                  <p className={`text-xs mt-1 ${message.isUser ? 'opacity-70' : 'text-gray-400 px-1'}`}>
                    {formatTime(message.timestamp)}
                  </p>
                )}
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-gray-100 text-gray-800 px-3 py-2 rounded-lg">
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Recommended Prompts */}
        <div className="border-t border-gray-200 p-3">
          <h3 className="text-xs font-medium text-gray-700 mb-2">Recommended Prompts</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {recommendedPrompts.map((prompt, index) => (
              <button
                key={index}
                onClick={() => handleSendMessage(prompt)}
                className="text-left p-2 text-xs text-gray-600 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors overflow-hidden truncate max-w-full"
                disabled={isLoading}
              >
                {prompt}
              </button>
            ))}
          </div>
        </div>

        {/* Input Box */}
        <div className="border-t border-gray-200 p-3">
          <div className="flex space-x-2">
            <textarea
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your question..."
              className="flex-1 p-2 border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
              rows={1}
              disabled={isLoading}
            />
            <button
              onClick={() => handleSendMessage()}
              disabled={!inputValue.trim() || isLoading}
              className="px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Send size={18} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;