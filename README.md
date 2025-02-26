# Stats For Adventure

A web dashboard for Rivian vehicle owners to monitor and control their vehicles.

## Features

- **Real-time Vehicle Stats**: Battery level, range, door status, and more
- **Charging Information**: View active charging sessions and stats
- **Vehicle Control**: Send commands to your vehicle (lock/unlock, climate control, etc.)
- **Secure Authentication**: Full support for Rivian's MFA authentication
- **Privacy-focused**: No user data stored between sessions

## Security & Privacy

This application:
- Does not store any Rivian credentials
- Only keeps authentication tokens in encrypted, server-side sessions
- Requires re-authentication for each new browser session
- Transmits all data over secure HTTPS

## Installation

### Prerequisites

- Python 3.9+
- A Rivian account with at least one registered vehicle

### Setup

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/stats-for-adventure.git
   cd stats-for-adventure
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file:
   ```
   cp .env.example .env
   ```

5. Edit the `.env` file and set the required configuration values:
   - Generate secure keys for `SECRET_KEY` and `SESSION_SECRET_KEY`
   - Update other settings as needed

## Running the Application

Start the application with:

```
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

Then navigate to `http://localhost:8000` in your web browser.

## Deployment

For production deployment, consider:

1. Setting up a proper web server (Nginx/Apache) in front of the application
2. Using a process manager like Supervisor or systemd
3. Setting `DEBUG=false` in your `.env` file
4. Using HTTPS with proper SSL certificates

### Ubuntu VPS Deployment Example

1. Install required packages:
   ```
   sudo apt update
   sudo apt install -y python3-pip python3-venv nginx
   ```

2. Set up a virtual environment and install dependencies:
   ```
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. Configure Nginx:
   ```
   sudo nano /etc/nginx/sites-available/stats-for-adventure
   ```

   Add the following configuration:
   ```
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

4. Enable the site:
   ```
   sudo ln -s /etc/nginx/sites-available/stats-for-adventure /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

5. Set up SSL with Certbot:
   ```
   sudo apt install -y certbot python3-certbot-nginx
   sudo certbot --nginx -d your-domain.com
   ```

6. Create a systemd service:
   ```
   sudo nano /etc/systemd/system/stats-for-adventure.service
   ```

   Add the following:
   ```
   [Unit]
   Description=Stats For Adventure
   After=network.target

   [Service]
   User=ubuntu
   WorkingDirectory=/path/to/stats-for-adventure
   ExecStart=/path/to/stats-for-adventure/venv/bin/uvicorn backend.main:app --host 127.0.0.1 --port 8000
   Restart=on-failure
   Environment="PATH=/path/to/stats-for-adventure/venv/bin"
   Environment="SECRET_KEY=your-secret-key"
   Environment="SESSION_SECRET_KEY=your-session-secret-key"
   Environment="DEBUG=false"

   [Install]
   WantedBy=multi-user.target
   ```

7. Enable and start the service:
   ```
   sudo systemctl enable stats-for-adventure
   sudo systemctl start stats-for-adventure
   ```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Disclaimer

This is an unofficial application and is not affiliated with, endorsed by, or connected to Rivian Automotive Inc. in any way. Use at your own risk.

## License

This project is licensed under the MIT License - see the LICENSE file for details.