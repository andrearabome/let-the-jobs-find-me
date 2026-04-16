# Let The Jobs Find Me

my personal job board application for tracking and searching UI/UX, Research, and Analyst roles in Ottawa, Guelph, Toronto, and Mississauga so that I can easily apply and would not have to scroll for hours

## Features

- 🔍 **Advanced Filtering** - Filter jobs by role type and location
- 📌 **Bookmarking** - Save interesting jobs for later review
- 📊 **Application Tracking** - Track the status of your applications (interested, applied, interview, offered, etc.)
- 📝 **Notes** - Add notes to applications
- 🎯 **Custom Locations** - Pre-configured for Ottawa, Guelph, Toronto, and Mississauga
- 💼 **Role Categories** - Focused on UI/UX, Research, and Analyst positions

## Project Structure

```
├── app.py                    # Flask application (main server)
├── requirements.txt          # Python dependencies
├── templates/
│   └── index.html           # Main HTML template
├── static/
│   ├── style.css            # Styling
│   └── script.js            # Frontend JavaScript
├── jobs.db                  # SQLite database (created on first run)
├── sample_jobs.csv          # Sample job data
└── README.md                # This file
```

## Getting Started

### Prerequisites

- Python 3.7 or higher
- pip (Python package manager)

### Installation

1. Install Python dependencies:

```bash
pip install -r requirements.txt
```

### Running the Application

Start the Flask development server:

```bash
python app.py
```

The application will open at:
- **http://localhost:5000**

Open this URL in your web browser.

## API Endpoints

### Jobs
- `GET /api/jobs` - Get all jobs (with optional filters)
  - Query parameters: `role`, `location`, `search`
- `GET /api/jobs/:id` - Get a specific job
- `POST /api/jobs` - Add a new job
- `PUT /api/jobs/:id` - Update a job
- `DELETE /api/jobs/:id` - Delete a job

### Applications
- `POST /api/applications` - Track an application
- `GET /api/applications/:jobId` - Get application for a job

### Bookmarks
- `POST /api/bookmarks` - Bookmark a job
- `DELETE /api/bookmarks/:jobId` - Remove bookmark
- `GET /api/bookmarks` - Get all bookmarked jobs

### Import
- `POST /api/import` - Import jobs from CSV

### Filters
- `GET /api/filters` - Get available filter options

## CSV Format

When importing jobs, use the following CSV format:

```csv
title,company,location,role,description,url,salary
UI Designer,Tech Corp,Toronto,UI/UX,Seeking experienced UI designer...,https://example.com/job1,60000-80000
```

**Required columns**: title, company, location, role  
**Optional columns**: description, url, salary

## Database

The application uses SQLite database with the following tables:

- **jobs** - Stores all job listings
- **applications** - Tracks application status for each job
- **bookmarks** - Stores bookmarked jobs

Database file location: `jobs.db` (created automatically on first run)

## Built With

- **Backend**: Python Flask, SQLite3
- **Frontend**: HTML, CSS, Vanilla JavaScript
- **Database**: SQLite3

## Usage Tips

1. **Import Jobs**: Start by importing the sample CSV file or your own job listings
2. **Filter & Search**: Use the sidebar filters to narrow down jobs
3. **Track Applications**: Click on a job to view details and track your application status
4. **Bookmark Favorites**: Star jobs you're interested in for quick access later
5. **Review Status**: Check the "Bookmarked" tab to see your saved opportunities

## Future Enhancements

- Manual job entry form
- Email notifications for new matching jobs
- Job board API integration (Indeed, LinkedIn, etc.)
- Resume storage and management
- Interview preparation notes
- Salary tracking and comparison

## License

This project is for personal use.

## Support

For issues or improvements, feel free to modify the code according to your needs!
