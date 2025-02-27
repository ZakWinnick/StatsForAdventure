import React, { useState, useEffect, useContext } from 'react';
import { useParams, Navigate } from 'react-router-dom';
import styled from 'styled-components';
import { AuthContext } from '../context/AuthContext';
import api from '../utils/api';

const VehicleContainer = styled.div`
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1rem;
`;

const VehicleHeader = styled.div`
  display: flex;
  align-items: center;
  margin-bottom: 2rem;
  
  @media (max-width: ${props => props.theme.breakpoints.md}) {
    flex-direction: column;
    align-items: flex-start;
  }
`;

const VehicleImage = styled.div`
  width: 120px;
  height: 120px;
  border-radius: 12px;
  background-color: #f5f5f5;
  margin-right: 2rem;
  overflow: hidden;
  
  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
  
  @media (max-width: ${props => props.theme.breakpoints.md}) {
    margin-bottom: 1rem;
  }
`;

const VehicleHeaderInfo = styled.div``;

const VehicleName = styled.h1`
  font-size: 2.5rem;
  color: ${props => props.theme.colors.dark};
  margin-bottom: 0.5rem;
`;

const VehicleModel = styled.p`
  font-size: 1.2rem;
  color: #777;
  margin-bottom: 0.5rem;
`;

const VehicleVIN = styled.p`
  font-size: 0.875rem;
  color: #999;
`;

const StatsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1.5rem;
  margin-bottom: 2rem;
  
  @media (max-width: ${props => props.theme.breakpoints.lg}) {
    grid-template-columns: repeat(2, 1fr);
  }
  
  @media (max-width: ${props => props.theme.breakpoints.sm}) {
    grid-template-columns: 1fr;
  }
`;

const StatCard = styled.div`
  background: white;
  border-radius: 12px;
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.05);
  padding: 1.5rem;
  transition: all 0.3s ease;
  
  &:hover {
    transform: translateY(-5px);
    box-shadow: 0 15px 30px rgba(0, 0, 0, 0.1);
  }
`;

const StatTitle = styled.h3`
  font-size: 1rem;
  color: #777;
  margin-bottom: 0.5rem;
`;

const StatValue = styled.p`
  font-size: 2rem;
  font-weight: 700;
  color: ${props => props.theme.colors.dark};
  margin-bottom: 0.5rem;
`;

const StatSubtext = styled.p`
  font-size: 0.875rem;
  color: #999;
`;

const RefreshButton = styled.button`
  padding: 0.75rem 1.5rem;
  background-color: ${props => props.theme.colors.primary};
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  margin-bottom: 2rem;
  
  &:hover {
    background-color: ${props => props.theme.colors.primary}dd;
  }
  
  &:disabled {
    background-color: #ccc;
    cursor: not-allowed;
  }
`;

const LoadingText = styled.div`
  text-align: center;
  padding: 2rem;
  font-size: 1.2rem;
  color: #777;
`;

const ErrorText = styled.div`
  text-align: center;
  padding: 2rem;
  font-size: 1.2rem;
  color: ${props => props.theme.colors.danger};
  background-color: #fee;
  border-radius: 8px;
  margin-bottom: 2rem;
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

// Format large numbers with commas
const formatNumber = (num) => {
  return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
};

// Convert kilometers to miles
const kmToMiles = (km) => {
  return (km * 0.621371).toFixed(0);
};

// Format as percentage
const formatPercentage = (value) => {
  return `${value}%`;
};

// Format power state
const formatPowerState = (state) => {
  if (!state) return 'Unknown';
  
  switch (state) {
    case 'ready':
      return 'Ready';
    case 'go':
      return 'Active';
    case 'sleep':
      return 'Sleep';
    case 'standby':
      return 'Standby';
    default:
      return state.charAt(0).toUpperCase() + state.slice(1);
  }
};

// Format charging state
const formatChargingState = (state) => {
  if (!state) return 'Unknown';
  
  switch (state) {
    case 'charging_active':
      return 'Charging';
    case 'charging_complete':
      return 'Charge Complete';
    case 'not_charging':
      return 'Not Charging';
    default:
      return state.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  }
};

