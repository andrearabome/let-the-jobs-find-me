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

- I think email notifications for new matching jobs would be cool
- Resume storage and management and maybe auto apply to certain jobs?
- Salary tracking and comparison with other jobs

## License

This project is for me to find jobs faster instead of scrolling for hours.
