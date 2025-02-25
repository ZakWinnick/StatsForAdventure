/**
 * Socket.IO client for real-time vehicle updates
 */

class RivianSocket {
    constructor() {
        this.socket = null;
        this.connected = false;
        this.authenticated = false;
        this.vehicleSubscriptions = new Set();
        this.eventHandlers = {};
    }

    /**
     * Connect to the Socket.IO server
     */
    connect() {
        if (this.socket) {
            return Promise.resolve();
        }

        return new Promise((resolve, reject) => {
            try {
                this.socket = io();

                // Connection events
                this.socket.on('connect', () => {
                    console.log('Connected to server');
                    this.connected = true;
                    this._triggerEvent('connect');
                    resolve();
                });

                this.socket.on('disconnect', () => {
                    console.log('Disconnected from server');
                    this.connected = false;
                    this.authenticated = false;
                    this._triggerEvent('disconnect');
                });

                // Vehicle update events
                this.socket.on('vehicle_update', (data) => {
                    console.log('Received vehicle update:', data);
                    this._triggerEvent('vehicle_update', data);
                });

                // Error handling
                this.socket.on('connect_error', (error) => {
                    console.error('Connection error:', error);
                    this._triggerEvent('error', error);
                    reject(error);
                });
            } catch (error) {
                console.error('Socket initialization error:', error);
                reject(error);
            }
        });
    }

    /**
     * Authenticate with the server
     * @param {string} userId - User ID
     * @param {string} accessToken - Access token
     */
    authenticate(userId, accessToken) {
        if (!this.connected) {
            return Promise.reject(new Error('Not connected to server'));
        }

        return new Promise((resolve, reject) => {
            this.socket.emit('authenticate', {
                user_id: userId,
                access_token: accessToken
            }, (response) => {
                if (response.error) {
                    console.error('Authentication error:', response.error);
                    reject(new Error(response.error));
                } else {
                    this.authenticated = true;
                    this._triggerEvent('authenticated');
                    resolve(response);
                }
            });
        });
    }

    /**
     * Subscribe to vehicle updates
     * @param {string} vehicleId - Vehicle ID
     */
    subscribeToVehicle(vehicleId) {
        if (!this.connected || !this.authenticated) {
            return Promise.reject(new Error('Not connected or authenticated'));
        }

        return new Promise((resolve, reject) => {
            this.socket.emit('subscribe_vehicle', {
                vehicle_id: vehicleId
            }, (response) => {
                if (response.error) {
                    console.error('Subscription error:', response.error);
                    reject(new Error(response.error));
                } else {
                    this.vehicleSubscriptions.add(vehicleId);
                    this._triggerEvent('subscribed', { vehicleId });
                    resolve(response);
                }
            });
        });
    }

    /**
     * Unsubscribe from vehicle updates
     * @param {string} vehicleId - Vehicle ID
     */
    unsubscribeFromVehicle(vehicleId) {
        if (!this.connected) {
            return Promise.reject(new Error('Not connected to server'));
        }

        return new Promise((resolve, reject) => {
            this.socket.emit('unsubscribe_vehicle', {
                vehicle_id: vehicleId
            }, (response) => {
                if (response.error) {
                    console.error('Unsubscription error:', response.error);
                    reject(new Error(response.error));
                } else {
                    this.vehicleSubscriptions.delete(vehicleId);
                    this._triggerEvent('unsubscribed', { vehicleId });
                    resolve(response);
                }
            });
        });
    }

    /**
     * Disconnect from the server
     */
    disconnect() {
        if (this.socket) {
            this.socket.disconnect();
            this.socket = null;
            this.connected = false;
            this.authenticated = false;
            this.vehicleSubscriptions.clear();
        }
    }

    /**
     * Register an event handler
     * @param {string} event - Event name
     * @param {Function} handler - Event handler
     */
    on(event, handler) {
        if (!this.eventHandlers[event]) {
            this.eventHandlers[event] = [];
        }
        this.eventHandlers[event].push(handler);
    }

    /**
     * Remove an event handler
     * @param {string} event - Event name
     * @param {Function} handler - Event handler
     */
    off(event, handler) {
        if (this.eventHandlers[event]) {
            this.eventHandlers[event] = this.eventHandlers[event].filter(h => h !== handler);
        }
    }

    /**
     * Trigger an event
     * @param {string} event - Event name
     * @param {any} data - Event data
     * @private
     */
    _triggerEvent(event, data) {
        if (this.eventHandlers[event]) {
            for (const handler of this.eventHandlers[event]) {
                handler(data);
            }
        }
    }
}

// Create a global instance
const rivianSocket = new RivianSocket();