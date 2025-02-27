import React, { useContext } from 'react';
import { Link, Navigate } from 'react-router-dom';
import styled from 'styled-components';
import { AuthContext } from '../context/AuthContext';

const DashboardContainer = styled.div`
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1rem;
`;

const DashboardHeader = styled.div`
  margin-bottom: 2rem;
`;

const DashboardTitle = styled.h1`
  font-size: 2.5rem;
  color: ${props => props.theme.colors.dark};
  margin-bottom: 0.5rem;
`;

const DashboardSubtitle = styled.p`
  color: #777;
  font-size: 1.1rem;
`;

const VehiclesGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 2rem;
`;

const VehicleCard = styled.div`
  background: white;
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.05);
  overflow: hidden;
  transition: all 0.3s ease;
  
  &:hover {
    transform: translateY(-5px);
    box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
  }
`;

const VehicleImage = styled.div`
  height: 200px;
  background-color: #f5f5f5;
  display: flex;
  align-items: center;
  justify-content: center;
  
  img {
    max-width: 100%;
    max-height: 100%;
    object-fit: cover;
  }
`;

const VehicleInfo = styled.div`
  padding: 1.5rem;
`;

const VehicleName = styled.h3`
  font-size: 1.5rem;
  color: ${props => props.theme.colors.dark};
  margin-bottom: 0.5rem;
`;

const VehicleModel = styled.p`
  color: #777;
  margin-bottom: 1rem;
  font-weight: 500;
`;

const VehicleVIN = styled.p`
  color: #999;
  font-size: 0.875rem;
  margin-bottom: 1.5rem;
`;

const VehicleButton = styled(Link)`
  display: inline-block;
  background-color: ${props => props.theme.colors.primary};
  color: white;
  font-weight: 600;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  transition: all 0.3s;
  
  &:hover {
    background-color: ${props => props.theme.colors.primary}dd;
  }
`;

const NoVehicles = styled.div`
  background: white;
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.05);
  padding: 2rem;
  text-align: center;
`;

const NoVehiclesTitle = styled.h3`
  font-size: 1.5rem;
  color: ${props => props.theme.colors.dark};
  margin-bottom: 1rem;
`;

const NoVehiclesText = styled.p`
  color: #777;
  margin-bottom: 1.5rem;
`;

const getVehicleImageByModel = (model) => {
  switch (model) {
    case 'R1T':
      return 'https://images.unsplash.com/photo-1650619819226-f8cf13808a02?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxzZWFyY2h8Mnx8cml2aWFuJTIwcjF0fGVufDB8fDB8fHww&auto=format&fit=crop&w=600&q=60';
    case 'R1S':
      return 'https://images.unsplash.com/photo-1687130999110-3fd8c591f051?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxzZWFyY2h8M3x8cml2aWFuJTIwcjFzfGVufDB8fDB8fHww&auto=format&fit=crop&w=600&q=60';
    default:
      return 'https://images.unsplash.com/photo-1650619819226-f8cf13808a02?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxzZWFyY2h8Mnx8cml2aWFuJTIwcjF0fGVufDB8fDB8fHww&auto=format&fit=crop&w=600&q=60';
  }
};

const Dashboard = () => {
  const { isAuthenticated, user, vehicles, loading } = useContext(AuthContext);
  
  if (loading) {
    return <div>Loading...</div>;
  }
  
  if (!isAuthenticated) {
    return <Navigate to="/login" />;
  }
  
// Handle if we're not authenticated or data is loading
if (loading) {
  return <div className="container"><LoadingText>Loading your vehicles...</LoadingText></div>;
}

if (!isAuthenticated) {
  return <Navigate to="/login" />;
}

  return (
    <DashboardContainer>
      <DashboardHeader>
        <DashboardTitle>Your Vehicles</DashboardTitle>
        <DashboardSubtitle>
          {user?.firstName ? `Welcome back, ${user.firstName}!` : 'Welcome back!'}
        </DashboardSubtitle>
      </DashboardHeader>
      
      {vehicles && vehicles.length > 0 ? (
        <VehiclesGrid>
          {vehicles.map((vehicle) => (
            <VehicleCard key={vehicle.id}>
              <VehicleImage>
                <img 
                  src={getVehicleImageByModel(vehicle.vehicle.model)} 
                  alt={`${vehicle.name || vehicle.vehicle.model}`} 
                />
              </VehicleImage>
              <VehicleInfo>
                <VehicleName>{vehicle.name || 'My Rivian'}</VehicleName>
                <VehicleModel>{vehicle.vehicle.model}</VehicleModel>
                <VehicleVIN>VIN: {vehicle.vehicle.vin}</VehicleVIN>
                <VehicleButton to={`/vehicle/${vehicle.vehicle.vin}`}>
                  View Stats
                </VehicleButton>
              </VehicleInfo>
            </VehicleCard>
          ))}
        </VehiclesGrid>
      ) : (
        <NoVehicles>
          <NoVehiclesTitle>No Vehicles Found</NoVehiclesTitle>
          <NoVehiclesText>
            We couldn't find any Rivian vehicles associated with your account.
            Make sure your account has access to a Rivian vehicle.
          </NoVehiclesText>
        </NoVehicles>
      )}
    </DashboardContainer>
  );
};

export default Dashboard;
