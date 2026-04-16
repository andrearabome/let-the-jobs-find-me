# Greenhouse Integration Setup

This application now includes integration with Greenhouse job board API to automatically fetch job listings.

## How to Add Greenhouse Board Tokens

1. Open the `greenhouse_config.py` file
2. Add your Greenhouse board tokens to the `GREENHOUSE_BOARDS` list

### Configuration Example

```python
GREENHOUSE_BOARDS = [
    {
        "board_token": "yourbodtoken1",
        "company_name": "Company One",
        "include_locations": ["Ottawa", "Toronto"],  # Optional - filters jobs by location
        "include_roles": ["UI/UX", "Analyst"]  # Optional - filters jobs by role
    },
    {
        "board_token": "yourboardtoken2",
        "company_name": "Company Two",
        # No filters - will include all jobs from this board
    }
]
```

## Finding Your Greenhouse Board Token

Your board token is typically in your company's Greenhouse job board URL:
- Check your company's career page URL
- Contact the company's HR/Recruiting team
- Look for URLs like: `https://boards.greenhouse.io/BOARDTOKEN`

## Using the API

### Sync Jobs from Greenhouse

Send a POST request to import all jobs from your configured Greenhouse boards:

```bash
curl -X POST http://localhost:5000/api/sync-greenhouse
```

Response:
```json
{
  "success": true,
  "imported": 15
}
```

The endpoint will:
- Fetch all jobs from your configured Greenhouse boards
- Apply location filters if specified
- Apply role filters if specified
- Skip duplicate jobs (already in database)
- Store jobs in the local database

### Location & Role Filtering

Optional filters in `greenhouse_config.py`:

- **include_locations**: Only import jobs from these locations
  - Example: `["Ottawa", "Guelph", "Toronto", "Mississauga"]`
  - Leave empty or omit to include all locations

- **include_roles**: Only import jobs with these roles/departments
  - Example: `["UI/UX", "Research", "Analyst"]`
  - Leave empty or omit to include all roles

### API Endpoints

- `GET /api/jobs` - Get all imported jobs (with optional filters)
  - Query params: `?role=UI/UX&location=Ottawa&search=keyword`
- `POST /api/sync-greenhouse` - Sync jobs from Greenhouse boards
- `GET /api/filters` - Get available filter options

## Notes

- The Greenhouse Job Board API has no authentication requirements
- Jobs are deduplicated using title + company + URL
- Location and role filtering is case-insensitive
- The sync process may take a few seconds depending on the number of jobs

## Troubleshooting

- **No jobs imported**: Verify board tokens are correct in `greenhouse_config.py`
- **Connection error**: Check your internet connection and firewall
- **Wrong jobs filtering in**: Adjust location/role names to match Greenhouse data exactly
