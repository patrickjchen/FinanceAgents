import React, { useState } from 'react';
import { User, Bell, Shield, Globe, Moon, Sun } from 'lucide-react';

const Settings: React.FC = () => {
  const [darkMode, setDarkMode] = useState(false);
  const [notifications, setNotifications] = useState({
    email: true,
    push: false,
    sms: true,
  });
  const [profile, setProfile] = useState({
    name: 'John Doe',
    email: 'johndoe@example.com',
    phone: '+1 555-123-4567',
    language: 'en-US',
  });

  const handleNotificationChange = (type: keyof typeof notifications) => {
    setNotifications(prev => ({
      ...prev,
      [type]: !prev[type],
    }));
  };

  const handleProfileChange = (field: keyof typeof profile, value: string) => {
    setProfile(prev => ({
      ...prev,
      [field]: value,
    }));
  };

  return (
    <div className="p-6 bg-gray-50 min-h-full">
      <h1 className="text-3xl font-bold text-gray-800 mb-8">Settings</h1>

      {/* Profile Settings */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <div className="flex items-center mb-4">
          <User className="w-5 h-5 text-blue-600 mr-2" />
          <h2 className="text-xl font-semibold text-gray-700">Profile</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Name
            </label>
            <input
              type="text"
              value={profile.name}
              onChange={(e) => handleProfileChange('name', e.target.value)}
              className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Email
            </label>
            <input
              type="email"
              value={profile.email}
              onChange={(e) => handleProfileChange('email', e.target.value)}
              className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Phone
            </label>
            <input
              type="tel"
              value={profile.phone}
              onChange={(e) => handleProfileChange('phone', e.target.value)}
              className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Language
            </label>
            <select
              value={profile.language}
              onChange={(e) => handleProfileChange('language', e.target.value)}
              className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="zh-CN">Chinese (Simplified)</option>
              <option value="zh-TW">Chinese (Traditional)</option>
              <option value="en-US">English</option>
              <option value="ja-JP">Japanese</option>
            </select>
          </div>
        </div>
        <button className="mt-4 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
          Save Changes
        </button>
      </div>

      {/* Notification Settings */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <div className="flex items-center mb-4">
          <Bell className="w-5 h-5 text-blue-600 mr-2" />
          <h2 className="text-xl font-semibold text-gray-700">Notifications</h2>
        </div>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-medium text-gray-700">Email Notifications</h3>
              <p className="text-sm text-gray-500">Receive important updates and market alerts</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={notifications.email}
                onChange={() => handleNotificationChange('email')}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
            </label>
          </div>
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-medium text-gray-700">Push Notifications</h3>
              <p className="text-sm text-gray-500">Real-time price change alerts</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={notifications.push}
                onChange={() => handleNotificationChange('push')}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
            </label>
          </div>
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-medium text-gray-700">SMS Notifications</h3>
              <p className="text-sm text-gray-500">Important security alerts</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={notifications.sms}
                onChange={() => handleNotificationChange('sms')}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
            </label>
          </div>
        </div>
      </div>

      {/* Security Settings */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <div className="flex items-center mb-4">
          <Shield className="w-5 h-5 text-blue-600 mr-2" />
          <h2 className="text-xl font-semibold text-gray-700">Security</h2>
        </div>
        <div className="space-y-4">
          <button className="w-full text-left p-4 border border-gray-200 rounded-lg hover:bg-gray-50">
            <h3 className="font-medium text-gray-700">Change Password</h3>
            <p className="text-sm text-gray-500">Update your login password</p>
          </button>
          <button className="w-full text-left p-4 border border-gray-200 rounded-lg hover:bg-gray-50">
            <h3 className="font-medium text-gray-700">Two-Factor Authentication</h3>
            <p className="text-sm text-gray-500">Enhance account security</p>
          </button>
          <button className="w-full text-left p-4 border border-gray-200 rounded-lg hover:bg-gray-50">
            <h3 className="font-medium text-gray-700">Login History</h3>
            <p className="text-sm text-gray-500">View recent login records</p>
          </button>
        </div>
      </div>

      {/* Appearance Settings */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center mb-4">
          <Globe className="w-5 h-5 text-blue-600 mr-2" />
          <h2 className="text-xl font-semibold text-gray-700">Appearance</h2>
        </div>
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            {darkMode ? (
              <Moon className="w-5 h-5 text-gray-600 mr-2" />
            ) : (
              <Sun className="w-5 h-5 text-yellow-500 mr-2" />
            )}
            <div>
              <h3 className="font-medium text-gray-700">Dark Mode</h3>
              <p className="text-sm text-gray-500">Switch to dark theme</p>
            </div>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={darkMode}
              onChange={() => setDarkMode(!darkMode)}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
          </label>
        </div>
      </div>
    </div>
  );
};

export default Settings; 