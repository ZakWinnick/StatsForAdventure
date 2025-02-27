import React from 'react';
import { Link } from 'react-router-dom';
import styled from 'styled-components';

const HomeContainer = styled.div`
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1rem;
`;

const Hero = styled.section`
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 2rem 0 4rem;
  
  @media (max-width: ${props => props.theme.breakpoints.md}) {
    flex-direction: column;
    text-align: center;
  }
`;

const HeroContent = styled.div`
  flex: 1;
  padding-right: 2rem;
  
  @media (max-width: ${props => props.theme.breakpoints.md}) {
    padding-right: 0;
    margin-bottom: 2rem;
  }
`;

const HeroImage = styled.div`
  flex: 1;
  
  img {
    max-width: 100%;
    border-radius: 8px;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
  }
`;

const HeroTitle = styled.h1`
  font-size: 3rem;
  margin-bottom: 1.5rem;
  color: ${props => props.theme.colors.dark};
  line-height: 1.2;
  
  span {
    color: ${props => props.theme.colors.primary};
  }
  
  @media (max-width: ${props => props.theme.breakpoints.md}) {
    font-size: 2.5rem;
  }
`;

const HeroText = styled.p`
  font-size: 1.2rem;
  margin-bottom: 2rem;
  color: #555;
  line-height: 1.6;
`;

const CtaButton = styled(Link)`
  display: inline-block;
  padding: 1rem 2rem;
  background-color: ${props => props.theme.colors.primary};
  color: white;
  font-weight: 600;
  border-radius: 8px;
  transition: all 0.3s ease;
  
  &:hover {
    transform: translateY(-3px);
    box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
  }
`;

const Features = styled.section`
  margin: 4rem 0;
`;

const SectionTitle = styled.h2`
  text-align: center;
  font-size: 2.5rem;
  margin-bottom: 3rem;
  color: ${props => props.theme.colors.dark};
`;

const FeatureGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 2rem;
  
  @media (max-width: ${props => props.theme.breakpoints.md}) {
    grid-template-columns: repeat(2, 1fr);
  }
  
  @media (max-width: ${props => props.theme.breakpoints.sm}) {
    grid-template-columns: 1fr;
  }
`;

const FeatureCard = styled.div`
  background: white;
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.05);
  padding: 2rem;
  transition: all 0.3s ease;
  
  &:hover {
    transform: translateY(-10px);
    box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
  }
`;

const FeatureIcon = styled.div`
  font-size: 2.5rem;
  margin-bottom: 1.5rem;
  color: ${props => props.theme.colors.primary};
`;

const FeatureTitle = styled.h3`
  font-size: 1.5rem;
  margin-bottom: 1rem;
  color: ${props => props.theme.colors.dark};
`;

const FeatureText = styled.p`
  color: #555;
  line-height: 1.6;
`;

const Home = () => {
  return (
    <HomeContainer>
      <Hero>
        <HeroContent>
          <HeroTitle>
            Your <span>Rivian</span> Adventure, <span>Analyzed</span>
          </HeroTitle>
          <HeroText>
            Stats for Adventure gives you powerful insights into your Rivian electric vehicle data.
            Track your battery usage, monitor your trips, and optimize your adventure.
          </HeroText>
          <CtaButton to="/login">Get Started</CtaButton>
        </HeroContent>
        <HeroImage>
          <img src="https://images.unsplash.com/photo-1687130999110-3fd8c591f051?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxzZWFyY2h8M3x8cml2aWFuJTIwcjFzfGVufDB8fDB8fHww&auto=format&fit=crop&w=600&q=60" alt="Rivian R1S on an adventure" />
        </HeroImage>
      </Hero>
      
      <Features>
        <SectionTitle>Why Stats for Adventure?</SectionTitle>
        <FeatureGrid>
          <FeatureCard>
            <FeatureIcon>🔋</FeatureIcon>
            <FeatureTitle>Battery Insights</FeatureTitle>
            <FeatureText>
              Get detailed analytics on your battery performance, charging habits, and efficiency.
            </FeatureText>
          </FeatureCard>
          
          <FeatureCard>
            <FeatureIcon>🗺️</FeatureIcon>
            <FeatureTitle>Trip Tracking</FeatureTitle>
            <FeatureText>
              Monitor your adventures with detailed trip statistics and location information.
            </FeatureText>
          </FeatureCard>
          
          <FeatureCard>
            <FeatureIcon>🔒</FeatureIcon>
            <FeatureTitle>Private & Secure</FeatureTitle>
            <FeatureText>
              Your data stays private. We don't store your credentials or personal information.
            </FeatureText>
          </FeatureCard>
          
          <FeatureCard>
            <FeatureIcon>📊</FeatureIcon>
            <FeatureTitle>Data Visualization</FeatureTitle>
            <FeatureText>
              Beautiful charts and graphs that help you understand your vehicle's performance.
            </FeatureText>
          </FeatureCard>
          
          <FeatureCard>
            <FeatureIcon>🏔️</FeatureIcon>
            <FeatureTitle>Adventure Ready</FeatureTitle>
            <FeatureText>
              Plan your next adventure with confidence based on real data from your vehicle.
            </FeatureText>
          </FeatureCard>
          
          <FeatureCard>
            <FeatureIcon>🔄</FeatureIcon>
            <FeatureTitle>Real-time Updates</FeatureTitle>
            <FeatureText>
              Get up-to-date information about your vehicle whenever you need it.
            </FeatureText>
          </FeatureCard>
        </FeatureGrid>
      </Features>
    </HomeContainer>
  );
};

export default Home;
