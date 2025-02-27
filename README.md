cat > /opt/rivian-web/README.md << 'EOF'
# Stats for Adventure

A web interface for the Rivian API that allows you to:
- View vehicle state and information
- Check charging status
- Send commands to your vehicle

## Security Notes

- Authentication tokens are stored only in your browser's localStorage
- No data is stored on the server
- Communication is encrypted via HTTPS
- The application requires Rivian account credentials and MFA verification

## Usage

1. Access the web interface at https://statsforadventure.com
2. Log in with your Rivian account credentials
3. Enter the MFA code sent to your phone
4. View your vehicles and their status
5. Send commands as needed

## Vehicle Commands

To send commands to your vehicle, you need:
1. An enrolled phone in your Rivian account
2. Your private key from the phone enrollment process
3. Select the command and vehicle, then provide the private key

## Maintenance

- Check logs: `journalctl -u rivian-web`
- Restart service: `systemctl restart rivian-web`
- Update application: Pull latest changes and restart service