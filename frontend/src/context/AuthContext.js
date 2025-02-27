import React, { createContext, useState } from 'react';
import api from '../utils/api';

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [vehicles, setVehicles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [needsOTP, setNeedsOTP] = useState(false);
  const [otpData, setOTPData] = useState(null);
  const [username, setUsername] = useState('');

  const login = async (credentials) => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.post('/login', credentials);
      
      if (response.status === 'otp_required') {
        setNeedsOTP(true);
        setOTPData(response.data);
        setUsername(credentials.username);
        setLoading(false);
        return { needsOTP: true, otpData: response.data };
      }
      
      if (response.status === 'success') {
        const userData = await api.get('/user');
        setUser(userData);
        setVehicles(userData.vehicles || []);
        setIsAuthenticated(true);
        setLoading(false);
        return { success: true };
      }
      
      setError(response.message || 'Login failed');
      setLoading(false);
      return { success: false, error: response.message };
    } catch (err) {
      setError(err.message || 'An error occurred during login');
      setLoading(false);
      return { success: false, error: err.message };
    }
  };

  const validateOTP = async (otpCode) => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.post('/validate-otp', { 
        username, 
        otp: otpCode 
      });
      
      if (response.status === 'success') {
        const userData = await api.get('/user');
        setUser(userData);
        setVehicles(userData.vehicles || []);
        setIsAuthenticated(true);
        setNeedsOTP(false);
        setOTPData(null);
        setLoading(false);
        return { success: true };
      }
      
      setError(response.message || 'OTP validation failed');
      setLoading(false);
      return { success: false, error: response.message };
    } catch (err) {
      setError(err.message || 'An error occurred during OTP validation');
      setLoading(false);
      return { success: false, error: err.message };
    }
  };

  const logout = () => {
    setIsAuthenticated(false);
    setUser(null);
    setVehicles([]);
    setNeedsOTP(false);
    setOTPData(null);
    setUsername('');
    
    // Force a complete page reload with cache clearing
    window.location.href = '/?t=' + new Date().getTime();
  };

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated,
        user,
        vehicles,
        loading,
        error,
        needsOTP,
        otpData,
        login,
        validateOTP,
        logout
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};