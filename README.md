# GS-Pass-Scheduling
Pass Scheduling API for ground stations and satellites

## Maintenance

Scheduled cleanup (recommended via cron):

```bash
python scripts/cleanup_reservations.py
```

Example cron entry (runs every 48 hours at 2am):

```cron
0 2 */2 * * cd /Users/amaebong/Documents/Git/GS-Pass-Scheduling && /usr/bin/python3 scripts/cleanup_reservations.py
```
