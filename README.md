### Apex Serial

Serial Number management tools for used and demo devices

### Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
# 1. Get the app
cd $PATH_TO_YOUR_BENCH
bench get-app apex_serial

# 2. Install on your site
bench --site [your-site-name] install-app apex_serial

# 3. Migrate database and load fixtures
bench --site [your-site-name] migrate

# 4. Build assets
bench build

# 5. Restart all services
bench restart

# 6. Clear cache
bench --site [your-site-name] clear-cache
```

### Features

- **Serial No Management**: Mark as Used, Send/Receive Demo Device buttons
- **Used Device Workflow**: Transfer devices to "Stores - Used Devices" warehouse
- **Demo Device Workflow**: Track devices assigned to sales representatives
- **Warehouse Management**: Automatic creation of used and demo warehouses

### License

mit

