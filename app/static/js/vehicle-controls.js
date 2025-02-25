/**
 * Vehicle controls JavaScript for Rivian Dashboard
 */

// Command configuration
const COMMANDS = {
    LOCK: {
        id: 'LOCK_ALL_CLOSURES_FEEDBACK',
        name: 'Lock Vehicle',
        icon: 'lock',
        description: 'Lock all doors and closures',
        successMessage: 'Vehicle locked successfully'
    },
    UNLOCK: {
        id: 'UNLOCK_ALL_CLOSURES',
        name: 'Unlock Vehicle',
        icon: 'unlock',
        description: 'Unlock all doors and closures',
        successMessage: 'Vehicle unlocked successfully'
    },
    CLIMATE_START: {
        id: 'START_CLIMATE',
        name: 'Start Climate',
        icon: 'snowflake',
        description: 'Start climate control system',
        successMessage: 'Climate control started successfully'
    },
    CLIMATE_STOP: {
        id: 'STOP_CLIMATE',
        name: 'Stop Climate',
        icon: 'power-off',
        description: 'Stop climate control system',
        successMessage: 'Climate control stopped successfully'
    },
    OPEN_FRUNK: {
        id: 'OPEN_FRONT_TRUNK',
        name: 'Open Frunk',
        icon: 'box-open',
        description: 'Open the front trunk',
        successMessage: 'Front trunk opened successfully'
    },
    START_CHARGING: {
        id: 'START_CHARGING',
        name: 'Start Charging',
        icon: 'bolt',
        description: 'Start charging if plugged in',
        successMessage: 'Charging started successfully'
    },
    HONK_AND_FLASH: {
        id: 'HONK_AND_FLASH',
        name: 'Honk & Flash',
        icon: 'volume-up',
        description: 'Honk horn and flash lights',
        successMessage: 'Honk and flash command sent successfully'
    },
    WAKE_VEHICLE: {
        id: 'WAKE_VEHICLE',
        name: 'Wake Vehicle',
        icon: 'bell',
        description: 'Wake up the vehicle',
        successMessage: 'Wake command sent successfully'
    }
};

// Store vehicle information
let vehicleData = {};
// Track active command requests
const activeCommands = new Map();
// Phone key configuration
let phoneKeyConfig = null;

/**
 * Initialize vehicle controls
 * @param {Object} vehicle Vehicle data
 */
function initVehicleControls(vehicle) {
    // Store vehicle data
    vehicleData = vehicle;
    
    // Load phone key configuration
    loadPhoneKeyConfig();
    
    // Initialize command buttons
    initCommandButtons();
    
    // Initialize phone key form
    initPhoneKeyForm();
}

/**
 * Load phone key configuration from localStorage
 */
function loadPhoneKeyConfig() {
    const configKey = `phone_key_${vehicleData.id}`;
    const savedConfig = localStorage.getItem(configKey);
    
    if (savedConfig) {
        phoneKeyConfig = JSON.parse(savedConfig);
        
        // Fill form fields
        document.getElementById('phoneId').value = phoneKeyConfig.phoneId || '';
        document.getElementById('identityId').value = phoneKeyConfig.identityId || '';
        document.getElementById('vehicleKey').value = phoneKeyConfig.vehicleKey || '';
        document.getElementById('privateKey').value = phoneKeyConfig.privateKey || '';
        
        // Enable command buttons if we have all required data
        if (phoneKeyConfig.phoneId && phoneKeyConfig.identityId && 
            phoneKeyConfig.vehicleKey && phoneKeyConfig.privateKey) {
            enableCommandButtons();
        }
    }
}

/**
 * Save phone key configuration to localStorage
 */
function savePhoneKeyConfig() {
    const phoneId = document.getElementById('phoneId').value.trim();
    const identityId = document.getElementById('identityId').value.trim();
    const vehicleKey = document.getElementById('vehicleKey').value.trim();
    const privateKey = document.getElementById('privateKey').value.trim();
    
    // Validate required fields
    if (!phoneId || !identityId || !vehicleKey || !privateKey) {
        showAlert('All fields are required to enable vehicle commands.', 'danger');
        return false;
    }
    
    // Save configuration to localStorage
    const configKey = `phone_key_${vehicleData.id}`;
    phoneKeyConfig = {
        phoneId,
        identityId,
        vehicleKey,
        privateKey
    };
    
    localStorage.setItem(configKey, JSON.stringify(phoneKeyConfig));
    
    // Enable command buttons
    enableCommandButtons();
    
    // Close modal
    const modal = bootstrap.Modal.getInstance(document.getElementById('phoneKeyModal'));
    if (modal) {
        modal.hide();
    }
    
    showAlert('Phone key configuration saved successfully.', 'success');
    return true;
}

/**
 * Initialize command buttons
 */
function initCommandButtons() {
    // Get all command buttons
    const buttons = document.querySelectorAll('[data-command]');
    
    buttons.forEach(button => {
        const commandId = button.getAttribute('data-command');
        const command = COMMANDS[commandId];
        
        if (command) {
            button.innerHTML = `<i class="fas fa-${command.icon} me-2"></i>${command.name}`;
            button.setAttribute('title', command.description);
            
            // Add click event listener
            button.addEventListener('click', () => {
                executeCommand(command);
            });
        }
    });
}

/**
 * Enable command buttons
 */
function enableCommandButtons() {
    document.querySelectorAll('[data-command]').forEach(button => {
        button.disabled = false;
        button.classList.remove('btn-outline-secondary');
        button.classList.add('btn-outline-primary');
    });
}

