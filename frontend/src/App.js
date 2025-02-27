import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import styled, { ThemeProvider } from 'styled-components';

// Components
import Navbar from './components/layout/Navbar';
import Footer from './components/layout/Footer';

// Pages
import Home from './pages/Home';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import VehicleDetails from './pages/VehicleDetails';
import NotFound from './pages/NotFound';

// Context
import { AuthProvider } from './context/AuthContext';

// Theme
const theme = {
  colors: {
    primary: '#3498db',
    secondary: '#2ecc71',
    dark: '#2c3e50',
    light: '#ecf0f1',
    danger: '#e74c3c',
    warning: '#f39c12',
  },
  fonts: {
    main: 'Inter, sans-serif',
  },
  breakpoints: {
    sm: '576px',
    md: '768px',
    lg: '992px',
    xl: '1200px',
  }
};

const AppContainer = styled.div`
  display: flex;
  flex-direction: column;
  min-height: 100vh;
`;

const ContentContainer = styled.main`
  flex: 1;
  padding: 2rem 0;
`;

// Protected route component
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useContext(AuthContext);
  
  if (loading) {
    return <div style={{ 
      padding: '2rem', 
      textAlign: 'center', 
      fontSize: '1.2rem',
      color: '#777' 
    }}>Loading...</div>;
  }
  
  if (!isAuthenticated) {
    return <Navigate to="/login" />;
  }
  
  return children;
};

const App = () => {
  return (
    <ThemeProvider theme={theme}>
      <AuthProvider>
        <Router>
          <AppContainer>
            <Navbar />
            <ContentContainer>
            <Routes>
  <Route path="/" element={<Home />} />
  <Route path="/login" element={<Login />} />
  <Route path="/dashboard" element={
    <ProtectedRoute>
      <Dashboard />
    </ProtectedRoute>
  } />
  <Route path="/vehicle/:vin" element={
    <ProtectedRoute>
      <VehicleDetails />
    </ProtectedRoute>
  } />
  <Route path="*" element={<NotFound />} />
</Routes>
            </ContentContainer>
            <Footer />
          </AppContainer>
        </Router>
      </AuthProvider>
    </ThemeProvider>
  );
};

export default App;
