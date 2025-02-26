/**
 * Stats For Adventure - Frontend JavaScript
 */

// DOM Elements
const loginSection = document.getElementById('login-section');
const otpSection = document.getElementById('otp-section');
const dashboardSection = document.getElementById('dashboard-section');
const loginForm = document.getElementById('login-form');
const otpForm = document.getElementById('otp-form');
const loginError = document.getElementById('login-error');
const otpError = document.getElementById('otp-error');
const logoutButton = document.getElementById('logout-button');
const vehicleList = document.getElementById('vehicle-list');
const commandButtons = document.getElementById('command-buttons');
const commandResult = document.getElementById('command-result');
const commandSuccess = document.getElementById('command-success');
const commandError = document.getElementById('command-error');

// State variables
let selectedVehicleId = null;
let vehicleState = null;
let chargingData = null;
let supportedCommands = null;

// Initialize the application
async function init() {
    // Check session status
    const sessionStatus = await checkSessionStatus();
    
    if (sessionStatus.authenticated) {
        // Already authenticated, go to dashboard
        showDashboard();
        loadVehicles();
        loadSupportedCommands();
    } else if (sessionStatus.otp_pending) {
        // OTP verification needed
        showOtpVerification();
    } else {
        // Show login form
        showLoginForm();
    }
    
    // Set up event listeners
    setupEventListeners();
}

// Show the login form
function showLoginForm() {
    loginSection.classList.remove('hidden');
    otpSection.classList.add('hidden');
    dashboardSection.classList.add('hidden');
}

// Show the OTP verification form
function showOtpVerification() {
    loginSection.classList.add('hidden');
    otpSection.classList.remove('hidden');
    dashboardSection.classList.add('hidden');
}

// Show the dashboard
function showDashboard() {
    loginSection.classList.add('hidden');
    otpSection.classList.add('hidden');
    dashboardSection.classList.remove('hidden');
}

// Set up event listeners
function setupEventListeners() {
    // Login form submission
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = new FormData(loginForm);
        const loginData = {
            email: formData.get('email'),
            password: formData.get('password')
        };
        
        try {
            loginError.classList.add('hidden');
            
            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(loginData),
                credentials: 'include'
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.detail || 'Login failed');
            }
            
            if (data.requires_otp) {
                showOtpVerification();
            } else {
                showDashboard();
                loadVehicles();
                loadSupportedCommands();
            }
        } catch (error) {
            loginError.textContent = error.message;
            loginError.classList.remove('hidden');
        }
    });
    
    // OTP form submission
    otpForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = new FormData(otpForm);
        const otpData = {
            otp_code: formData.get('otp_code')
        };
        
        try {
            otpError.classList.add('hidden');
            
            const response = await fetch('/api/auth/verify-otp', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(otpData),
                credentials: 'include'
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.detail || 'OTP verification failed');
            }
            
            showDashboard();
            loadVehicles();
            loadSupportedCommands();
        } catch (error) {
            otpError.textContent = error.message;
            otpError.classList.remove('hidden');
        }
    });
    
    // Logout button
    logoutButton.addEventListener('click', async () => {
        try {
            await fetch('/api/auth/logout', {
                method: 'POST',
                credentials: 'include'
            });
            
            // Clear state
            selectedVehicleId = null;
            vehicleState = null;
            chargingData = null;
            supportedCommands = null;
            
            // Go back to login form
            showLoginForm();
        } catch (error) {
            console.error('Logout failed:', error);
        }
    });
}

// Check session status
async function checkSessionStatus() {
    try {
        const response = await fetch('/api/auth/session-status', {
            credentials: 'include'
        });
        
        return await response.json();
    } catch (error) {
        console.error('Failed to check session status:', error);
        return { authenticated: false, otp_pending: false };
    }
}

// Load user's vehicles
async function loadVehicles() {
    try {
        const response = await fetch('/api/vehicles/list', {
            credentials: 'include'
        });
        
        if (!response.ok) {
            throw new Error('Failed to load vehicles');
        }
        
        const vehicles = await response.json();
        
        // Clear previous list
        vehicleList.innerHTML = '';
        
        // Display vehicles
        vehicles.forEach(vehicle => {
            const vehicleElement = document.createElement('div');
            vehicleElement.className = 'p-3 border rounded cursor-pointer hover:bg-gray-100';
            vehicleElement.dataset.vehicleId = vehicle.id;
            vehicleElement.innerHTML = `
                <div class="font-medium">${vehicle.name}</div>
                <div class="text-sm text-gray-500">${vehicle.model} ${vehicle.model_year || ''}</div>
                <div class="text-xs text-gray-400">VIN: ${vehicle.vin}</div>
            `;
            
            // Add click event to select vehicle
            vehicleElement.addEventListener('click', () => {
                selectVehicle(vehicle.id);
                // Update visual selection
                document.querySelectorAll('#vehicle-list > div').forEach(el => {
                    el.classList.remove('bg-blue-50', 'border-blue-500');
                });
                vehicleElement.classList.add('bg-blue-50', 'border-blue-500');
            });
            
            vehicleList.appendChild(vehicleElement);
        });
        
        // If vehicles exist, select the first one
        if (vehicles.length > 0) {
            selectVehicle(vehicles[0].id);
            // Highlight the first vehicle
            const firstVehicleElement = vehicleList.querySelector('div');
            if (firstVehicleElement) {
                firstVehicleElement.classList.add('bg-blue-50', 'border-blue-500');
            }
        }
    } catch (error) {
        console.error('Failed to load vehicles:', error);
    }
}

