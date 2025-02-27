import React, { useState, useContext, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import styled from 'styled-components';
import { AuthContext } from '../context/AuthContext';

const LoginContainer = styled.div`
  max-width: 500px;
  margin: 2rem auto;
  padding: 2rem;
  background-color: white;
  border-radius: 10px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
`;

const LoginHeader = styled.div`
  text-align: center;
  margin-bottom: 2rem;
`;

const LoginTitle = styled.h1`
  font-size: 2rem;
  color: ${props => props.theme.colors.dark};
  margin-bottom: 0.5rem;
`;

const LoginSubtitle = styled.p`
  color: #777;
`;

const LoginForm = styled.form`
  display: flex;
  flex-direction: column;
`;

const FormGroup = styled.div`
  margin-bottom: 1.5rem;
`;

const FormLabel = styled.label`
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: ${props => props.theme.colors.dark};
`;

const FormInput = styled.input`
  width: 100%;
  padding: 0.75rem 1rem;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 1rem;
  transition: border-color 0.3s;
  
  &:focus {
    outline: none;
    border-color: ${props => props.theme.colors.primary};
  }
`;

const SubmitButton = styled.button`
  padding: 0.75rem 1rem;
  background-color: ${props => props.theme.colors.primary};
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  
  &:hover {
    background-color: ${props => props.theme.colors.primary}dd;
  }
  
  &:disabled {
    background-color: #ccc;
    cursor: not-allowed;
  }
`;

const ErrorMessage = styled.div`
  color: ${props => props.theme.colors.danger};
  background-color: #fee;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  margin-bottom: 1.5rem;
  font-size: 0.875rem;
`;

const OTPInfo = styled.div`
  margin-bottom: 1.5rem;
  padding: 1rem;
  background-color: #f8f9fa;
  border-radius: 8px;
  font-size: 0.875rem;
`;

const Login = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [otpCode, setOTPCode] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const { isAuthenticated, loading, error, needsOTP, otpData, login, validateOTP } = useContext(AuthContext);
  const navigate = useNavigate();
  
  useEffect(() => {
    // Redirect if already authenticated
    if (isAuthenticated) {
      navigate('/dashboard');
    }
  }, [isAuthenticated, navigate]);
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg('');
    
    if (!username || !password) {
      setErrorMsg('Please enter both username and password');
      return;
    }
    
    const result = await login({ username, password });
    
    if (result.error) {
      setErrorMsg(result.error);
    }
  };
  
  const handleOTPSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg('');
    
    if (!otpCode) {
      setErrorMsg('Please enter the verification code');
      return;
    }
    
    const result = await validateOTP(otpCode);
    
    if (result.error) {
      setErrorMsg(result.error);
    }
  };
  
  if (loading) {
    return (
      <LoginContainer>
        <LoginHeader>
          <LoginTitle>Loading...</LoginTitle>
        </LoginHeader>
      </LoginContainer>
    );
  }
  
  if (needsOTP) {
    return (
      <LoginContainer>
        <LoginHeader>
          <LoginTitle>Verification Required</LoginTitle>
          <LoginSubtitle>Enter the code sent to your device</LoginSubtitle>
        </LoginHeader>
        
        {errorMsg && <ErrorMessage>{errorMsg}</ErrorMessage>}
        
        <OTPInfo>
          {otpData.maskedEmail && (
            <p>A verification code has been sent to {otpData.maskedEmail}</p>
          )}
          {otpData.maskedPhone && (
            <p>A verification code has been sent to {otpData.maskedPhone}</p>
          )}
        </OTPInfo>
        
        <LoginForm onSubmit={handleOTPSubmit}>
          <FormGroup>
            <FormLabel htmlFor="otpCode">Verification Code</FormLabel>
            <FormInput
              type="text"
              id="otpCode"
              value={otpCode}
              onChange={(e) => setOTPCode(e.target.value)}
              placeholder="Enter verification code"
              autoComplete="one-time-code"
            />
          </FormGroup>
          
          <SubmitButton type="submit" disabled={loading}>
            {loading ? 'Verifying...' : 'Verify'}
          </SubmitButton>
        </LoginForm>
      </LoginContainer>
    );
  }
  
  return (
    <LoginContainer>
      <LoginHeader>
        <LoginTitle>Welcome Back</LoginTitle>
        <LoginSubtitle>Sign in to access your Rivian stats</LoginSubtitle>
      </LoginHeader>
      
      {errorMsg && <ErrorMessage>{errorMsg}</ErrorMessage>}
      
      <LoginForm onSubmit={handleSubmit}>
        <FormGroup>
          <FormLabel htmlFor="username">Email</FormLabel>
          <FormInput
            type="email"
            id="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="your.email@example.com"
            autoComplete="email"
          />
        </FormGroup>
        
        <FormGroup>
          <FormLabel htmlFor="password">Password</FormLabel>
          <FormInput
            type="password"
            id="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Your password"
            autoComplete="current-password"
          />
        </FormGroup>
        
        <SubmitButton type="submit" disabled={loading}>
          {loading ? 'Signing In...' : 'Sign In'}
        </SubmitButton>
      </LoginForm>
    </LoginContainer>
  );
};

export default Login;
