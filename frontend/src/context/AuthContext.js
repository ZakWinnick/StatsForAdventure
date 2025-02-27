import React, { createContext, useState, useEffect } from 'react';
import api from '../utils/api';

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [vehicles, setVehicles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [needsOTP, setNeedsOTP] = useState(false);
  const [otpData, setOTPData] = useState(null);
  const [username, setUsername] = useState('');

  // Check for existing auth data
  useEffect(() => {
    const checkAuth = async () => {
      setLoading(true);
      try {
        const userData = await api.get('/user');
        setUser(userData);
        setVehicles(userData.vehicles || []);
        setIsAuthenticated(true);
      } catch (err) {
        console.error('Not authenticated', err);
        setIsAuthenticated(false);
        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    checkAuth();
  }, []);

  const login = async (credentials) => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.post('/login', credentials);
      
      if (response.status === 'otp_required') {
        setNeedsOTP(true);
        setOTPData(response.data);
        setUsername(credentials.username);
        return { needsOTP: true, otpData: response.data };
      }
      
      if (response.status === 'success') {
        const userData = await api.get('/user');
        setUser(userData);
        setVehicles(userData.vehicles || []);
        setIsAuthenticated(true);
        return { success: true };
      }
      
      setError(response.message || 'Login failed');
      return { success: false, error: response.message };
    } catch (err) {
      setError(err.message || 'An error occurred during login');
      return { success: false, error: err.message };
    } finally {
      setLoading(false);
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
        return { success: true };
      }
      
      setError(response.message || 'OTP validation failed');
      return { success: false, error: response.message };
    } catch (err) {
      setError(err.message || 'An error occurred during OTP validation');
      return { success: false, error: err.message };
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    setIsAuthenticated(false);
    setUser(null);
    setVehicles([]);
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
