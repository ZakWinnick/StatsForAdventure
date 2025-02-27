import React from 'react';
import styled from 'styled-components';

const FooterContainer = styled.footer`
  background-color: #fff;
  box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.05);
  padding: 2rem 0;
  margin-top: auto;
`;

const FooterContent = styled.div`
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1rem;
  display: flex;
  flex-direction: column;
  align-items: center;
`;

const FooterText = styled.p`
  color: ${props => props.theme.colors.dark};
  text-align: center;
  margin-bottom: 1rem;
`;

const FooterLinks = styled.div`
  display: flex;
  margin-bottom: 1rem;
`;

const FooterLink = styled.a`
  color: ${props => props.theme.colors.primary};
  margin: 0 0.5rem;
  transition: color 0.2s;
  
  &:hover {
    color: ${props => props.theme.colors.secondary};
  }
`;

const FooterCopyright = styled.p`
  color: #777;
  font-size: 0.875rem;
`;

const Footer = () => {
  return (
    <FooterContainer>
      <FooterContent>
        <FooterText>
          Stats for Adventure is an unofficial tool for Rivian owners.
          Not affiliated with Rivian Automotive Inc.
        </FooterText>
        <FooterLinks>
          <FooterLink href="https://github.com/bretterer/home-assistant-rivian" target="_blank" rel="noopener noreferrer">
            GitHub
          </FooterLink>
          <FooterLink href="mailto:contact@statsforadventure.com">
            Contact
          </FooterLink>
        </FooterLinks>
        <FooterCopyright>
          © {new Date().getFullYear()} Stats for Adventure. All rights reserved.
        </FooterCopyright>
      </FooterContent>
    </FooterContainer>
  );
};

export default Footer;