// Select a vehicle
async function selectVehicle(vehicleId) {
    try {
        const response = await fetch(`/api/vehicles/select/${vehicleId}`, {
            method: 'POST',
            credentials: 'include'
        });
        
        if (!response.ok) {
            throw new Error('Failed to select vehicle');
        }
        
        selectedVehicleId = vehicleId;
        
        // Load vehicle data
        loadVehicleState();
        loadChargingData();
    } catch (error) {
        console.error('Failed to select vehicle:', error);
    }
}

// Load vehicle state
async function loadVehicleState() {
    try {
        const response = await fetch('/api/vehicles/state', {
            credentials: 'include'
        });
        
        if (!response.ok) {
            throw new Error('Failed to load vehicle state');
        }
        
        vehicleState = await response.json();
        
        // Update UI with vehicle state
        updateVehicleStateUI();
    } catch (error) {
        console.error('Failed to load vehicle state:', error);
    }
}

// Load charging data
async function loadChargingData() {
    try {
        const response = await fetch('/api/vehicles/charging', {
            credentials: 'include'
        });
        
        if (!response.ok) {
            throw new Error('Failed to load charging data');
        }
        
        chargingData = await response.json();
        
        // Update UI with charging data
        updateChargingDataUI();
    } catch (error) {
        console.error('Failed to load charging data:', error);
    }
}

// Load supported commands
async function loadSupportedCommands() {
    try {
        const response = await fetch('/api/commands/supported', {
            credentials: 'include'
        });
        
        if (!response.ok) {
            throw new Error('Failed to load supported commands');
        }
        
        supportedCommands = await response.json();
        
        // Update UI with supported commands
        updateCommandsUI();
    } catch (error) {
        console.error('Failed to load supported commands:', error);
    }
}

// Update UI with vehicle state
function updateVehicleStateUI() {
    if (!vehicleState) return;
    
    // Battery status
    const batteryPercentage = document.getElementById('battery-percentage');
    const batteryRange = document.getElementById('battery-range');
    const batteryBar = document.getElementById('battery-bar');
    const batteryLimit = document.getElementById('battery-limit');
    const powerState = document.getElementById('power-state');
    
    if (vehicleState.battery_level !== null) {
        batteryPercentage.textContent = `${Math.round(vehicleState.battery_level)}%`;
        batteryBar.style.width = `${vehicleState.battery_level}%`;
        
        // Adjust color based on level
        if (vehicleState.battery_level > 50) {
            batteryBar.className = 'bg-green-600 h-4 rounded-full';
        } else if (vehicleState.battery_level > 20) {
            batteryBar.className = 'bg-yellow-500 h-4 rounded-full';
        } else {
            batteryBar.className = 'bg-red-500 h-4 rounded-full';
        }
    }
    
    if (vehicleState.distance_to_empty !== null) {
        batteryRange.textContent = `${vehicleState.distance_to_empty} mi`;
    }
    
    if (vehicleState.battery_limit !== null) {
        batteryLimit.textContent = `${vehicleState.battery_limit}%`;
    }
    
    if (vehicleState.power_state !== null) {
        powerState.textContent = formatStateValue(vehicleState.power_state);
    }
    
    // Vehicle status
    const vehicleOnlineStatus = document.getElementById('vehicle-online-status');
    const vehicleOdometer = document.getElementById('vehicle-odometer');
    const doorsStatus = document.getElementById('doors-status');
    const windowsStatus = document.getElementById('windows-status');
    
    vehicleOnlineStatus.textContent = vehicleState.is_online ? 'Online' : 'Offline';
    
    if (vehicleState.vehicle_mileage !== null) {
        // Convert from millimeters to miles and round to 1 decimal place
        const miles = (vehicleState.vehicle_mileage / 1609344).toFixed(1);
        vehicleOdometer.textContent = `${miles} mi`;
    }
    
    doorsStatus.textContent = vehicleState.doors_locked ? 'Locked' : 'Unlocked';
    windowsStatus.textContent = vehicleState.windows_closed ? 'Closed' : 'Open';
    
    // Vehicle location
    const vehicleLocation = document.getElementById('vehicle-location');
    
    if (vehicleState.latitude !== null && vehicleState.longitude !== null) {
        vehicleLocation.innerHTML = `
            <p>Latitude: ${vehicleState.latitude.toFixed(6)}</p>
            <p>Longitude: ${vehicleState.longitude.toFixed(6)}</p>
            <p class="mt-2">
                <a href="https://maps.google.com/?q=${vehicleState.latitude},${vehicleState.longitude}" 
                   target="_blank" class="text-blue-600 hover:underline">View on Google Maps</a>
            </p>
        `;
    } else {
        vehicleLocation.innerHTML = '<p class="text-gray-500">Location data not available</p>';
    }
}

