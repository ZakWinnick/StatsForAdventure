/**
 * Dashboard JavaScript for Rivian Dashboard
 */

// Socket.IO connection for real-time updates
let socket;

// Connect to Socket.IO server
function connectSocket() {
    socket = io();
    
    // Connection events
    socket.on('connect', () => {
        console.log('Connected to server');
    });
    
    socket.on('disconnect', () => {
        console.log('Disconnected from server');
    });
    
    // Vehicle update events
    socket.on('vehicle_update', (data) => {
        console.log('Received vehicle update:', data);
        updateVehicleData(data);
    });
}

// Subscribe to vehicle updates
function subscribeToVehicle(vehicleId) {
    if (socket && socket.connected) {
        socket.emit('subscribe_vehicle', { vehicle_id: vehicleId });
    }
}

// Update vehicle data on the page
function updateVehicleData(data) {
    // Update battery level
    if (data.batteryLevel) {
        const batteryPercent = document.getElementById('battery-percentage');
        const batteryProgress = document.getElementById('battery-progress');
        
        if (batteryPercent) {
            batteryPercent.textContent = `${data.batteryLevel.value.toFixed(1)}%`;
        }
        
        if (batteryProgress) {
            batteryProgress.style.width = `${data.batteryLevel.value}%`;
            batteryProgress.textContent = `${data.batteryLevel.value.toFixed(1)}%`;
        }
    }
    
    // Update range
    if (data.distanceToEmpty) {
        const distanceToEmpty = document.getElementById('distance-to-empty');
        if (distanceToEmpty) {
            distanceToEmpty.textContent = data.distanceToEmpty.value;
        }
    }
    
    // Update power state
    if (data.powerState) {
        const powerState = document.getElementById('power-state');
        if (powerState) {
            powerState.textContent = data.powerState.value;
        }
    }
    
    // Update charging state
    if (data.chargerState) {
        const chargingState = document.getElementById('charging-state');
        if (chargingState) {
            chargingState.textContent = data.chargerState.value.replace('_', ' ');
        }
    }
}

// Format date to local time
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    
    const date = new Date(dateString);
    return date.toLocaleString();
}

// Send a vehicle command
async function sendVehicleCommand(vehicleId, command, params = null) {
    // Get stored phone key configuration
    const configKey = `phone_key_${vehicleId}`;
    const savedConfig = localStorage.getItem(configKey);
    
    if (!savedConfig) {
        alert('Phone key configuration not found. Please configure your phone key first.');
        return;
    }
    
    const config = JSON.parse(savedConfig);
    
    // Validate required fields
    if (!config.phoneId || !config.identityId || !config.vehicleKey || !config.privateKey) {
        alert('Incomplete phone key configuration. Please configure all required fields.');
        return;
    }
    
    // Prepare request data
    const requestData = {
        command: command,
        phone_id: config.phoneId,
        identity_id: config.identityId,
        vehicle_key: config.vehicleKey,
        private_key: config.privateKey
    };
    
    if (params) {
        requestData.params = params;
    }
    
    try {
        // Send the command
        const response = await fetch(`/api/vehicle/${vehicleId}/command`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            alert(`Command sent successfully! Command ID: ${result.command_id}`);
            // You could implement command status polling here
            return result.command_id;
        } else {
            alert(`Error sending command: ${result.error}`);
            return null;
        }
    } catch (error) {
        console.error('Error sending command:', error);
        alert('An error occurred while sending the command. Please try again.');
        return null;
    }
}

// Poll command status
async function pollCommandStatus(commandId, maxAttempts = 10, interval = 2000) {
    let attempts = 0;
    
    const checkStatus = async () => {
        try {
            const response = await fetch(`/api/command/${commandId}`);
            const result = await response.json();
            
            if (response.ok) {
                console.log('Command status:', result);
                
                // Check if command completed
                if (result.state === 3) { // Completed state
                    return result;
                }
                
                // Continue polling if not completed and not reached max attempts
                if (attempts < maxAttempts) {
                    attempts++;
                    setTimeout(checkStatus, interval);
                }
            } else {
                console.error('Error checking command status:', result.error);
            }
        } catch (error) {
            console.error('Error polling command status:', error);
        }
    };
    
    // Start polling
    checkStatus();
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    // Connect to Socket.IO
    connectSocket();
    
    // Add event listeners for control buttons
    addControlButtonListeners();
});

// Add event listeners for control buttons
function addControlButtonListeners() {
    // Example for lock/unlock buttons
    const lockButton = document.querySelector('button[data-command="LOCK_ALL_CLOSURES_FEEDBACK"]');
    if (lockButton) {
        lockButton.addEventListener('click', () => {
            const vehicleId = lockButton.getAttribute('data-vehicle-id');
            sendVehicleCommand(vehicleId, 'LOCK_ALL_CLOSURES_FEEDBACK');
        });
    }
    
    const unlockButton = document.querySelector('button[data-command="UNLOCK_ALL_CLOSURES"]');
    if (unlockButton) {
        unlockButton.addEventListener('click', () => {
            const vehicleId = unlockButton.getAttribute('data-vehicle-id');
            sendVehicleCommand(vehicleId, 'UNLOCK_ALL_CLOSURES');
        });
    }
    
    // Add more button listeners as needed
}