const VehicleDetails = () => {
  const { vin } = useParams();
  const { isAuthenticated, vehicles, loading: authLoading } = useContext(AuthContext);
  const [vehicleData, setVehicleData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [refreshing, setRefreshing] = useState(false);
  
  const vehicle = vehicles?.find(v => v.vehicle.vin === vin);
  
  const fetchVehicleData = async () => {
    setRefreshing(true);
    try {
      const data = await api.get(`/vehicle/${vin}`);
      setVehicleData(data);
      setError('');
    } catch (err) {
      setError(err.message || 'Failed to load vehicle data');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };
  
  useEffect(() => {
    if (isAuthenticated && vin) {
      fetchVehicleData();
    }
  }, [isAuthenticated, vin]);
  
  if (authLoading) {
    return <LoadingText>Loading...</LoadingText>;
  }
  
  if (!isAuthenticated) {
    return <Navigate to="/login" />;
  }
  
  if (!vehicle) {
    return <Navigate to="/dashboard" />;
  }
  
  const handleRefresh = () => {
    fetchVehicleData();
  };
  
  const parseVehicleData = () => {
    if (!vehicleData || !vehicleData.properties) return {};
    
    const properties = {};
    for (const [key, value] of Object.entries(vehicleData.properties)) {
      properties[key] = value;
    }
    
    return properties;
// Parse properties from the API response
    const batteryLevel = properties.batteryLevel?.value;
    const range = properties.distanceToEmpty?.value;
    const odometer = properties.vehicleMileage?.value;
    const powerState = properties.powerState?.value;
    const chargerStatus = properties.chargerStatus?.value;
    const chargerState = properties.chargerState?.value;
    const cabinTemp = properties.cabinClimateInteriorTemperature?.value;
    const timeToCharge = properties.timeToEndOfCharge?.value;
    const lastUpdated = properties.batteryLevel?.timeStamp;
    
    return {
      batteryLevel,
      range,
      odometer,
      powerState,
      chargerStatus,
      chargerState,
      cabinTemp,
      timeToCharge,
      lastUpdated
    };
  };
  
  const stats = vehicleData ? parseVehicleData() : {};
  
  return (
    <VehicleContainer>
      <VehicleHeader>
        <VehicleImage>
          <img 
            src={getVehicleImageByModel(vehicle.vehicle.model)} 
            alt={vehicle.name || vehicle.vehicle.model} 
          />
        </VehicleImage>
        <VehicleHeaderInfo>
          <VehicleName>{vehicle.name || 'My Rivian'}</VehicleName>
          <VehicleModel>{vehicle.vehicle.model}</VehicleModel>
          <VehicleVIN>VIN: {vehicle.vehicle.vin}</VehicleVIN>
        </VehicleHeaderInfo>
      </VehicleHeader>
      
      <RefreshButton onClick={handleRefresh} disabled={refreshing}>
        {refreshing ? 'Refreshing...' : 'Refresh Data'}
      </RefreshButton>
      
      {error && <ErrorText>{error}</ErrorText>}
      
      {loading ? (
        <LoadingText>Loading vehicle data...</LoadingText>
      ) : (
        <StatsGrid>
          <StatCard>
            <StatTitle>Battery Level</StatTitle>
            <StatValue>{stats.batteryLevel ? formatPercentage(stats.batteryLevel) : 'N/A'}</StatValue>
            <StatSubtext>Current charge level</StatSubtext>
          </StatCard>
          
          <StatCard>
            <StatTitle>Estimated Range</StatTitle>
            <StatValue>{stats.range ? `${kmToMiles(stats.range)} mi` : 'N/A'}</StatValue>
            <StatSubtext>Remaining range</StatSubtext>
          </StatCard>
          
          <StatCard>
            <StatTitle>Odometer</StatTitle>
            <StatValue>{stats.odometer ? `${formatNumber(kmToMiles(stats.odometer))} mi` : 'N/A'}</StatValue>
            <StatSubtext>Total distance traveled</StatSubtext>
          </StatCard>
          
          <StatCard>
            <StatTitle>Power State</StatTitle>
            <StatValue>{stats.powerState ? formatPowerState(stats.powerState) : 'N/A'}</StatValue>
            <StatSubtext>Current vehicle status</StatSubtext>
          </StatCard>
          
          <StatCard>
            <StatTitle>Charging Status</StatTitle>
            <StatValue>{stats.chargerState ? formatChargingState(stats.chargerState) : 'N/A'}</StatValue>
            <StatSubtext>{stats.timeToCharge ? `Time remaining: ${stats.timeToCharge} min` : 'Not currently charging'}</StatSubtext>
          </StatCard>
          
          <StatCard>
            <StatTitle>Cabin Temperature</StatTitle>
            <StatValue>{stats.cabinTemp ? `${stats.cabinTemp}°C` : 'N/A'}</StatValue>
            <StatSubtext>Current interior temperature</StatSubtext>
          </StatCard>
        </StatsGrid>
      )}
    </VehicleContainer>
  );
};

export default VehicleDetails;
