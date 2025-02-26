// Load available commands
async function loadAvailableCommands() {
    const commandsSelect = document.getElementById('command-select');
    if (!commandsSelect) return;
    
    try {
        const response = await fetch('/api/commands/available');
        const data = await response.json();
        
        // Clear existing options
        commandsSelect.innerHTML = '<option value="">Select a command</option>';
        
        // Add options from the API
        data.commands.forEach(command => {
            const option = document.createElement('option');
            option.value = command;
            option.textContent = command.replace(/_/g, ' ');
            commandsSelect.appendChild(option);
        });
        
        // Store command info for later use
        window.commandsInfo = data.commands_info;
        
        // Set up command change handler
        commandsSelect.addEventListener('change', handleCommandChange);
    } catch (error) {
        console.error('Error loading commands:', error);
    }
}

// Handle command selection change
function handleCommandChange() {
    const commandSelect = document.getElementById('command-select');
    const selectedCommand = commandSelect.value;
    const paramsContainer = document.getElementById('command-params-container');
    
    // Clear existing params
    paramsContainer.innerHTML = '';
    
    if (!selectedCommand || !window.commandsInfo || !window.commandsInfo[selectedCommand]) {
        return;
    }
    
    const commandInfo = window.commandsInfo[selectedCommand];
    const params = commandInfo.params || {};
    
    // Add description
    if (commandInfo.description) {
        const description = document.createElement('div');
        description.className = 'text-gray-600 mb-3';
        description.textContent = commandInfo.description;
        paramsContainer.appendChild(description);
    }
    
    // Add params if any
    if (Object.keys(params).length > 0) {
        const paramsTitle = document.createElement('h4');
        paramsTitle.className = 'font-semibold mb-2';
        paramsTitle.textContent = 'Parameters:';
        paramsContainer.appendChild(paramsTitle);
        
        Object.entries(params).forEach(([paramName, description]) => {
            const formGroup = document.createElement('div');
            formGroup.className = 'mb-3';
            
            const label = document.createElement('label');
            label.className = 'block text-gray-700 mb-1';
            label.textContent = paramName;
            label.htmlFor = `param-${paramName}`;
            
            const input = document.createElement('input');
            input.className = 'w-full px-3 py-2 border rounded-lg';
            input.type = 'text';
            input.id = `param-${paramName}`;
            input.name = paramName;
            input.placeholder = description;
            
            formGroup.appendChild(label);
            formGroup.appendChild(input);
            paramsContainer.appendChild(formGroup);
        });
    }
}

// Send vehicle command
async function sendVehicleCommand(vehicleId, phoneDetails) {
    const commandSelect = document.getElementById('command-select');
    const selectedCommand = commandSelect.value;
    
    if (!selectedCommand) {
        alert('Please select a command');
        return;
    }
    
    const tokens = JSON.parse(localStorage.getItem('rivian_tokens'));
    if (!tokens) {
        alert('Authentication required');
        return;
    }
    
    // Collect parameters
    const params = {};
    const paramsContainer = document.getElementById('command-params-container');
    const inputs = paramsContainer.querySelectorAll('input');
    inputs.forEach(input => {
        const paramName = input.name;
        let value = input.value.trim();
        
        // Convert to appropriate type
        if (!isNaN(value) && value !== '') {
            value = Number(value);
        }
        
        if (value !== '') {
            params[paramName] = value;
        }
    });
    
    // Show loading state
    const resultDiv = document.getElementById('command-result');
    resultDiv.innerHTML = '<div class="text-blue-600">Sending command...</div>';
    
    try {
        const formData = new FormData();
        formData.append('vehicle_id', vehicleId);
        formData.append('command', selectedCommand);
        formData.append('phone_id', phoneDetails.phoneId);
        formData.append('identity_id', phoneDetails.identityId);
        formData.append('vehicle_key', phoneDetails.vehicleKey);
        formData.append('private_key', phoneDetails.privateKey);
        
        if (Object.keys(params).length > 0) {
            formData.append('params', JSON.stringify(params));
        }
        
        const response = await fetch('/api/commands/send', {
            method: 'POST',
            headers: {
                'X-CSRF-Token': tokens.csrf_token,
                'X-App-Session-Token': tokens.app_session_token,
                'X-User-Session-Token': tokens.user_session_token
            },
            body: formData
        });
        
        if (!response.ok) {
            throw new Error('Failed to send command');
        }
        
        const data = await response.json();
        resultDiv.innerHTML = `
            <div class="bg-green-100 text-green-700 p-4 rounded-lg">
                Command sent successfully! Command ID: ${data.command_id}
                <button 
                    class="ml-2 bg-green-500 text-white px-2 py-1 rounded hover:bg-green-600"
                    onclick="checkCommandStatus('${data.command_id}')"
                >
                    Check Status
                </button>
            </div>
        `;
    } catch (error) {
        console.error('Error sending command:', error);
        resultDiv.innerHTML = `<div class="bg-red-100 text-red-700 p-4 rounded-lg">Error: ${error.message}</div>`;
    }
}

// Check command status
async function checkCommandStatus(commandId) {
    const tokens = JSON.parse(localStorage.getItem('rivian_tokens'));
    if (!tokens) return;
    
    const resultDiv = document.getElementById('command-result');
    resultDiv.innerHTML = '<div class="text-blue-600">Checking command status...</div>';
    
    try {
        const response = await fetch(`/api/commands/status/${commandId}`, {
            headers: {
                'X-CSRF-Token': tokens.csrf_token,
                'X-App-Session-Token': tokens.app_session_token,
                'X-User-Session-Token': tokens.user_session_token
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to check command status');
        }
        
        const data = await response.json();
        const commandState = data?.data?.getVehicleCommand?.state || 'unknown';
        const stateText = commandState === 1 ? 'Pending' : 
                         commandState === 2 ? 'In Progress' : 
                         commandState === 3 ? 'Completed' :
                         commandState === 4 ? 'Failed' : 'Unknown';
        
        resultDiv.innerHTML = `
            <div class="bg-blue-100 text-blue-700 p-4 rounded-lg">
                Command Status: ${stateText} (State: ${commandState})
                <button 
                    class="ml-2 bg-blue-500 text-white px-2 py-1 rounded hover:bg-blue-600"
                    onclick="checkCommandStatus('${commandId}')"
                >
                    Refresh
                </button>
            </div>
        `;
    } catch (error) {
        console.error('Error checking command status:', error);
        resultDiv.innerHTML = `<div class="bg-red-100 text-red-700 p-4 rounded-lg">Error: ${error.message}</div>`;
    }
}
