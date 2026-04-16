# Greenhouse Job Board Configuration
# Add your Greenhouse board tokens here
# You can find your board token in your Greenhouse job board URL:
# https://boards.greenhouse.io/BOARD_TOKEN or from your company's Greenhouse portal

GREENHOUSE_BOARDS = [
    # Example format:
    # {
    #     "board_token": "your_board_token_here",
    #     "company_name": "Company Name",
    #     "include_locations": ["Ottawa", "Guelph", "Toronto", "Mississauga"],  # Optional filter
    #     "include_roles": ["UI/UX", "Research", "Analyst"],  # Optional filter
    # }
]

# API endpoint (do not modify)
GREENHOUSE_API_BASE = "https://boards-api.greenhouse.io/v1/boards"