/**
 * Initialize phone key form
 */
function initPhoneKeyForm() {
    const saveButton = document.getElementById('savePhoneKey');
    if (saveButton) {
        saveButton.addEventListener('click', savePhoneKeyConfig);
    }
}

/**
 * Execute a vehicle command
 * @param {Object} command Command configuration
 */
async function executeCommand(command) {
    // Check if phone key is configured
    if (!phoneKeyConfig) {
        showAlert('Please configure your phone key first.', 'warning');
        
        // Show phone key modal
        const phoneKeyModal = new bootstrap.Modal(document.getElementById('phoneKeyModal'));
        phoneKeyModal.show();
        
        return;
    }
    
    // Check if all required fields are present
    if (!phoneKeyConfig.phoneId || !phoneKeyConfig.identityId || 
        !phoneKeyConfig.vehicleKey || !phoneKeyConfig.privateKey) {
        showAlert('Incomplete phone key configuration. Please configure all required fields.', 'warning');
        
        // Show phone key modal
        const phoneKeyModal = new bootstrap.Modal(document.getElementById('phoneKeyModal'));
        phoneKeyModal.show();
        
        return;
    }
    
    // Confirm command execution
    if (!confirm(`Are you sure you want to execute the "${command.name}" command?`)) {
        return;
    }
    
    // Show loading state
    const button = document.querySelector(`[data-command="${command.id}"]`);
    const originalText = button.innerHTML;
    button.disabled = true;
    button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Sending...';
    
    try {
        // Get CSRF token
        const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
        
        // Prepare request data
        const requestData = {
            command: command.id,
            phone_id: phoneKeyConfig.phoneId,
            identity_id: phoneKeyConfig.identityId,
            vehicle_key: phoneKeyConfig.vehicleKey,
            private_key: phoneKeyConfig.privateKey,
            _csrf_token: csrfToken
        };
        
        // Send the command
        const response = await fetch(`/api/vehicle/${vehicleData.id}/command`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': csrfToken
            },
            body: JSON.stringify(requestData)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showAlert(`${command.name} command sent successfully!`, 'success');
            
            // Track command for status updates
            if (result.command_id) {
                activeCommands.set(result.command_id, {
                    command: command,
                    timestamp: new Date(),
                    status: 'pending'
                });
                
                // Poll for command status
                pollCommandStatus(result.command_id);
            }
        } else {
            showAlert(`Error: ${result.error || 'Failed to send command'}`, 'danger');
        }
    } catch (error) {
        console.error('Error sending command:', error);
        showAlert(`Error: ${error.message || 'An error occurred while sending the command'}`, 'danger');
    } finally {
        // Restore button state
        button.innerHTML = originalText;
        button.disabled = false;
    }
}

/**
 * Poll command status until completed or failed
 * @param {string} commandId Command ID
 * @param {number} maxAttempts Maximum number of polling attempts
 * @param {number} interval Polling interval in milliseconds
 */
async function pollCommandStatus(commandId, maxAttempts = 10, interval = 2000) {
    let attempts = 0;
    
    const checkStatus = async () => {
        try {
            // Check if command is still being tracked
            if (!activeCommands.has(commandId)) {
                return;
            }
            
            // Get command data
            const commandData = activeCommands.get(commandId);
            
            const response = await fetch(`/api/command/${commandId}`);
            const result = await response.json();
            
            if (response.ok) {
                console.log('Command status:', result);
                
                // Update command status
                commandData.status = result.command_status;
                activeCommands.set(commandId, commandData);
                
                // Check if command completed
                if (result.command_status === 3) { // Completed
                    showAlert(`${commandData.command.successMessage}`, 'success');
                    activeCommands.delete(commandId);
                    return;
                }
                
                // Check if command failed
                if (result.command_status === 2) { // Failed
                    showAlert(`${commandData.command.name} command failed. Please try again.`, 'danger');
                    activeCommands.delete(commandId);
                    return;
                }
                
                // Continue polling if not completed and not reached max attempts
                if (attempts < maxAttempts) {
                    attempts++;
                    setTimeout(checkStatus, interval);
                } else {
                    // Max attempts reached, stop polling
                    activeCommands.delete(commandId);
                }
            } else {
                console.error('Error checking command status:', result.error);
                activeCommands.delete(commandId);
            }
        } catch (error) {
            console.error('Error polling command status:', error);
            activeCommands.delete(commandId);
        }
    };
    
    // Start polling
    checkStatus();
}

/**
 * Show an alert message
 * @param {string} message Alert message
 * @param {string} type Alert type (success, info, warning, danger)
 */
function showAlert(message, type = 'info') {
    const alertsContainer = document.getElementById('alerts-container');
    if (!alertsContainer) {
        console.error('Alerts container not found');
        return;
    }
    
    const alertId = `alert-${Date.now()}`;
    const alertHtml = `
        <div id="${alertId}" class="alert alert-${type} alert-dismissible fade show">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    alertsContainer.innerHTML += alertHtml;
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        const alertElement = document.getElementById(alertId);
        if (alertElement) {
            const bsAlert = new bootstrap.Alert(alertElement);
            bsAlert.close();
        }
    }, 5000);
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    // Check if vehicle data is available on the page
    const vehicleDataElement = document.getElementById('vehicle-data');
    if (vehicleDataElement) {
        try {
            const vehicle = JSON.parse(vehicleDataElement.textContent);
            initVehicleControls(vehicle);
        } catch (error) {
            console.error('Error parsing vehicle data:', error);
        }
    }
});