// Update UI with charging data
function updateChargingDataUI() {
    const noChargingData = document.getElementById('no-charging-data');
    const chargingDataSection = document.getElementById('charging-data');
    const chargingStatus = document.getElementById('charging-status');
    const chargingPower = document.getElementById('charging-power');
    const chargingTimeRemaining = document.getElementById('charging-time-remaining');
    const chargingRangeAdded = document.getElementById('charging-range-added');
    
    if (!chargingData || !chargingData.charging_status) {
        noChargingData.classList.remove('hidden');
        chargingDataSection.classList.add('hidden');
        return;
    }
    
    noChargingData.classList.add('hidden');
    chargingDataSection.classList.remove('hidden');
    
    chargingStatus.textContent = formatStateValue(chargingData.charging_status);
    
    if (chargingData.power !== null) {
        chargingPower.textContent = `${chargingData.power} kW`;
    }
    
    if (chargingData.time_remaining !== null) {
        const hours = Math.floor(chargingData.time_remaining / 3600);
        const minutes = Math.floor((chargingData.time_remaining % 3600) / 60);
        chargingTimeRemaining.textContent = `${hours}h ${minutes}m`;
    }
    
    if (chargingData.range_added !== null) {
        chargingRangeAdded.textContent = `${Math.round(chargingData.range_added)} mi`;
    }
}

// Update UI with supported commands
function updateCommandsUI() {
    if (!supportedCommands) return;
    
    // Clear previous buttons
    commandButtons.innerHTML = '';
    
    // Filter for common useful commands
    const usefulCommands = [
        'WAKE_VEHICLE',
        'HONK_AND_FLASH_LIGHTS',
        'UNLOCK_ALL_CLOSURES',
        'LOCK_ALL_CLOSURES_FEEDBACK',
        'CHARGING_LIMITS',
        'START_CHARGING',
        'STOP_CHARGING',
        'VEHICLE_CABIN_PRECONDITION_ENABLE',
        'VEHICLE_CABIN_PRECONDITION_DISABLE',
        'OPEN_FRUNK',
        'CLOSE_FRUNK',
        'OPEN_ALL_WINDOWS',
        'CLOSE_ALL_WINDOWS'
    ];
    
    // Create buttons for each command
    usefulCommands.forEach(command => {
        if (supportedCommands.commands.includes(command)) {
            const button = document.createElement('button');
            button.className = 'p-3 bg-blue-100 rounded hover:bg-blue-200 text-center';
            button.textContent = formatCommandName(command);
            button.dataset.command = command;
            
            button.addEventListener('click', () => {
                if (command === 'CHARGING_LIMITS') {
                    // Special handling for charging limits
                    const limit = prompt('Enter battery charge limit (50-100%):', '80');
                    if (limit && !isNaN(limit) && limit >= 50 && limit <= 100) {
                        sendCommand(command, { SOC_limit: parseInt(limit) });
                    }
                } else {
                    sendCommand(command);
                }
            });
            
            commandButtons.appendChild(button);
        }
    });
}

// Send a command to the vehicle
async function sendCommand(command, params = null) {
    try {
        // Hide previous result
        commandResult.classList.add('hidden');
        commandSuccess.classList.add('hidden');
        commandError.classList.add('hidden');
        
        const response = await fetch('/api/commands', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                command: command,
                params: params
            }),
            credentials: 'include'
        });
        
        const data = await response.json();
        
        // Show result
        commandResult.classList.remove('hidden');
        
        if (response.ok) {
            commandSuccess.textContent = data.message;
            commandSuccess.classList.remove('hidden');
            
            // Refresh vehicle state after command
            setTimeout(() => {
                loadVehicleState();
                loadChargingData();
            }, 2000);
        } else {
            commandError.textContent = data.detail || 'Command failed';
            commandError.classList.remove('hidden');
        }
    } catch (error) {
        console.error('Failed to send command:', error);
        
        // Show error
        commandResult.classList.remove('hidden');
        commandError.textContent = error.message;
        commandError.classList.remove('hidden');
    }
}

// Format command name for display
function formatCommandName(command) {
    return command
        .replace(/_/g, ' ')
        .replace(/\b\w/g, l => l.toUpperCase())
        .replace(/Hvac/g, 'HVAC')
        .replace(/Cabin/g, 'Cabin')
        .replace(/Vehicle/g, 'Vehicle')
        .replace(/Soc/g, 'SOC');
}

// Format state value for display
function formatStateValue(value) {
    if (!value) return '--';
    
    // Replace underscores with spaces and capitalize first letter of each word
    return value
        .replace(/_/g, ' ')
        .replace(/\b\w/g, l => l.toUpperCase());
}

// Refresh data at regular intervals
function startDataRefresh() {
    // Refresh every 30 seconds
    setInterval(() => {
        if (selectedVehicleId) {
            loadVehicleState();
            loadChargingData();
        }
    }, 30000);
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    init();
    startDataRefresh();
});